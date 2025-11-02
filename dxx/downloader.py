import os
import requests
import tarfile
from . import config
from .logger import logger
from .manager import download_and_extract

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), ".dxx", "downloads")


def download_from_url(url, package_name=None, verbose=False):
    """
    Downloads a file from a direct URL and extracts it.
    """
    logger.info(f"  - Downloading from URL: {url}...")

    filename = os.path.basename(url)
    base_filename = filename
    known_extensions = [".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".zip"]
    for ext in known_extensions:
        if base_filename.endswith(ext):
            base_filename = base_filename[:-len(ext)]
            break
    else:
        base_filename, _ = os.path.splitext(base_filename)
    
    # Use provided package_name for extraction directory if available, otherwise use derived base_filename
    final_extract_name = package_name if package_name else base_filename
    extract_dir = os.path.join(DOWNLOAD_DIR, "sources", final_extract_name)

    extracted_path = download_and_extract(url, extract_dir, verbose=verbose)

    return extracted_path
