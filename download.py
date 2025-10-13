import sys
import os
import shutil
import time
import requests
import logging
import re
from colorama import Fore, Style, init

# Initialize Colorama
if sys.platform == 'win32':
    init(autoreset=True, strip=True, convert=True)
else:
    init(autoreset=True, strip=False, convert=False)

LOG_DIR = os.path.join(os.path.expanduser("~"), ".logs")
class Logger:
    def __init__(self):
        self.debug = True
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self._last_line_count = 0

        if self.debug:
            os.makedirs(LOG_DIR, exist_ok=True)
            file_handler = logging.FileHandler(os.path.join(LOG_DIR, f"download-{time.strftime('%Y%m%d-%H%M%S')}.log"))
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.debug("Logger initialized and debug mode is ON.")

    def log_debug(self, message):
        if self.debug:
            self.logger.debug(message)

    def _strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)
  
    def least_count(self, line):
        """Calculates the number of lines a string will occupy in the terminal."""
        self.log_debug(f"least_count received line: {line}")
        terminal_width = shutil.get_terminal_size().columns
        visible_line_length = len(self._strip_ansi(line))
        if terminal_width > 0:
            calculated_lines = (visible_line_length + terminal_width - 1) // terminal_width
            self.log_debug(f"least_count: Visible line length: {visible_line_length}, Terminal width: {terminal_width}, Calculated lines: {calculated_lines}")
            return calculated_lines
        return 1

    def _overwrite_line(self, line):
        """Overwrites the previous line(s) in the terminal with the given line."""
        escape_code = f"\x1b[{self._last_line_count}F\r\x1b[K"
        sys.stdout.write(escape_code)
        print(line)
        sys.stdout.flush()
        self._last_line_count = self.least_count(line)

    """def _output_line(self, line):
        if not sys.stdout.isatty():
            print(f'\r{line}')
            sys.stdout.flush()
        else:
            self._overwrite_line(line)"""
 
    def format_time(self, seconds):
        seconds = int(seconds)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # -------- Progress bar method --------
    def progress(self, iterable, description="Downloading", total=None, bar_length=30, unit="b", completion_message="✅ Download complete!"):
        """if os.environ.get("CI") == "true":
            print(f"{description}...")
            for item in iterable:
                yield item
            print(f"\n{completion_message}")
            return"""

        if total is None:
            try:
                total = len(iterable)
            except TypeError:
                for item in iterable:
                    yield item
                return

        start_time = time.time()
        current_val = 0
        is_bytes = (unit.lower() == 'b')

        def format_size(bytes_val):
            if bytes_val >= 1024 * 1024 * 1024:
                return f"{bytes_val / (1024*1024*1024):.1f} GB"
            if bytes_val >= 1024 * 1024:
                return f"{bytes_val / (1024*1024):.1f} MB"
            if bytes_val >= 1024:
                return f"{bytes_val / 1024:.1f} KB"
            return f"{int(bytes_val)} B"

        print(f"{description}...\n")
        sys.stdout.flush()
        """self._last_line_count = 1"""
        for i, item in enumerate(iterable):
            yield item

            # Current progress
            if is_bytes:
                try:
                    current_val += len(item)
                except TypeError:
                    current_val += 1
            else:
                current_val = i + 1

            elapsed = time.time() - start_time
            percent = min(1.0, current_val / total if total > 0 else 0)
            filled_len = int(bar_length * percent)

            # Bar
            bar = Fore.GREEN + "━" * filled_len
            if filled_len < bar_length:
                bar += Fore.RED + "╺" + Style.RESET_ALL + "━" * (bar_length - filled_len - 1)
            else:
                bar += Style.RESET_ALL

            speed = current_val / elapsed if elapsed > 0 else 0
            remaining = total - current_val
            eta = remaining / speed if speed > 0 else 0

            if is_bytes:
                speed_unit, speed_divisor = ("MB/s", 1024*1024)
                if speed > 1024*1024*1024:
                    speed_unit, speed_divisor = ("GB/s", 1024*1024*1024)
            else:
                speed_unit, speed_divisor = ("it/s", 1)

            try:
                eta_str = self.format_time(eta)
            except (ValueError, OverflowError, OSError):
                eta_str = "∞"

            line = (
                f"{percent*100:3.0f}% | "
                f"{bar} | "
                f"{format_size(current_val)}/{format_size(total)} • "
                f"{speed/speed_divisor:.1f} {speed_unit} • "
                f"{self.format_time(elapsed)}/"
                f"{eta_str}"
            )

            self._overwrite_line(line)

        # completion message
        if completion_message:
            print(f"\n{completion_message}")
        """self._last_line_count = 0"""

logger = Logger()
logger.debug = True


def download(url, dest_dir, filename=None, timeout=60, verbose=False):
    logger.log_debug(f"Starting download for URL: {url} to destination: {dest_dir}")
    os.makedirs(dest_dir, exist_ok=True)
    if filename is None:
        filename = url.split('/')[-1]
    
    # Create a temporary directory for the download
    download_temp_dir = os.path.join(dest_dir, ".download.tmp")
    logger.log_debug(f"Creating temporary download directory: {download_temp_dir}")
    if not os.path.exists(download_temp_dir):
        os.makedirs(download_temp_dir)
    
    filepath = os.path.join(download_temp_dir, filename)
    temp_filepath = filepath + ".tmp"

    try:
        logger.log_debug(f"Initiating GET request to {url} with timeout {timeout}")
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            logger.log_debug(f"Total file size: {total_size} bytes")

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
            logger.log_debug(f"Download complete to temporary file: {temp_filepath}")
            # Move the temporary file to its final destination
            shutil.move(temp_filepath, filepath)
            print(f"Downloaded {filename} to {dest_dir}")
            logger.log_debug(f"Moved {temp_filepath} to {filepath}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {filename}: {e}")
        logger.log_debug(f"RequestException during download: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logger.log_debug(f"Unexpected error during download: {e}")
    finally:
        # Clean up the temporary directory
        if os.path.exists(download_temp_dir):
            logger.log_debug(f"Cleaning up temporary directory: {download_temp_dir}")
            shutil.rmtree(download_temp_dir)
        logger.log_debug(f"Download function finished for {url}")





# Example usage:

# Trigger a new GitHub workflow run
if __name__ == "__main__":

    url = "https://github.com/libffi/libffi/releases/download/v3.5.2/libffi-3.5.2.tar.gz"

    dest_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    download(url, dest_dir)
