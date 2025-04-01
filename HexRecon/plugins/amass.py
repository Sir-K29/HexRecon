import subprocess

PLUGIN_NAME = "Amass"
PLUGIN_DESCRIPTION = "Amass is a powerful subdomain enumeration tool that uses multiple techniques to discover subdomains."
REQUIRED_TOOLS = ["amass"]
PLUGIN_COMMANDS = {
    "Basic Enumeration: enum": "enum",
    "Passive Enumeration (Recommended): enum -passive": "enum -passive",
    "Active Enumeration: enum -active": "enum -active"
}

def run(target, command):
    """Run Amass enumeration on the target domain."""
    cmd = f"amass {command} -d {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running Amass: {e}"
