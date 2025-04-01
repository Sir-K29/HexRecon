import subprocess

PLUGIN_NAME = "Nuclei"
PLUGIN_DESCRIPTION = "Nuclei is a fast and configurable vulnerability scanner for web applications."
REQUIRED_TOOLS = ["nuclei"]
PLUGIN_COMMANDS = {
    "Basic Vulnerability Scan (Recommended): nuclei -u {target}": "-u",
    "Aggressive Scan: nuclei -u {target} -severity critical": "-u -severity critical"
}

def run(target, command):
    """Run Nuclei vulnerability scan on the target domain."""
    cmd = f"nuclei {command} {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running Nuclei: {e}"
