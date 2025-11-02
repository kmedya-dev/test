import subprocess, re, os

def sh(*cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception:
        return ""

def detect_libc_from_header(head):
    if b"musl" in head:
        return "musl"
    elif b"GNU" in head:
        return "gnu"
    elif b"bionic" in head:
        return "android"
    return ""

arch    = sh("uname", "-m")
system  = sh("uname", "-s").lower()
vendor  = re.sub(r".*?:\s*", "", sh("grep", "-m1", "-E", "vendor_id|CPU implementer", "/proc/cpuinfo | awk '{print $3}'") or "unknown")
ldd_ver = sh("ldd", "--version")

detect_libc = ""
base_paths = ["/lib", "/usr/lib", "/system/lib", "/vendor/lib", "/usr/local/lib"]
print("Checking for libc files:")
for base_path in base_paths:
    for libc_name in ["libc.so", "libc.so.*"]:
        full_path = os.path.join(base_path, libc_name)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                head = f.read(128)
                detected_type = detect_libc_from_header(head)
                if detected_type:
                    print(f"Found {libc_name} at {full_path}, detected type: {detected_type}")
                    detect_libc = detected_type # Update detect_libc with the detected type
                    break # Stop after finding the first libc
                else:
                    print(f"Found {libc_name} at {full_path}, but could not determine type from header.")
        else:
            print(f"{libc_name} not found at {full_path}")
    if detect_libc: # If libc found, break from outer loop as well
        break

if not detect_libc and system == "linux":
    detect_libc = "bionic"
triplet = f"{arch}-{vendor}-{system}-{detect_libc}"
print(triplet)

