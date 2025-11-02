import subprocess, re, os

def sh(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, shell=True).strip()
    except Exception:
        return ""

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

arch    = sh("uname -m")
system  = sh("uname -s").lower()
vendor_cmd = "grep -m1 -E 'vendor_id|CPU implementer' /proc/cpuinfo"
vendor_id_raw = sh(f"{vendor_cmd} | awk '{{print $3}}'")

if ":" not in vendor_id_raw:
    vendor_id = vendor_id_raw
else:
    vendor_id = sh(f"{vendor_cmd} | awk '{{print $NF}}'")

vendor = implementers.get(vendor_id.lower(), vendor_id)

libc_c_code = '''
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
libc = sh(f"echo '{libc_c_code}' | cc -E - 2>/dev/null | grep LIBC=").split("=")[-1]

triplet = f"{arch}-{vendor}-{system}-{libc}"
print(triplet)
