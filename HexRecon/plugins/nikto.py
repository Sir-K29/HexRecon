import subprocess
import logging

PLUGIN_NAME = "Nikto"
PLUGIN_DESCRIPTION = "Nikto is a web server vulnerability scanner that performs comprehensive tests to find potential issues."
REQUIRED_TOOLS = ["nikto"]
PLUGIN_COMMANDS = {
    "Basic Vulnerability Scan (Recommended): nikto -h {target}": "nikto -h {target}",
    "Aggressive Scan: nikto -h {target} -C all": "nikto -h {target} -C all"
}

def run(target, command):
    """Run Nikto scan with the selected command on the target."""
    cmd = command.replace("{target}", target)  # Replace placeholder
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        logging.error(f"Error running Nikto: {e}")
        return f"Error running Nikto: {e}"
