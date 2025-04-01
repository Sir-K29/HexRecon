import subprocess
import logging

PLUGIN_NAME = "Hydra"
PLUGIN_DESCRIPTION = "Hydra is a fast network login cracker that supports brute forcing credentials for many different services."
REQUIRED_TOOLS = ["hydra"]
PLUGIN_COMMANDS = {
    "Basic Login Crack (Recommended): hydra -l user -P passlist.txt {target} ssh": "hydra -l user -P passlist.txt {target} ssh",
    "FTP Brute Force: hydra -L userlist.txt -P passlist.txt {target} ftp": "hydra -L userlist.txt -P passlist.txt {target} ftp"
}

def run(target, command):
    """Run Hydra with the selected command on the target."""
    cmd = command.replace("{target}", target)  # Replace placeholder
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        logging.error(f"Error running Hydra: {e}")
        return f"Error running Hydra: {e}"
