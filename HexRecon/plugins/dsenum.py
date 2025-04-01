import subprocess

PLUGIN_NAME = "DSEnum"
PLUGIN_DESCRIPTION = "DSEnum is a tool for performing DNS enumeration to gather subdomain and DNS record information."
REQUIRED_TOOLS = ["dsenum"]
PLUGIN_COMMANDS = {
    "Basic DNS Enumeration (Recommended)": " "
}

def run(target, command):
    """Run DSEnum for DNS enumeration on the target domain."""
    cmd = f"dsenum {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running DSEnum: {e}"
