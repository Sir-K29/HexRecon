import subprocess

PLUGIN_NAME = "Whois"
PLUGIN_DESCRIPTION = "Whois is a tool for querying domain registration and IP information."
REQUIRED_TOOLS = ["whois"]
PLUGIN_COMMANDS = {
    "Domain Lookup (Recommended): whois {target}": ""
}

def run(target, command):
    """Run Whois lookup on the target domain."""
    cmd = f"whois {command} {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running Whois: {e}"
