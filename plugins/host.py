import subprocess

PLUGIN_NAME = "Host"
PLUGIN_DESCRIPTION = "Host is a simple tool for performing DNS lookups."
REQUIRED_TOOLS = ["host"]
PLUGIN_COMMANDS = {
    "Basic Lookup: host {target}": "",
    "Get IPv6 Address: host -6 {target}": "-6",
    "Get All Records: host -a {target}": "-a"
}

def run(target, command):
    """Run host on the target domain."""
    if not target.strip():
        return "Error: No target provided"

    cmd = f"host {command} {target}" if command else f"host {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=60)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running Host: {e}"
