import subprocess

PLUGIN_NAME = "WhatWeb"
PLUGIN_DESCRIPTION = "WhatWeb is a website fingerprinting tool used to identify the technologies powering a website."
REQUIRED_TOOLS = ["whatweb"]
PLUGIN_COMMANDS = {
    "Basic Fingerprinting (Recommended): whatweb {target}": "",
    "Verbose Fingerprinting: whatweb -v {target}": "-v"
}

def run(target, command):
    """Run whatweb scan with the selected command on the target."""
    cmd = f"whatweb {command} {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running WhatWeb: {e}"
