import subprocess

PLUGIN_NAME = "Dig"
PLUGIN_DESCRIPTION = "Dig is a DNS lookup utility used to query various DNS record types for a domain."
REQUIRED_TOOLS = ["dig"]
PLUGIN_COMMANDS = {
    "Query A Record (Recommended): dig {target} A +short": "A",
    "Query AAAA Record: dig {target} AAAA +short": "AAAA",
    "Query MX Record: dig {target} MX +short": "MX",
    "Query NS Record: dig {target} NS +short": "NS",
    "Query TXT Record: dig {target} TXT +short": "TXT"
}

def run(target, command):
    """Run dig query for the selected DNS record type on the target domain."""
    cmd = f"dig {target} {command} +short"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=60)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running dig: {e}"
