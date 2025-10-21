import os
import zipfile
import tarfile
import shutil
import sys
import contextlib
import subprocess
import requests
from logger import logger

# -------------------- Helpers: safe paths & extraction --------------------

def _safe_join(base, *paths):
    """Safely join paths, preventing path traversal attacks."""
    base = os.path.abspath(base)
    final = os.path.abspath(os.path.join(base, *paths))
    if not final.startswith(base + os.sep) and final != base:
        raise IOError(f"Unsafe path detected: {final}")
    return final

def _safe_extract_zip(zip_ref: zipfile.ZipFile, dest_dir: str, log_each=True, verbose=False):
    """Safely extract a zip file, preventing zip slip attacks."""
    for member in zip_ref.infolist():
        # protect against zip slip
        target_path = _safe_join(dest_dir, member.filename)
        # logging like unzip
        if member.is_dir():
            if log_each:
                logger.step_info(f"creating: {member.filename}", indent=3, overwrite=True, verbose=verbose)
            os.makedirs(target_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            if log_each:
                if os.path.exists(target_path):
                    logger.step_info(f" replace: {member.filename}", indent=2, overwrite=True, verbose=verbose)
                else:
                    logger.step_info(f"extracting: {member.filename}", indent=2, overwrite=True, verbose=verbose)
            with zip_ref.open(member, 'r') as src, open(target_path, 'wb') as out:
                shutil.copyfileobj(src, out)
            # Preserve file permissions
            mode = member.external_attr >> 16
            if mode:
                os.chmod(target_path, mode)

def _safe_extract_tar(tar_ref: tarfile.TarFile, dest_dir: str, log_each=True, verbose=False):
    """Safely extract a tar file, preventing path traversal attacks."""
    for member in tar_ref.getmembers():
        # deny absolute or parent traversal
        member_path = _safe_join(dest_dir, member.name)
        if member.isdir():
            if log_each:
                logger.step_info(f"creating: {member.name}", indent=3, overwrite=True, verbose=verbose)
            os.makedirs(member_path, exist_ok=True)
            continue
        # ensure parent exists
        os.makedirs(os.path.dirname(member_path), exist_ok=True)
        if log_each:
            if os.path.exists(member_path):
                logger.step_info(f" replace: {member.name}", indent=2, overwrite=True, verbose=verbose)
            else:
                logger.step_info(f"extracting: {member.name}", indent=2, overwrite=True, verbose=verbose)
        src = tar_ref.extractfile(member)
        if src is None:
            # could be special file; skip silently
            continue
        with src as src_file: # Use a different variable name to avoid confusion
            with open(member_path, "wb") as out:
                shutil.copyfileobj(src_file, out)
            # Preserve file permissions
            if member.mode:
                os.chmod(member_path, member.mode)

def _move_extracted_files(source_dir, dest_dir):
    """Move extracted files, normalizing the directory structure."""
    extracted_items = os.listdir(source_dir)

    """if len(extracted_items) == 1:
        inner_dir = os.path.join(source_dir, extracted_items[0])
        if os.path.isdir(inner_dir):
            # Move the inner directory to the destination
            shutil.move(inner_dir, dest_dir)
            shutil.rmtree(source_dir) # Clean up the now-empty source dir
            return dest_dir # Return the destination directory, which now contains the inner directory"""

    for item in extracted_items:
        shutil.move(os.path.join(source_dir, item), os.path.join(dest_dir, item))
    shutil.rmtree(source_dir)
    return dest_dir

def extract(filepath, dest_dir, verbose=False):
    """Extracts an archive file to a destination directory."""
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(filepath)
    temp_dir = dest_dir + ".tmp"

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    try:
        if tarfile.is_tarfile(filepath):
            with tarfile.open(filepath, 'r:*') as tar:
                _safe_extract_tar(tar, temp_dir, log_each=True, verbose=verbose)
        elif zipfile.is_zipfile(filepath):
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                _safe_extract_zip(zip_ref, temp_dir, log_each=True, verbose=verbose)
        elif filename.endswith('.bz2'):
            with tarfile.open(filepath, 'r:bz2') as tar:
                _safe_extract_tar(tar, temp_dir, log_each=True, verbose=verbose)
        else:
            logger.warning(f"Unsupported archive type for {filename}. Skipping extraction.")
            shutil.rmtree(temp_dir)
            return None

        # Move files from temp_dir to dest_dir and normalize structure
        final_extracted_path = _move_extracted_files(temp_dir, dest_dir)

        # Remove archive after successful extraction
        with contextlib.suppress(OSError):
            os.remove(filepath)

        logger.success(f"Successfully extracted to {final_extracted_path}")
        return final_extracted_path

    except (zipfile.BadZipFile, tarfile.TarError, IOError) as e:
        logger.error(f"Error during extraction: {e}")
        shutil.rmtree(temp_dir)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during extraction: {e}")
        logger.exception(*sys.exc_info())
        shutil.rmtree(temp_dir)
        return None

# -------------------- Download & Extract --------------------



def download_and_extract(url, dest_dir, filename=None, timeout=60, verbose=False):

    """Download and extract a file to a destination directory."""

    os.makedirs(dest_dir, exist_ok=True)

    if filename is None:

        filename = url.split('/')[-1]

    

    # Create a temporary directory for the download

    download_temp_dir = dest_dir + ".download.tmp"

    if not os.path.exists(download_temp_dir):

        os.makedirs(download_temp_dir)

    

    filepath = os.path.join(download_temp_dir, filename)

    temp_filepath = filepath + ".tmp"



    try:

        with requests.get(url, stream=True, timeout=timeout) as r:

            r.raise_for_status()

            total_size = int(r.headers.get('content-length', 0))



            with open(temp_filepath, 'wb') as f:

                chunks = logger.progress(

                    r.iter_content(chunk_size=1024 * 256),  # 256KB chunks

                    description=f"Downloading {filename}",

                    total=total_size,

                    unit="b"

                )

                for chunk in chunks:

                    if chunk:  # keep-alive chunks may be empty

                        f.write(chunk)



        # Atomic rename

        os.replace(temp_filepath, filepath)



        logger.step_info(f"Archive:  {filename}")



        return extract(filepath, dest_dir, verbose=verbose)



    except requests.exceptions.RequestException as e:

        logger.error(f"Error downloading the file: {e}")

        # cleanup temp

        with contextlib.suppress(Exception):

            if os.path.exists(temp_filepath):

                os.remove(temp_filepath)

            if os.path.exists(download_temp_dir):

                shutil.rmtree(download_temp_dir)

        return None

    except Exception as e:

        logger.error(f"An unexpected error occurred: {e}")

        logger.exception(*sys.exc_info())

        return None
