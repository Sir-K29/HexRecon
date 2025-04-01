import subprocess

PLUGIN_NAME = "Gobuster"
PLUGIN_DESCRIPTION = "Gobuster is a directory and file scanner used to brute-force hidden directories on web servers."
REQUIRED_TOOLS = ["gobuster"]
PLUGIN_COMMANDS = {
    "Directory Brute Force (Recommended): gobuster dir -u {target} -w /usr/share/wordlists/dirb/common.txt": "-u {target} -w /usr/share/wordlists/dirb/common.txt",
    "Wordlist Scan: gobuster dir -u {target} -w /usr/share/wordlists/dirb/big.txt": "-u {target} -w /usr/share/wordlists/dirb/big.txt"
}

def run(target, command):
    """Run Gobuster scan on the given target with the specified command."""
    # Determine the wordlist based on the command content.
    if "big.txt" in command:
        wordlist = "/usr/share/wordlists/dirb/big.txt"
    else:
        wordlist = "/usr/share/wordlists/dirb/common.txt"
    cmd = ["gobuster", "dir", "-u", target, "-w", wordlist]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running Gobuster: {e}"
