import subprocess

def build_triple():
    arch = subprocess.getoutput("uname -m").strip()
    vendor = subprocess.getoutput("grep -m1 -E 'vendor_id|CPU implementer' /proc/cpuinfo | awk '{print $3}'").strip() or "unknown"
    system = subprocess.getoutput("uname -s").strip().lower()
    api = subprocess.getoutput("getprop ro.build.version.sdk 2>/dev/null").strip() or "gnu"
    return f"{arch}-{vendor}-{system}-{api}"

print(build_triple())
