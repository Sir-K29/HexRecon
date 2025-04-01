import subprocess

PLUGIN_NAME = "theHarvester"
PLUGIN_DESCRIPTION = "theHarvester is an OSINT tool for gathering emails, subdomains, and other reconnaissance data."
REQUIRED_TOOLS = ["theHarvester"]
PLUGIN_COMMANDS = {
    "Basic OSINT Scan (Recommended): theHarvester -d {target}": "",
    "Google Search (100 results): theHarvester -d {target} -l 100 -b google": "-l 100 -b google"
}

def run(target, command):
    """Run theHarvester scan with the selected command on the target domain."""
    base_cmd = f"theHarvester -d {target}"
    cmd = f"{base_cmd} {command}".strip()
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running theHarvester: {e}"
