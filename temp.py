#!/usr/bin/env python3
"""
This tutorial demonstrates how to build a basic PyQt5 application that processes tasks
in the background using QThread. You can load tasks, enter items to process (one per line),
select commands for each task, and see the progress and output in the GUI.
"""

import sys
import time
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QVBoxLayout,
    QHBoxLayout, QPushButton, QListWidget, QTextEdit, QLabel,
    QProgressBar, QMessageBox, QDialog
)
from PyQt5.QtCore import QThread, pyqtSignal

# Define a dummy task to simulate processing. Modify this class to implement your own task logic.
class DummyTask:
    def __init__(self, name, description, commands=None):
        self.name = name
        self.description = description
        self.commands = commands or {}  # A dictionary mapping command names to command values
    
    def run(self, item, command):
        # Simulate a time-consuming process (e.g., a network call or heavy computation)
        time.sleep(1)
        return f"{self.name} processed item '{item}' with command '{command}'."


# Load dummy tasks that simulate available tools.
def load_tasks():
    # Create two dummy tasks with available commands. You can add more or modify these.
    task1 = DummyTask("TaskOne", "Simulated Task One", commands={"Option A": "A", "Option B": "B"})
    task2 = DummyTask("TaskTwo", "Simulated Task Two", commands={"Option X": "X", "Option Y": "Y"})
    return [task1, task2]


# Worker thread to run tasks in the background.
class ProcessWorker(QThread):
    progress_update = pyqtSignal(str)  # Signal to update the log output
    progress_percent = pyqtSignal(int)  # Signal to update the progress bar
    finished_signal = pyqtSignal()      # Signal to indicate that processing is complete

    def __init__(self, tasks, items, parent=None):
        super().__init__(parent)
        self.tasks = tasks  # List of tuples (task, command) to run
        self.items = items  # List of items to process

    def run(self):
        total_steps = len(self.tasks) * len(self.items)
        step_count = 0
        for task, command in self.tasks:
            self.progress_update.emit(f"<b>Starting task: {task.name}</b>")
            for idx, item in enumerate(self.items, start=1):
                step_count += 1
                self.progress_update.emit(
                    f"Processing <i>{item}</i> ({idx}/{len(self.items)}) using <u>{task.name} ({command})</u>..."
                )
                try:
                    # Run the dummy task; in a real application, this could be any long-running operation.
                    result = task.run(item, command)
                    result = result.strip() if result else "No result."
                    self.progress_update.emit(f"<pre>{result}</pre>")
                except Exception:
                    error_msg = "Error: " + traceback.format_exc()
                    self.progress_update.emit(f"<span style='color: red'>{error_msg}</span>")
                percent = int((step_count / total_steps) * 100)
                self.progress_percent.emit(percent)
        self.finished_signal.emit()


# A simple dialog that lets the user select multiple commands.
class MultiSelectDialog(QDialog):
    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        self.layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.addItems(items)
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.layout.addWidget(self.list_widget)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)
    
    def selected_items(self):
        # Return a list of the selected command names.
        return [item.text() for item in self.list_widget.selectedItems()]


# Main window class that builds the user interface.
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Tutorial - Background Processing")
        self.resize(800, 600)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Top area divided into a task selection panel and an item input area.
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # Left panel: Task selection list.
        task_layout = QVBoxLayout()
        top_layout.addLayout(task_layout)
        task_layout.addWidget(QLabel("Available Tasks:"))
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QListWidget.MultiSelection)
        task_layout.addWidget(self.task_list)

        # Right panel: Item input area.
        item_layout = QVBoxLayout()
        top_layout.addLayout(item_layout)
        item_layout.addWidget(QLabel("Items to process (one per line):"))
        self.item_text = QTextEdit()
        item_layout.addWidget(self.item_text)
        load_button = QPushButton("Load Items from File")
        load_button.clicked.connect(self.load_items)
        item_layout.addWidget(load_button)

        # Controls: Start button and progress bar.
        self.start_button = QPushButton("Start Processing")
        self.start_button.clicked.connect(self.start_processing)
        main_layout.addWidget(self.start_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        main_layout.addWidget(self.progress_bar)

        # Log output area where process updates are displayed.
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        # Load the dummy tasks.
        self.tasks = load_tasks()
        for task in self.tasks:
            self.task_list.addItem(f"{task.name} - {task.description}")
        self.worker = None

    def load_items(self):
        # Open a file dialog to load items from a text file.
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Item File", "", "Text Files (*.txt);;All Files (*)")
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    items = [line.strip() for line in f if line.strip()]
                self.item_text.setPlainText("\n".join(items))
                self.append_log(f"<span style='color: green'>Loaded {len(items)} item(s) from file.</span>")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load items: {e}")

    def append_log(self, text):
        # Append HTML formatted text to the log output area.
        self.log_output.append(text)

    def start_processing(self):
        # Check that at least one task is selected.
        selected_indices = self.task_list.selectedIndexes()
        if not selected_indices:
            QMessageBox.warning(self, "Warning", "No tasks selected.")
            return

        selected_tasks = []
        # For each selected task, if commands are available, let the user choose.
        for index in selected_indices:
            task = self.tasks[index.row()]
            if task.commands:
                command_dialog = MultiSelectDialog(f"Select Commands for {task.name}", list(task.commands.keys()), self)
                if command_dialog.exec_():
                    commands = command_dialog.selected_items()
                    for command in commands:
                        selected_tasks.append((task, task.commands[command]))
                else:
                    selected_tasks.append((task, None))
            else:
                selected_tasks.append((task, None))

        # Get items to process from the text input.
        items_text = self.item_text.toPlainText().strip()
        if not items_text:
            QMessageBox.warning(self, "Warning", "No items provided.")
            return
        items = [line.strip() for line in items_text.splitlines() if line.strip()]

        self.append_log("<b>Starting processing...</b>")
        self.progress_bar.setValue(0)
        self.start_button.setEnabled(False)

        # Create and start the worker thread.
        self.worker = ProcessWorker(selected_tasks, items)
        self.worker.progress_update.connect(self.append_log)
        self.worker.progress_percent.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.processing_finished)
        self.worker.start()

    def processing_finished(self):
        # Called when the worker thread finishes processing.
        self.append_log("<b>Processing finished.</b>")
        self.start_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
