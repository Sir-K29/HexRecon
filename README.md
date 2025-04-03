# Pentest Framework

A modular pentesting framework with a plugin system, real-time scanning, and report generation in HTML and PDF formats.

## Virtual Environment Setup

To keep your dependencies isolated, it is recommended to create a Python virtual environment.

### 1. Create a Virtual Environment

Open your terminal and run:

```bash
python3 -m venv venv
```

### 2. Activate the Virtual Environment

**On macOS and Linux:**

```bash
source venv/bin/activate
```

**On Windows:**

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

With the virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

Ensure your `requirements.txt` contains the required dependencies, such as PyQt5, rich, psutil, pyqtgraph, and fpdf.

## Using the GUI

Once the virtual environment is set up and dependencies are installed, navigate to the `HexRecon` folder and run:

```bash
python3 main.py
```

This will open the HexRecon GUI, where you can:

- **Select Tools**: Choose from available plugins for scanning.
- **Add Targets**: Enter target domains or IP addresses.
- **Start Scanning**: Execute the scan with real-time progress updates.
- **Monitor Dashboard**: View progress metrics, CPU, and memory usage.
- **Manage Plugins**: Enable/disable plugins and edit their descriptions.
- **Generate Reports**: After a scan, generate CSV, HTML, or PDF reports.

## Main Functionalities

### Plugin-Based Architecture

- Dynamically loads Python plugins from the designated `plugins` directory.
- Each plugin can define its own commands and required external tools.

### Graphical User Interface (GUI)

Built with PyQt5, the GUI provides:

- A **scan tab** for selecting plugins and entering targets.
- A **dashboard** to monitor scan progress, CPU, and memory usage in real time.
- A **plugins tab** for managing and editing plugin settings.

### Asynchronous Scanning

- Utilizes worker threads to execute scan commands concurrently without freezing the user interface.

### Real-Time Reporting

After completing scans, the framework can:

- Export results as **CSV**.
- Generate detailed **HTML and PDF reports** grouped by target and tool.

### Utility Functions

- Includes helper functions for logging, sanitizing input, managing file paths, and executing shell commands with proper process management.

## Summary

This pentest framework provides a robust and extensible environment for running security scans. By running `python3 main.py` inside the `HexRecon` folder, the tool supports modular testing, real-time monitoring, and comprehensive reporting, making it a valuable asset for pentesters.

**Happy Testing!**

