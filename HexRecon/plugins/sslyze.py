import subprocess

PLUGIN_NAME = "SSLyze"
PLUGIN_DESCRIPTION = "SSLyze is a tool for analyzing SSL/TLS configurations and detecting vulnerabilities on a target."
REQUIRED_TOOLS = ["sslyze"]
PLUGIN_COMMANDS = {
    "Basic SSL/TLS Scan (Recommended): sslyze {target}": " "
}

def run(target, command):
    """Run SSLyze to scan SSL/TLS configurations on the target domain."""
    cmd = f"sslyze {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running SSLyze: {e}"
