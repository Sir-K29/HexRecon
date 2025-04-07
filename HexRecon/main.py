#!/usr/bin/env python3
import sys
import os
import time
import datetime
import logging
import subprocess
import re
import psutil  # For CPU and memory monitoring

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QVBoxLayout,
    QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QTextEdit,
    QLabel, QProgressBar, QMessageBox, QDialog, QAction, QLineEdit, QTabWidget,
    QCheckBox, QFormLayout, QSplitter, QComboBox, QSystemTrayIcon, QMenu, QInputDialog
)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QIcon

import pyqtgraph as pg

from pentest import config, utils
from pentest.plugin_manager import load_plugins, Plugin

# Setup enhanced logging (Rotating handler etc. is configured in utils.setup_logging)
utils.setup_logging()

# Global variable for scan results
scan_results_global = []

# Define layout constants
PLUGIN_WIDTH = 300
TARGET_WIDTH = 300

# ---------------------------
# Worker Thread for Scanning
# ---------------------------
class ScanWorker(QThread):
    progress_update = pyqtSignal(str)    # For updating logs
    progress_percent = pyqtSignal(int)     # For progress bar
    finished_signal = pyqtSignal()         # When scan completes
    task_update = pyqtSignal(int, int, str)  # completed, total, tool name

    def __init__(self, grouped_plugins, targets, parent=None):
        super().__init__(parent)
        self.grouped_plugins = grouped_plugins
        self.targets = targets
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True
        if utils.current_process:
            try:
                os.killpg(os.getpgid(utils.current_process.pid), 2)  # SIGINT to process group.
                self.progress_update.emit("<span style='color: red;'>Terminated running command.</span>")
            except Exception as e:
                self.progress_update.emit(f"<span style='color: red;'>Error terminating process: {e}</span>")

    def run(self):
        total_tasks = sum(len(commands) for _, commands in self.grouped_plugins) * len(self.targets)
        task_counter = 0
        tool_task_counters = {plugin.name: 0 for plugin, _ in self.grouped_plugins}

        for plugin, commands in self.grouped_plugins:
            self.progress_update.emit(f"<b style='color: blue;'>Running tool: {plugin.name}</b>")
            for command in commands:
                self.progress_update.emit(f"<b style='color: blue;'>Executing command: {command}</b>")
                for target in self.targets:
                    if self._stop_requested:
                        self.progress_update.emit("<i style='color: red;'>Scan stopped by user.</i>")
                        self.finished_signal.emit()
                        return

                    try:
                        output = plugin.run(target, command)
                    except Exception as e:
                        output = f"Error: {e}"
                    output = output.strip() if output else "No output received."
                    file_path = utils.save_scan_results(plugin.name, target, output, command)
                    log_msg = f"{plugin.name} on {target} completed. Results saved to: {file_path}"
                    self.progress_update.emit(f"<pre style='color: gray;'>{output}</pre>")
                    self.progress_update.emit(f"<span style='color: green;'>{log_msg}</span>")
                    logging.info(log_msg)
                    scan_results_global.append({
                        "tool": plugin.name,
                        "command": command,
                        "target": target,
                        "output": output,
                        "file": file_path
                    })
                    task_counter += 1
                    tool_task_counters[plugin.name] += 1
                    self.task_update.emit(task_counter, total_tasks, plugin.name)
                    percent = int((task_counter / total_tasks) * 100)
                    self.progress_percent.emit(percent)
        self.finished_signal.emit()

# ---------------------------
# Plugin Creation Dialog
# ---------------------------
class PluginCreationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Plugin")
        layout = QVBoxLayout(self)
        self.name_input = QLineEdit()
        self.name_input.setToolTip("Enter the new plugin name")
        layout.addWidget(QLabel("Plugin Name:"))
        layout.addWidget(self.name_input)
        self.desc_input = QLineEdit()
        self.desc_input.setToolTip("Enter a brief description for the plugin")
        layout.addWidget(QLabel("Plugin Description:"))
        layout.addWidget(self.desc_input)
        self.ok_button = QPushButton("Create Plugin")
        self.ok_button.setToolTip("Click to create the plugin file")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

    def get_details(self):
        return self.name_input.text().strip(), self.desc_input.text().strip()

# ---------------------------
# MultiSelect Dialog for Command Selection
# ---------------------------
class MultiSelectDialog(QDialog):
    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.setToolTip("Select one or more commands to run for this tool")
        self.list_widget.addItems(items)
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.list_widget)
        self.ok_button = QPushButton("OK")
        self.ok_button.setToolTip("Confirm selected commands")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

    def selected_items(self):
        return [item.text() for item in self.list_widget.selectedItems()]

# ---------------------------
# Main Window with Tabs and Advanced UI
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HexRecon GUI")
        self.resize(1600, 900)

        # Setup system tray icon for error notifications.
        self.tray_icon = QSystemTrayIcon(QIcon("icon.png"), self)
        tray_menu = QMenu()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_application)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Create tabs (Scan, Plugins).
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.scan_tab = self.create_scan_tab()
        self.plugin_tab = self.create_plugin_tab()

        self.tabs.addTab(self.scan_tab, "Scan")
        self.tabs.addTab(self.plugin_tab, "Plugins")

        # Menu bar.
        menu_bar = self.menuBar()
        plugin_menu = menu_bar.addMenu("Plugin")
        create_plugin_action = QAction("Create New Plugin", self)
        create_plugin_action.setToolTip("Create a new plugin file")
        create_plugin_action.triggered.connect(self.create_new_plugin)
        plugin_menu.addAction(create_plugin_action)
        control_menu = menu_bar.addMenu("Control")
        stop_action = QAction("Stop Scan & Generate Reports", self)
        stop_action.setToolTip("Stop the current scan and generate reports")
        stop_action.triggered.connect(self.stop_scan)
        control_menu.addAction(stop_action)
        exit_action = QAction("Exit Application", self)
        exit_action.setToolTip("Exit the application")
        exit_action.triggered.connect(self.exit_application)
        control_menu.addAction(exit_action)

        # Load plugins.
        self.all_plugins = load_plugins()
        if not self.all_plugins:
            self.show_error("No plugins found in the 'plugins' folder.")
            sys.exit(1)
        self.enabled_plugins = {plugin: True for plugin in self.all_plugins}
        self.refresh_plugin_lists()

        self.worker = None
        self.scan_start_time = None

        # Dashboard timers and data.
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self.update_dashboard)
        self.chart_data = {}  # key: tool name, value: (times list, progress list)
        self.cpu_data = []
        self.mem_data = []
        self.chart_start_time = None

    # --- New Method: create_new_plugin ---
    def create_new_plugin(self):
        dialog = PluginCreationDialog(self)
        if dialog.exec_():
            name, description = dialog.get_details()
            if not name:
                QMessageBox.warning(self, "Warning", "Plugin name cannot be empty.")
                return
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
            plugin_filename = f"{name.lower().replace(' ', '_')}.py"
            plugin_path = os.path.join(config.PLUGIN_DIR, plugin_filename)
            try:
                with open(plugin_path, "w", encoding="utf-8") as f:
                    f.write(template)
                self.append_scan_log(f"<span style='color: green;'>Plugin {name} created at {plugin_path}</span>")
                # Reload plugins.
                self.all_plugins = load_plugins()
                self.enabled_plugins = {plugin: True for plugin in self.all_plugins}
                self.refresh_plugin_lists()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create plugin: {e}")

    def create_scan_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        plugin_label = QLabel("Available Tools:")
        plugin_label.setToolTip("Select the tools you wish to run")
        left_layout.addWidget(plugin_label)
        self.plugin_list = QListWidget()
        self.plugin_list.setToolTip("Multi-select tools to use for scanning")
        self.plugin_list.setSelectionMode(QListWidget.MultiSelection)
        left_layout.addWidget(self.plugin_list)
        target_label = QLabel("Targets (one per line):")
        target_label.setToolTip("Enter target domains, one per line")
        left_layout.addWidget(target_label)
        self.target_text = QTextEdit()
        self.target_text.setToolTip("Input target domains or IP addresses here")
        left_layout.addWidget(self.target_text)
        load_btn = QPushButton("Load Targets from File")
        load_btn.setToolTip("Load targets from a text file")
        load_btn.clicked.connect(self.load_targets)
        left_layout.addWidget(load_btn)
        self.start_button = QPushButton("Start Scanning")
        self.start_button.setToolTip("Click to start scanning the selected targets with the chosen tools")
        self.start_button.clicked.connect(self.start_scanning)
        left_layout.addWidget(self.start_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setToolTip("Visual indicator of overall scan progress")
        self.progress_bar.setRange(0, 100)
        left_layout.addWidget(self.progress_bar)
        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        # Use QTextEdit to support HTML formatting (colored output)
        self.scan_log = QTextEdit()
        self.scan_log.setToolTip("Scan log output")
        self.scan_log.setReadOnly(True)
        right_layout.addWidget(self.scan_log)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        return widget

    def create_plugin_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        info_label = QLabel("Enable/Disable and Edit Plugins:")
        layout.addWidget(info_label)
        self.plugin_manage_list = QListWidget()
        self.plugin_manage_list.setToolTip("Check to enable plugins; double-click to edit settings")
        self.plugin_manage_list.itemChanged.connect(self.handle_plugin_enable_change)
        self.plugin_manage_list.itemDoubleClicked.connect(self.edit_plugin_settings)
        layout.addWidget(self.plugin_manage_list)
        """
        update_btn = QPushButton("Update Plugins (Git Pull)")
        update_btn.setToolTip("Update plugins from remote repository")
        update_btn.clicked.connect(self.update_plugins)
        layout.addWidget(update_btn)
        """
        return widget

    def refresh_plugin_lists(self):
        self.plugin_list.clear()
        self.plugin_manage_list.clear()
        for plugin in self.all_plugins:
            if self.enabled_plugins.get(plugin, True):
                display_text = f"{plugin.name} - {plugin.description}"
                item = QListWidgetItem(display_text)
                self.plugin_list.addItem(item)
            item = QListWidgetItem(f"{plugin.name} - {plugin.description}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            item.setCheckState(Qt.Checked if self.enabled_plugins.get(plugin, True) else Qt.Unchecked)
            self.plugin_manage_list.addItem(item)

    def handle_plugin_enable_change(self, item):
        plugin_name = item.text().split(" - ")[0]
        for plugin in self.all_plugins:
            if plugin.name == plugin_name:
                self.enabled_plugins[plugin] = (item.checkState() == Qt.Checked)
        self.refresh_plugin_lists()

    def edit_plugin_settings(self, item):
        plugin_name = item.text().split(" - ")[0]
        for plugin in self.all_plugins:
            if plugin.name == plugin_name:
                new_desc, ok = QInputDialog.getText(self, "Edit Plugin", f"Edit description for {plugin.name}:", text=plugin.__dict__.get("PLUGIN_DESCRIPTION", ""))
                if ok and new_desc:
                    plugin.__dict__["PLUGIN_DESCRIPTION"] = new_desc
                    self.refresh_plugin_lists()
                break

    def update_plugins(self):
        plugins_dir = config.PLUGIN_DIR
        try:
            result = subprocess.run(["git", "-C", plugins_dir, "pull"], capture_output=True, text=True, timeout=60)
            QMessageBox.information(self, "Update Plugins", f"Update Result:\n{result.stdout}")
        except Exception as e:
            self.show_error(f"Error updating plugins: {e}")

    def load_targets(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Target File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            try:
                targets = utils.read_targets(file_name)
                self.target_text.setPlainText("\n".join(targets))
                self.append_scan_log(f"<span style='color: green;'>Loaded {len(targets)} target(s) from file.</span>")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load targets: {e}")

    def append_scan_log(self, text):
        self.scan_log.append(text)

    def update_dashboard(self):
        if hasattr(self, 'last_completed') and hasattr(self, 'last_total') and self.scan_start_time:
            elapsed = time.time() - self.scan_start_time
            elapsed_str = f"{int(elapsed)}s"
            remaining_str = "N/A"
            if self.last_completed > 0 and self.last_total:
                estimated_total = elapsed / (self.last_completed / self.last_total)
                remaining = estimated_total - elapsed
                remaining_str = f"{int(remaining)}s" if remaining > 0 else "0s"
            self.metrics_label.setText(f"Tasks: {self.last_completed} / {self.last_total} | Elapsed: {elapsed_str} | Remaining: {remaining_str}")

        current_time = time.time() - self.chart_start_time if self.chart_start_time else 0
        self.plot_widget.clear()
        for tool, (times, progresses) in self.chart_data.items():
            self.plot_widget.plot(times, progresses, pen=pg.mkPen(width=2), name=tool)
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        self.cpu_data.append(current_time)
        self.mem_data.append(current_time)
        self.cpu_curve.setData(self.cpu_data, [cpu for _ in self.cpu_data])
        self.mem_curve.setData(self.mem_data, [mem for _ in self.mem_data])

    def start_scanning(self):
        selected_indices = self.plugin_list.selectedIndexes()
        if not selected_indices:
            QMessageBox.warning(self, "Warning", "No tools selected.")
            return
        targets_text = self.target_text.toPlainText().strip()
        if not targets_text:
            QMessageBox.warning(self, "Warning", "No targets provided.")
            return

        selected_plugins = []
        for index in selected_indices:
            plugin = list(self.enabled_plugins.keys())[index.row()]
            if not self.enabled_plugins.get(plugin, True):
                continue
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
                        self.append_scan_log(f"<span style='color: orange;'>Attempting to install {tool}...</span>")
                        if utils.install_tool(tool):
                            self.append_scan_log(f"<span style='color: green;'>{tool} installed successfully.</span>")
                        else:
                            self.append_scan_log(f"<span style='color: red;'>Failed to install {tool}. Skipping {plugin.name}.</span>")
                            skip_plugin = True
                            break
                    else:
                        self.append_scan_log(f"<span style='color: red;'>Skipping {plugin.name} because {tool} is not installed.</span>")
                        skip_plugin = True
                        break
            if skip_plugin:
                continue
            if plugin.commands:
                dialog = MultiSelectDialog(f"Select Commands for {plugin.name}", list(plugin.commands.keys()), self)
                if dialog.exec_():
                    commands = dialog.selected_items()
                    cmd_list = [plugin.commands.get(command, "") for command in commands]
                    selected_plugins.append((plugin, cmd_list))
            else:
                selected_plugins.append((plugin, [""]))
        if not selected_plugins:
            QMessageBox.warning(self, "Warning", "No valid tools selected after dependency check.")
            return

        grouped = {}
        for plugin, cmd_list in selected_plugins:
            grouped.setdefault(plugin, []).extend(cmd_list)
        grouped_plugins = list(grouped.items())
        targets = [line.strip() for line in targets_text.splitlines() if line.strip()]

        self.append_scan_log("<span style='color: blue;'>Starting scan...</span>")
        self.progress_bar.setValue(0)
        self.start_button.setEnabled(False)
        global scan_results_global
        scan_results_global = []
        self.scan_start_time = time.time()
        self.chart_start_time = time.time()
        self.last_completed = 0
        self.last_total = sum(len(cmds) for _, cmds in grouped_plugins) * len(targets)
        self.chart_data = {}
        for plugin, cmds in grouped_plugins:
            self.chart_data[plugin.name] = ([], [])
        self.cpu_data = []
        self.mem_data = []
        self.dashboard_timer.start(1000)  # Update every second.
        self.worker = ScanWorker(grouped_plugins, targets)
        self.worker.progress_update.connect(self.append_scan_log)
        self.worker.progress_percent.connect(self.progress_bar.setValue)
        self.worker.task_update.connect(self.handle_task_update)
        self.worker.finished_signal.connect(self.scan_finished)
        self.worker.start()

    def handle_task_update(self, completed, total, tool):
        self.last_completed = completed
        self.last_total = total
        if tool in self.chart_data:
            times, progresses = self.chart_data[tool]
            times.append(time.time() - self.chart_start_time)
            progress = int((completed / total) * 100)
            progresses.append(progress)
            self.chart_data[tool] = (times, progresses)

    def stop_scan(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None
            self.scan_finished()

    def scan_finished(self):
        self.append_scan_log("<span style='color: blue;'>Scan finished.</span>")
        self.start_button.setEnabled(True)
        self.dashboard_timer.stop()
        targets_reports = {}
        for result in scan_results_global:
            target = result['target']
            targets_reports.setdefault(target, []).append(result)
        csv_file = os.path.join(config.BASE_DIR, "scan_results.csv")
        utils.export_results_csv(scan_results_global, csv_file)
        self.append_scan_log(f"<span style='color: green;'>CSV Export generated: {csv_file}</span>")

        # Prompt user for report generation option.
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Generate Report")
        msg_box.setText("Select report type to generate:")
        btn_html = msg_box.addButton("HTML", QMessageBox.AcceptRole)
        btn_pdf = msg_box.addButton("PDF", QMessageBox.AcceptRole)
        btn_both = msg_box.addButton("Both", QMessageBox.AcceptRole)
        btn_none = msg_box.addButton("None", QMessageBox.RejectRole)
        msg_box.exec_()
        choice = msg_box.clickedButton().text()

        if choice in ["HTML", "Both"]:
            for target, results in targets_reports.items():
                report_file = utils.generate_report_site(target, results)
                self.append_scan_log(f"<span style='color: green;'>HTML Report for {target} generated: {report_file}</span>")
        if choice in ["PDF", "Both"]:
            for target, results in targets_reports.items():
                pdf_file = utils.generate_report_site_pdf(target, results)
                self.append_scan_log(f"<span style='color: green;'>PDF Report for {target} generated: {pdf_file}</span>")

    def show_error(self, message):
        self.tray_icon.showMessage("HexRecon Error", message, QSystemTrayIcon.Critical)
        QMessageBox.critical(self, "Error", message)

    def exit_application(self):
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
