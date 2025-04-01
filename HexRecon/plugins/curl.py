import subprocess
import logging

PLUGIN_NAME = "Curl"
PLUGIN_DESCRIPTION = "Curl is a versatile tool for transferring data with URL syntax supporting multiple protocols."
REQUIRED_TOOLS = ["curl"]
PLUGIN_COMMANDS = {
    "Fetch Web Page (Recommended): curl {target}": "curl {target}",
    "Head Request: curl -I {target}": "curl -I {target}",
    "Verbose Output: curl -v {target}": "curl -v {target}"
}

def run(target, command):
    """Run Curl with the selected command on the target."""
    cmd = command.replace("{target}", target)  # Replace placeholder
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        logging.error(f"Error running Curl: {e}")
        return f"Error running Curl: {e}"
