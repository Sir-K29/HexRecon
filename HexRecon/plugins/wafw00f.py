import subprocess

PLUGIN_NAME = "Wafw00f"
PLUGIN_DESCRIPTION = "Wafw00f detects the presence of web application firewalls (WAFs) on a target website."
REQUIRED_TOOLS = ["wafw00f"]
PLUGIN_COMMANDS = {
    "Detect WAF (Recommended): wafw00f {target}": ""
}

def run(target, command):
    """Run Wafw00f to detect WAFs on the target domain."""
    cmd = f"wafw00f {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running Wafw00f: {e}"
