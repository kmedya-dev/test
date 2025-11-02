import subprocess, re

def sh(*cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception:
        return ""

arch    = sh("uname", "-m")
system  = sh("uname", "-s").lower()
vendor  = re.sub(r".*?:\s*", "", sh("grep", "-m1", "-E", "vendor_id|CPU implementer", "/proc/cpuinfo") or "unknown")
ldd_ver = sh("ldd", "--version")
api     = sh("getprop", "ro.build.version.sdk")

abi = (
    ("android" + api) * bool(api)
    or "musl" * bool(re.search("musl", ldd_ver, re.I))
    or "gnu"  * bool(re.search("glibc|gnu libc", ldd_ver, re.I))
    or "eabihf" * bool(re.search("hard-float", sh("readelf", "-A", "/bin/sh"), re.I))
    or "eabi" * bool(re.search("arm", arch))
    or "darwin" * bool("darwin" in system)
    or "unknown"
)

triplet = f"{arch}-{vendor}-{system}-{abi}"
print(triplet)
