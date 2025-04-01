import subprocess

PLUGIN_NAME = "Nmap"
PLUGIN_DESCRIPTION = "Nmap is a powerful network scanner used for network exploration and vulnerability detection."
REQUIRED_TOOLS = ["nmap"]
PLUGIN_COMMANDS = {
    "Basic Scan (Recommended): nmap {target}": "",
    "Open Ports: nmap --open {target}": "--open",
    "TCP SYN Scan: nmap -sS {target}": "-sS",
    "TCP Connect Scan: nmap -sT {target}": "-sT",
    "UDP Scan: nmap -sU {target}": "-sU",
    "OS Detection: nmap -O {target}": "-O",
    "Aggressive Scan (Recommended): nmap -A {target}": "-A",
    "Faster Scan: nmap -T4 {target}": "-T4",
    "Fast Scan: nmap -F {target}": "-F",
    "Top 1000 Ports: nmap --top-ports 1000 {target}": "--top-ports 1000",
    "Vulnerability Scan (Recommended): nmap --script=vuln {target}": "--script=vuln"
}

def run(target, command):
    """Run Nmap scan with the selected command on the target."""
    cmd = f"nmap {command} {target}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running Nmap: {e}"
