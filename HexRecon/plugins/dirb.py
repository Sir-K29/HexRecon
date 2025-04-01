import subprocess
import logging

PLUGIN_NAME = "Dirb"
PLUGIN_DESCRIPTION = "Dirb is a web content scanner used to discover hidden files and directories on a web server."
REQUIRED_TOOLS = ["dirb"]
PLUGIN_COMMANDS = {
    "Basic Scan (Recommended): dirb {target}": "dirb {target}",
    "Verbose Scan: dirb -v {target}": "dirb -v {target}"
}

def run(target, command):
    """Run Dirb scan with the selected command on the target."""
    cmd = command.replace("{target}", target)  # Replace placeholder
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        logging.error(f"Error running Dirb: {e}")
        return f"Error running Dirb: {e}"
