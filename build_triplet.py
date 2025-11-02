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
ldd_ver = sh("ldd --version")
cc_ver = sh("cc --version")

toolchain_env = os.environ.get("TOOLCHAIN_ENV")
if not toolchain_env:
    if os.environ.get("ANDROID_ROOT"):
        toolchain_env = "android"
    elif "gnu" in ldd_ver.lower():
        toolchain_env = "gnu"
    elif "musl" in ldd_ver.lower():
        toolchain_env = "musl"
    elif "clang" in cc_ver.lower() or "llvm" in cc_ver.lower():
        toolchain_env = "llvm"
    else:
        toolchain_env = ""

triplet = f"{arch}-{vendor}-{system}-{toolchain_env}"
print(triplet)
