#!/usr/bin/env python3
import sys
import os
import logging
import traceback

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QVBoxLayout,
    QHBoxLayout, QPushButton, QListWidget, QTextEdit, QLabel,
    QProgressBar, QMessageBox, QDialog, QAction, QLineEdit
)
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition

from pentest import config, utils
from pentest.plugin_manager import load_plugins, Plugin

# Setup logging
utils.setup_logging()

# Global variable for scan results
scan_results_global = []

# Define layout constants (adjust these values as needed)
PLUGIN_WIDTH = 800
TARGET_WIDTH = 100

# ---------------------------
# Worker Thread for Scanning (Sequential Execution)
# ---------------------------
class ScanWorker(QThread):
    progress_update = pyqtSignal(str)    # For updating logs
    progress_percent = pyqtSignal(int)     # For progress bar
    finished_signal = pyqtSignal()         # When scan completes

    def __init__(self, grouped_plugins, targets, parent=None):
        """
        grouped_plugins: list of tuples (plugin, [commands])
        targets: list of target domains
        """
        super().__init__(parent)
        self.grouped_plugins = grouped_plugins
        self.targets = targets
        self.pause_flag = False
        self._pause_mutex = QMutex()
        self._pause_cond = QWaitCondition()
        self.skip_domain = False
        self.skip_command = False
        self.skip_tool = False
        self._stop_requested = False

    def pause(self):
        self.pause_flag = True
        self.progress_update.emit("<i>Scan paused.</i>")

    def resume(self):
        self.pause_flag = False
        self._pause_cond.wakeAll()
        self.progress_update.emit("<i>Scan resumed.</i>")

    def stop(self):
        self._stop_requested = True
        # If a subprocess is running, attempt to kill it.
        import os
        if utils.current_process:
            try:
                os.killpg(os.getpgid(utils.current_process.pid), 2)  # Send SIGINT to the process group.
                self.progress_update.emit("<i>Terminated running command.</i>")
            except Exception as e:
                self.progress_update.emit(f"<i>Error terminating process: {e}</i>")

    def set_skip_domain(self):
        self.skip_domain = True

    def set_skip_command(self):
        self.skip_command = True

    def set_skip_tool(self):
        self.skip_tool = True

    def run(self):
        total_tasks = sum(len(commands) for _, commands in self.grouped_plugins) * len(self.targets)
        task_counter = 0

        # Loop sequentially over each plugin, command, and target.
        for plugin, commands in self.grouped_plugins:
            self.progress_update.emit(f"<b>Running tool: {plugin.name}</b>")
            for command in commands:
                self.progress_update.emit(f"<b>Executing command: {command}</b>")
                for target in self.targets:
                    # Pause check.
                    self._pause_mutex.lock()
                    while self.pause_flag:
                        self._pause_cond.wait(self._pause_mutex)
                    self._pause_mutex.unlock()

                    if self._stop_requested:
                        self.progress_update.emit("<i>Scan stopped by user.</i>")
                        self.finished_signal.emit()
                        return

                    # Skip flags handling.
                    if self.skip_domain:
                        self.progress_update.emit(f"<i>Skipped domain: {target}</i>")
                        self.skip_domain = False
                        continue
                    if self.skip_command:
                        self.progress_update.emit("<i>Skipping current command for remaining targets.</i>")
                        self.skip_command = False
                        break  # Break out of the target loop for this command.
                    if self.skip_tool:
                        self.progress_update.emit("<i>Skipping current tool entirely.</i>")
                        self.skip_tool = False
                        break  # Break out of the command loop for this tool.

                    try:
                        # Always pass two arguments (even if command is empty).
                        output = plugin.run(target, command)
                    except Exception as e:
                        output = f"Error: {e}"
                    output = output.strip() if output else "No output received."
                    file_path = utils.save_scan_results(plugin.name, target, output, command)
                    log_msg = f"{plugin.name} on {target} completed. Results saved to: {file_path}"
                    self.progress_update.emit(f"<pre>{output}</pre>")
                    self.progress_update.emit(f"<span style='color: green'>{log_msg}</span>")
                    logging.info(log_msg)
                    scan_results_global.append({
                        "tool": plugin.name,
                        "command": command,
                        "target": target,
                        "output": output,
                        "file": file_path
                    })
                    task_counter += 1
                    percent = int((task_counter / total_tasks) * 100)
                    self.progress_percent.emit(percent)
        self.finished_signal.emit()

# ---------------------------
# Dialog for Plugin Creation
# ---------------------------
class PluginCreationDialog(QDialog):
    """Dialog for creating a new plugin."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Plugin")
        self.layout = QVBoxLayout(self)
        self.name_input = QLineEdit()
        self.layout.addWidget(QLabel("Plugin Name:"))
        self.layout.addWidget(self.name_input)
        self.desc_input = QLineEdit()
        self.layout.addWidget(QLabel("Plugin Description:"))
        self.layout.addWidget(self.desc_input)
        self.ok_button = QPushButton("Create Plugin")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

    def get_details(self):
        return self.name_input.text().strip(), self.desc_input.text().strip()

# ---------------------------
# MultiSelectDialog for Command Selection
# ---------------------------
class MultiSelectDialog(QDialog):
    """Dialog for selecting multiple commands from a list."""
    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.layout = QVBoxLayout(self)
        from PyQt5.QtWidgets import QListWidget
        self.list_widget = QListWidget()
        self.list_widget.addItems(items)
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.layout.addWidget(self.list_widget)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

    def selected_items(self):
        return [item.text() for item in self.list_widget.selectedItems()]

# ---------------------------
# Main Window (GUI)
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KaliSec Automator GUI")
        self.resize(1200, 1000)

        # Menu Bar with Skip and Control options.
        menu_bar = self.menuBar()
        skip_menu = menu_bar.addMenu("Skip")
        skip_domain_action = QAction("Skip Current Domain", self)
        skip_domain_action.triggered.connect(self.skip_current_domain)
        skip_menu.addAction(skip_domain_action)
        skip_command_action = QAction("Skip Current Command", self)
        skip_command_action.triggered.connect(self.skip_current_command)
        skip_menu.addAction(skip_command_action)
        skip_tool_action = QAction("Skip Current Tool", self)
        skip_tool_action.triggered.connect(self.skip_current_tool)
        skip_menu.addAction(skip_tool_action)

        plugin_menu = menu_bar.addMenu("Plugin")
        create_plugin_action = QAction("Create New Plugin", self)
        create_plugin_action.triggered.connect(self.create_new_plugin)
        plugin_menu.addAction(create_plugin_action)

        control_menu = menu_bar.addMenu("Control")
        pause_action = QAction("Pause Scan", self)
        pause_action.triggered.connect(self.pause_scan)
        control_menu.addAction(pause_action)
        resume_action = QAction("Resume Scan", self)
        resume_action.triggered.connect(self.resume_scan)
        control_menu.addAction(resume_action)
        stop_action = QAction("Stop Scan & Generate Reports", self)
        stop_action.triggered.connect(self.stop_scan)
        control_menu.addAction(stop_action)
        exit_action = QAction("Exit Application", self)
        exit_action.triggered.connect(self.exit_application)
        control_menu.addAction(exit_action)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Top layout: left for plugin selection, right for target input.
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # Left: Plugin list.
        plugin_widget = QWidget()
        plugin_widget.setMinimumWidth(PLUGIN_WIDTH)
        plugin_layout = QVBoxLayout(plugin_widget)
        plugin_layout.addWidget(QLabel("Available Tools:"))
        self.plugin_list = QListWidget()
        self.plugin_list.setSelectionMode(QListWidget.MultiSelection)
        plugin_layout.addWidget(self.plugin_list)
        top_layout.addWidget(plugin_widget)

        # Right: Targets input.
        target_widget = QWidget()
        target_widget.setMinimumWidth(TARGET_WIDTH)
        target_layout = QVBoxLayout(target_widget)
        target_layout.addWidget(QLabel("Targets (one per line):"))
        self.target_text = QTextEdit()
        target_layout.addWidget(self.target_text)
        load_button = QPushButton("Load Targets from File")
        load_button.clicked.connect(self.load_targets)
        target_layout.addWidget(load_button)
        top_layout.addWidget(target_widget)

        # Controls: Start scanning button and progress bar.
        self.start_button = QPushButton("Start Scanning")
        self.start_button.clicked.connect(self.start_scanning)
        main_layout.addWidget(self.start_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        main_layout.addWidget(self.progress_bar)

        # Log output area.
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        # Load plugins.
        self.plugins = load_plugins()
        if not self.plugins:
            QMessageBox.critical(self, "Error", "No plugins found in the 'plugins' folder.")
            sys.exit(1)
        for plugin in self.plugins:
            display_text = f"{plugin.name} - {plugin.description}"
            self.plugin_list.addItem(display_text)

        self.worker = None

    def load_targets(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Target File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            try:
                targets = utils.read_targets(file_name)
                self.target_text.setPlainText("\n".join(targets))
                self.append_log(f"<span style='color: green'>Loaded {len(targets)} target(s) from file.</span>")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load targets: {e}")

    def append_log(self, text):
        self.log_output.append(text)

    def create_new_plugin(self):
        dialog = PluginCreationDialog(parent=self)
        if dialog.exec_():
            name, description = dialog.get_details()
            template = f'''PLUGIN_NAME = "{name}"
PLUGIN_DESCRIPTION = "{description}"
PLUGIN_COMMANDS = {{
    "default": "default_command"
}}
REQUIRED_TOOLS = []

def run(target, command):
    # Implement your plugin logic here
    return f"Running {{command}} on {{target}} with plugin {name}"
'''
            plugin_path = os.path.join(config.BASE_DIR, "..", "plugins", f"{name.lower().replace(' ', '_')}.py")
            try:
                with open(plugin_path, "w", encoding="utf-8") as f:
                    f.write(template)
                self.append_log(f"<span style='color: green'>Plugin {name} created at {plugin_path}</span>")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create plugin: {e}")

    def start_scanning(self):
        selected_indices = self.plugin_list.selectedIndexes()
        if not selected_indices:
            QMessageBox.warning(self, "Warning", "No tools selected.")
            return

        # Check that targets are provided.
        targets_text = self.target_text.toPlainText().strip()
        if not targets_text:
            QMessageBox.warning(self, "Warning", "No targets provided.")
            return

        selected_plugins = []
        # For each selected plugin, check required tools.
        for index in selected_indices:
            plugin = self.plugins[index.row()]
            skip_plugin = False
            for tool in plugin.required_tools:
                if not utils.check_tool_installed(tool):
                    reply = QMessageBox.question(
                        self,
                        "Tool Missing",
                        f"{tool} is not installed for {plugin.name}. Do you want to attempt to install it?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.append_log(f"Attempting to install {tool}...")
                        if utils.install_tool(tool):
                            self.append_log(f"{tool} installed successfully.")
                        else:
                            self.append_log(f"Failed to install {tool}. Skipping {plugin.name}.")
                            skip_plugin = True
                            break
                    else:
                        self.append_log(f"Skipping {plugin.name} because {tool} is not installed.")
                        skip_plugin = True
                        break
            if not skip_plugin:
                if plugin.commands:
                    dialog = MultiSelectDialog(f"Select Commands for {plugin.name}", list(plugin.commands.keys()), self)
                    if dialog.exec_():
                        commands = dialog.selected_items()
                        # For each selected command, lookup the actual command string.
                        # If multiple commands are selected, they will be grouped together.
                        cmd_list = []
                        for command in commands:
                            actual_command = plugin.commands.get(command, "")
                            cmd_list.append(actual_command)
                        selected_plugins.append((plugin, cmd_list))
                else:
                    selected_plugins.append((plugin, [""]))
        if not selected_plugins:
            QMessageBox.warning(self, "Warning", "No valid tools selected after dependency check.")
            return

        # Group selected plugins by plugin.
        grouped = {}
        for plugin, cmd_list in selected_plugins:
            grouped.setdefault(plugin, []).extend(cmd_list)
        grouped_plugins = list(grouped.items())
        targets = [line.strip() for line in targets_text.splitlines() if line.strip()]
        self.append_log("<b>Starting scan...</b>")
        self.progress_bar.setValue(0)
        self.start_button.setEnabled(False)
        global scan_results_global
        scan_results_global = []  # Reset previous results.
        self.worker = ScanWorker(grouped_plugins, targets)
        self.worker.progress_update.connect(self.append_log)
        self.worker.progress_percent.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.scan_finished)
        self.worker.start()

    def stop_scan(self):
        """Stop the current scan and generate reports for the results so far."""
        if self.worker:
            self.worker.stop()  # Request the worker to stop and kill running commands.
            self.worker.wait()  # Wait for the worker thread to finish
            self.worker = None
            self.scan_finished()

    def scan_finished(self):
        self.append_log("<b>Scan finished.</b>")
        self.start_button.setEnabled(True)
        # Generate HTML and CSV reports per target.
        targets_reports = {}
        for result in scan_results_global:
            target = result['target']
            targets_reports.setdefault(target, []).append(result)
        for target, results in targets_reports.items():
            report_file = utils.generate_report_site(target, results)
            self.append_log(f"<span style='color: green'>HTML Report for {target} generated: {report_file}</span>")
        csv_file = os.path.join(config.BASE_DIR, "scan_results.csv")
        utils.export_results_csv(scan_results_global, csv_file)
        self.append_log(f"<span style='color: green'>CSV Export generated: {csv_file}</span>")
        
        # Ask user if they want to generate a PDF report for each domain.
        reply = QMessageBox.question(
            self,
            "PDF Report",
            "Do you want to generate PDF reports for the domains?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for target, results in targets_reports.items():
                pdf_file = utils.generate_report_site_pdf(target, results)
                self.append_log(f"<span style='color: green'>PDF Report for {target} generated: {pdf_file}</span>")

    def skip_current_domain(self):
        if self.worker:
            self.worker.set_skip_domain()

    def skip_current_command(self):
        if self.worker:
            self.worker.set_skip_command()

    def skip_current_tool(self):
        if self.worker:
            self.worker.set_skip_tool()

    def pause_scan(self):
        if self.worker:
            self.worker.pause()

    def resume_scan(self):
        if self.worker:
            self.worker.resume()

    def exit_application(self):
        """Stop any running scan and exit the application."""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        QApplication.quit()

# ---------------------------
# Main Function
# ---------------------------
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
