import subprocess

PLUGIN_NAME = "SQLMap"
PLUGIN_DESCRIPTION = "SQLMap is an automated tool for detecting and exploiting SQL injection vulnerabilities."
REQUIRED_TOOLS = ["sqlmap"]
PLUGIN_COMMANDS = {
    "Basic Test (Recommended): sqlmap -u {target}": "",
    "List Databases: sqlmap -u {target} --dbs": "--dbs",
    "List Tables: sqlmap -u {target} --tables": "--tables",
    "Dump Table: sqlmap -u {target} --dump": "--dump",
    "Automated Exploit (Batch Mode): sqlmap -u {target} --batch --dump": "--batch --dump",
    "OS Shell: sqlmap -u {target} --os-shell": "--os-shell",
    "Time-based Injection: sqlmap -u {target} --time-sec": "--time-sec",
    "SQL Query Execution: sqlmap -u {target} --sql-query": "--sql-query"
}

def run(target, command, extra_args=""):
    """Run sqlmap with the selected command and additional parameters on the target."""
    cmd = f"sqlmap -u {target} {command} {extra_args}"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=300)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error running SQLMap: {e}"
