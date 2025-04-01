import subprocess

PLUGIN_NAME = "Sublist3r"
PLUGIN_DESCRIPTION = "Sublist3r is a fast tool for enumerating subdomains using multiple search engines."
REQUIRED_TOOLS = ["sublist3r"]
PLUGIN_COMMANDS = {
    "Basic Subdomain Enumeration (Recommended): sublist3r -d {target}": "-d"
}

def run(target, command):
    """Run Sublist3r enumeration on the target domain."""
    cmd = f"sublist3r {command} {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running Sublist3r: {e}"
