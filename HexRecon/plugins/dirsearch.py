import subprocess

PLUGIN_NAME = "Dirsearch"
PLUGIN_DESCRIPTION = "Dirsearch is a web path scanner that enumerates directories and files on web servers."
REQUIRED_TOOLS = ["dirsearch"]
PLUGIN_COMMANDS = {
    "Basic Scan (Recommended): dirsearch -u {target}": "",
    "Recursive Scan: dirsearch -r -u {target}": "-r"
}

def run(target, command):
    """Run Dirsearch scan on the target domain."""
    cmd = f"dirsearch -u {command} {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running Dirsearch: {e}"
