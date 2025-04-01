# HexRecon

A modular pentesting framework with a plugin architecture and an intuitive graphical interface. The framework supports dynamic loading of plugins, real-time scanning, and report generation in both HTML and PDF formats.

Virtual Environment Setup

To keep your dependencies isolated, it is recommended to create a Python virtual environment.

1. Create a Virtual Environment

Open your terminal and run:
```bash
python3 -m venv venv
```
2. Activate the Virtual Environment

On macOS and Linux:
```bash
source venv/bin/activate
```
On Windows:
```bash
venv\Scripts\activate
```
3. Install Dependencies

With the virtual environment activated, install the required packages:
```bash
pip install -r requirements.txt
```
Ensure your requirements.txt contains the required dependencies, such as PyQt5, rich, psutil, pyqtgraph, and fpdf.

Using the GUI

Once the virtual environment is set up and dependencies are installed, you can launch the GUI.

Launch via Console Script

The package provides an entry point named hexrecon. Simply run:
```bash
hexrecon
```
This will open the HexRecon GUI, where you can:

Select Tools: Choose from available plugins for scanning.

Add Targets: Enter target domains or IP addresses.

Start Scanning: Execute the scan with real-time progress updates.

Monitor Dashboard: View progress metrics, CPU, and memory usage.

Manage Plugins: Enable/disable plugins and edit their descriptions.

Generate Reports: After a scan, generate CSV, HTML, or PDF reports.

Alternative Usage

If you prefer to run the code without using the package entry point, you can do so by running the main script directly.

1. Extract main.py

Take the main.py file from the pentest folder.

2. Run the Script

Execute the script from your terminal:
```bash
python3 main.py
```
This will launch the same GUI interface as described above.

Main Functionalities

Plugin-Based Architecture

Dynamically loads Python plugins from the designated plugins directory.

Each plugin can define its own commands and required external tools.

Graphical User Interface (GUI)

Built with PyQt5, the GUI provides:

A scan tab for selecting plugins and entering targets.

A dashboard to monitor scan progress, CPU, and memory usage in real time.

A plugins tab for managing and editing plugin settings.

Asynchronous Scanning

Utilizes worker threads to execute scan commands concurrently without freezing the user interface.

Real-Time Reporting

After completing scans, the framework can:

Export results as CSV.

Generate detailed HTML and PDF reports grouped by target and tool.

Utility Functions

Includes helper functions for logging, sanitizing input, managing file paths, and executing shell commands with proper process management.

Summary

This pentest framework provides a robust and extensible environment for running security scans. Whether you choose to use the GUI or run the script directly, the tool supports modular testing, real-time monitoring, and comprehensive reporting, making it a valuable asset for pentesters.

Happy Testing!
