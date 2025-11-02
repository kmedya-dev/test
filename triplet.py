import platform
import subprocess

def get_shell_output(command):
    """Executes a shell command and returns its output, ignoring errors."""
    try:
        return subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""

def get_arch():
    """Gets the machine architecture from uname -m."""
    return platform.machine()

def get_system():
    """Gets the operating system name from uname -s."""
    return platform.system().lower()

def get_vendor():
    """
    Gets the CPU vendor.
    Tries to read /proc/cpuinfo on Linux, or uses sysctl on macOS.
    """
    implementers = {
        "0x41": "arm",
        "0x42": "broadcom",
        "0x43": "cavium",
        "0x44": "dec",
        "0x46": "fujitsu",
        "0x49": "infineon",
        "0x4d": "motorola",
        "0x4e": "nvidia",
        "0x50": "apm",
        "0x51": "qualcomm",
        "0x56": "marvell",
        "0x61": "ampere",
        "0x69": "intel",
    }

    system = get_system()
    if system == "linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "vendor_id" in line or "CPU implementer" in line:
                        parts = line.strip().split(":")
                        if len(parts) > 1:
                            vendor_id = parts[1].strip()
                            return implementers.get(vendor_id.lower(), vendor_id)
        except FileNotFoundError:
            # /proc/cpuinfo not found
            pass
    elif system == "darwin":
        vendor_info = get_shell_output("sysctl -n machdep.cpu.vendor")
        if vendor_info:
            return vendor_info
        return "apple"  # A reasonable default for macOS

    return "unknown"

def get_libc():
    """
    Determines the C library (libc) used by the system using a C preprocessor trick.
    This method requires a C compiler (cc) to be installed.
    """
    c_code = '''
#if defined(__ANDROID__)
LIBC=android
#else
#include <features.h>
#if defined(__UCLIBC__)
LIBC=uclibc
#elif defined(__dietlibc__)
LIBC=dietlibc
#elif defined(__GLIBC__)
LIBC=gnu
#else
#include <stdarg.h>
/* First heuristic to detect musl libc.  */
#ifdef __DEFINED_va_list
LIBC=musl
#endif
#endif
#endif
'''
    command = f"echo '{c_code}' | cc -E - 2>/dev/null | grep LIBC="
    output = get_shell_output(command)
    if output and "=" in output:
        return output.split("=")[-1]

    return "unknown"

def main():
    """
    Constructs and prints the system triplet in the format arch-vendor-system-libc.
    """
    arch = get_arch()
    vendor = get_vendor()
    system = get_system()
    libc = get_libc()

    triplet = f"{arch}-{vendor}-{system}-{libc}"
    print(triplet)

if __name__ == "__main__":
    main()