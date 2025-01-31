import sys
import os
import urllib3
import pandas as pd
import requests
import json
import time
import csv
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtCore import Qt, QTimer, QSize
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, 
    QVBoxLayout, QHBoxLayout, QWidget, QTableWidgetItem, QMessageBox, 
    QAction, QDialog, QListWidget, QTextEdit
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DirectoryBrowser(QMainWindow):
    def __init__(self, version):
        super().__init__()
        self.init_main_layout(version)
    
    def init_main_layout(self, version):
        self.version = version  
        self.log_dir = "logs"
        self.ensure_log_directory() 
        self.setWindowTitle(f"Data Transfer - v{self.version}")
        self.setGeometry(200, 200, 700, 200)
        # self.setStyleSheet("background-color: lightblue;")

        self.version = version
        self.log_dir = "logs"  
        self.ensure_log_directory()

        self.latest_csv_file = None
        self.latest_json_data = None
        self.previous_csv_file = None
        self.err_msg = None

        self.current_log_file = self.generate_log_filename()
        self.generate_log_file() 

        self.log_timer = QTimer(self)
        self.log_timer.setInterval(60 * 1000)  # 1 minute (60,000 milliseconds)
        self.log_timer.start()

        icon_path = "images/your-logo.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file '{icon_path}' not found. Default icon will be used.")

        self.init_menu()

        self.central_widget = QWidget()
        main_layout = QVBoxLayout()  

        top_layout = QHBoxLayout()

        self.browse_button = QPushButton("Browse Directory", self)
        self.browse_button.setToolTip("Click to browse and select a directory.")
        self.browse_button.setFixedSize(110, 25) 
        self.browse_button.clicked.connect(self.browse_directory)
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color:rgb(167, 141, 86); /* Green background */
                color: white;             /* White text */
                border: none;             /* No border */
                border-radius: 5px;       /* Rounded corners */
                padding: 5px 10px;        /* Padding inside the button */
            }
            QPushButton:hover {
                background-color:rgb(148, 129, 78); /* Slightly darker green when hovered */
            }
            QPushButton:pressed {
                background-color:rgb(139, 130, 78); /* Even darker green when clicked */
            }
        """)
        top_layout.addWidget(self.browse_button)  

        self.msg_label = QLabel("", self)
        self.msg_label.setAlignment(Qt.AlignRight)
        self.msg_label.setStyleSheet("color: darkblue;")
        top_layout.addWidget(self.msg_label) 

        self.start_button = QPushButton("Start", self)
        self.start_button.setToolTip("Click to start extracting data.")
        self.start_button.setFixedSize(90, 30) 
        self.start_button.clicked.connect(self.start_all)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* Green background */
                color: white;             /* White text */
                border: none;             /* No border */
                border-radius: 5px;       /* Rounded corners */
                padding: 5px 10px;        /* Padding inside the button */
            }
            QPushButton:hover {
                background-color: #45a049; /* Slightly darker green when hovered */
            }
            QPushButton:pressed {
                background-color: #3e8e41; /* Even darker green when clicked */
            }
        """)
        self.start_button.setVisible(False)
        top_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setToolTip("Click to stop extracting data.")
        self.stop_button.setFixedSize(90, 30) 
        self.stop_button.clicked.connect(self.stop_data_extraction)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color:rgb(196, 77, 77); /* Green background */
                color: white;             /* White text */
                border: none;             /* No border */
                border-radius: 5px;       /* Rounded corners */
                padding: 5px 10px;        /* Padding inside the button */
            }
            QPushButton:hover {
                background-color:rgb(158, 62, 62); /* Slightly darker green when hovered */
            }
            QPushButton:pressed {
                background-color:rgb(126, 54, 54); /* Even darker green when clicked */
            }
        """)
        self.stop_button.setVisible(False)
        top_layout.addWidget(self.stop_button)

        main_layout.addLayout(top_layout)
        self.directory_label = QLabel("File Source Directory: None", self)
        self.directory_label.setStyleSheet("padding-left: 5px; color: maroon;")
        main_layout.addWidget(self.directory_label) 
        
        self.latestfile_label = QLabel("Latest File: None", self)
        self.latestfile_label.setStyleSheet("padding-left: 5px; color: darkblue;")
        main_layout.addWidget(self.latestfile_label)

        # Create the label to display the GIF
        self.gif_label = QLabel(self)
        self.gif_label.setAlignment(Qt.AlignCenter) 
        main_layout.addWidget(self.gif_label)        

        main_layout.addStretch()

        bottom_layout = QHBoxLayout()
        self.network_status_label = QLabel(self)
        self.network_status_label.setAlignment(Qt.AlignLeft)
        self.network_status_label.setStyleSheet("color: red;")
        bottom_layout.addWidget(self.network_status_label) 

        self.check_network_connection()

        bottom_layout.addWidget(QLabel(f"Your Team", self), alignment=Qt.AlignRight)
        bottom_layout.itemAt(bottom_layout.count() - 1).widget().setStyleSheet("color: gray;")

        main_layout.addLayout(bottom_layout)

        self.central_widget.setLayout(main_layout)
        self.setCentralWidget(self.central_widget)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # Set the timer interval to 1 hour (3600000 ms)
        self.timer.timeout.connect(self.timer_timeout)

        self.selected_directory = None

        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.setInterval(5000) 
        self.heartbeat_timer.timeout.connect(self.check_network_connection)
        self.heartbeat_timer.start()   

        # Set up the GIF using QMovie
        self.movie = QMovie("images/processing.gif")  
        self.movie.setScaledSize(QSize(60, 60))
        self.gif_label.setMovie(self.movie) 

    def init_menu(self):
            # Create the menu bar
            menu_bar = self.menuBar()
            file_menu = menu_bar.addMenu("File")

            # Add actions to "File" menu
            exit_action = QAction("Exit", self)
            # exit_action.setShortcut("Ctrl+Q")
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

            # Add "Logs" submenu
            logs_menu = menu_bar.addMenu("Logs")

            # Add actions to "Logs" submenu
            view_logs_action = QAction("View Logs", self)
            # view_logs_action.setShortcut("Ctrl+L")
            view_logs_action.triggered.connect(self.view_logs)
            logs_menu.addAction(view_logs_action)

            help_menu = menu_bar.addMenu("Help")

            about_action = QAction("About", self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)

    def start_all(self):
        self.show_gif()
        self.start_data_extraction()

    def check_network_connection(self):
        srv_url = "https://your_rest_api_url" # RestApi
        try:
            response = requests.get(srv_url, timeout=3, verify=False)
            if response.status_code == 200:
                self.network_status_label.setText("Network Status: Connected")
                self.network_status_label.setStyleSheet("color: green;")
            else:
                self.network_status_label.setText("Network Status: Disconnected")
                self.network_status_label.setStyleSheet("color: red;")
                self.write_to_log("Network Status: Disconnected")
        except requests.RequestException:
            self.network_status_label.setText("Network Status: Disconnected")
            self.network_status_label.setStyleSheet("color: red;")
            self.write_to_log("Network Status: Disconnected")

    def update_button_states(self):
        if self.log_dir:
            self.start_button.setVisible(True)
            self.stop_button.setVisible(True)
        else:
            self.start_button.setVisible(False)
            self.stop_button.setVisible(False)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.selected_directory = directory
            self.directory_label.setText(f"Selected Directory: {directory}")
            self.msg_label.setText("")
        else:
            self.directory_label.setText("Selected Directory: None")
            self.log_dir = None

        self.update_button_states()

    def load_latest_csv(self, directory):
        csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]

        if csv_files:
            latest_file = max(csv_files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
            latest_file_path = os.path.join(directory, latest_file)

            # Check if the latest file is different from the previous one
            if latest_file_path != self.previous_csv_file:
                self.previous_csv_file = latest_file_path
                self.latest_csv_file = latest_file_path
                self.latestfile_label.setText(f"Latest CSV File: {latest_file}")
                self.write_to_log(f"Latest CSV File: {latest_file}")

                self.load_csv(latest_file_path)
            else:
                self.latestfile_label.setText("No new CSV file found.")
        else:
            self.latestfile_label.setText("No CSV files found.")
            # self.write_to_log("No CSV files found.")

    def load_csv(self, file_path):
        error_msg = ""  # Initialize error_msg to avoid UnboundLocalError

        try:
            processed_rows = []
            with open(file_path, mode='r', newline='', encoding='utf-8') as file:
                csv_reader = csv.reader(file)

                # Read header
                header = next(csv_reader, None)
                if header is None:
                    raise ValueError("CSV file is empty or has no header.")

                for row in csv_reader:
                    row = row[:8]  # Limit to 8 columns
                    row = [cell.strip().replace('\x00', '') for cell in row]

                    if not any(row):  # Skip completely empty rows
                        continue

                    processed_rows.append(row)

            # Debugging: Print length of processed rows
            if not processed_rows:
                raise ValueError("No valid data found in the CSV file.")

            # Create DataFrame
            df = pd.DataFrame(processed_rows)

            # Debugging: Print DataFrame info
            # print("DataFrame Info:")
            # print(df.info())
            # print(df.head())

            # Ensure DataFrame has 8 columns before renaming
            if df.shape[1] != 8:
                raise ValueError(f"Expected 8 columns, but got {df.shape[1]}.")

            # Rename columns
            df.columns = ["Col1", "Col2", "Col3", "Col4", "Col5", "Col6", "Col7", "Col8"]

            # Send data to API (Ensure this function is defined)
            self.send_data_to_api(df)

        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
        except ValueError as ve:
            error_msg = f"Value error: {ve}"
        except Exception as e:
            error_msg = f"Error reading CSV file: {e}"
        finally:
            if error_msg:  # Only display if there's an error
                self.msg_label.setText(error_msg)
                self.write_to_log(error_msg)

    def send_data_to_api(self, df):

        api_url = "https://your_rest_api_url"  # RestApi for to post the csv data
        headers = {
            "Content-Type": "application/json"
        }

        # Customize the json item names
        column_name_mapping   = {
            'column_1': 'column_1',
            'column_2': 'column_2',
            'column_3': 'column_3',
            'column_4': 'column_4',
            'column_5': 'column_5',
            'column_6': 'column_6',
            'column_7': 'column_7',
            'column_8': 'column_8'
        }

        try:
            df.columns = list(column_name_mapping.values())
            # df = df.rename(columns=column_name_mapping)
        except Exception as e:
            raise ValueError(f"Error renaming DataFrame columns: {e}")
        
        if 'column_7' in df.columns:
            df['column_7'] = df['column_7'].astype(str)

        self.latest_json_data = df.to_json(orient='records')

        self.latest_json_data = self.prettify_json(self.latest_json_data)
        try:
            response = requests.post(api_url, data=self.latest_json_data, headers=headers, verify=False)
            response.raise_for_status() 
            
            self.msg_label.setText(f"Api Response: {response.text}")
            self.write_to_log(f"{response.text}")
            # self.latestfile_label.setText(f"API Response: {response.text}")
            # self.generate_log_file()

        except requests.exceptions.RequestException as e:
            print(f"Error sending data to API: {e}")
            raise

    def display_csv(self, df):
        custom_column_names = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8']
        
        df.columns = custom_column_names

        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])

        self.table.setHorizontalHeaderLabels(df.columns)

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                self.table.setItem(row, col, QTableWidgetItem(str(df.iat[row, col])))

    def prettify_json(self, json_data):
        try:
            parsed_json = json.loads(json_data)
            return json.dumps(parsed_json, indent=4)  
        except json.JSONDecodeError as e:
            print(f"Error pretty-printing JSON: {e}")
            return json_data  

    def start_data_extraction(self):
        if self.selected_directory: 
            self.timer.start()
            self.browse_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.msg_label.setText("Data transfer started")
        else:
            self.msg_label.setText("No directory selected")

    def timer_timeout(self):
        if self.selected_directory: 
            self.load_latest_csv(self.selected_directory)

    def stop_data_extraction(self):
        self.stop_gif() 
        self.timer.stop()
        self.msg_label.setText("Data transfer stopped")
        self.browse_button.setEnabled(True)
        self.start_button.setEnabled(True)

    def view_logs(self):
        try:
            log_files = [f for f in os.listdir(self.log_dir) if f.endswith(".txt")]
            if log_files:

                log_files = sorted(
                    log_files,
                    key=lambda f: os.path.getmtime(os.path.join(self.log_dir, f)),
                    reverse=True
                )
                dialog = LogViewerDialog(log_dir=self.log_dir, log_files=log_files)
                dialog.exec_()
            else:
                QMessageBox.information(self, "View Logs", "No log files found in the logs directory.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading logs: {e}")
            self.write_to_log(f"An error occurred while loading logs: {e}")

    def show_about(self):
        QMessageBox.information(self, "About", "Data Transfer\n"
                                               f"Version {self.version}\n\n"
                                               "Copyright (c) 2025 Your Team. All rights reserved.")

    def show_gif(self):
        if self.movie.state() == QMovie.NotRunning:
            self.movie.start()  
        else:
            self.movie.stop()  
            self.movie.start()  
        self.gif_label.setMovie(self.movie) 

    def stop_gif(self):
        self.movie.stop()  

    def ensure_log_directory(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def generate_log_filename(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H")
        return os.path.join(self.log_dir, f"latest_csv_log_{timestamp}.txt")

    def generate_log_file(self):
        self.current_log_file = self.generate_log_filename()

        try:
            with open(self.current_log_file, "a") as log_file:
                log_entry = f"Log generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                log_file.write(log_entry)

                if self.latest_csv_file:
                    log_file.write(f"Latest CSV File: {self.latest_csv_file}\n")

                if self.latest_json_data:
                    self.latest_json_data = self.prettify_json(self.latest_json_data)
                    log_file.write(f"JSON Data:\n{self.latest_json_data}\n")
                    
                log_file.write("=" * 50 + "\n")

        except IOError as e:
            print(f"Error writing to log file: {e}")
            self.write_to_log(f"Error writing to log file: {e}")

        # Clean up old log files
        self.cleanup_old_files(self.log_dir)

    def write_to_log(self, message):
        if not hasattr(self, 'current_log_file') or not self.current_log_file:
            self.current_log_file = self.generate_log_filename()
            self.generate_log_file()  # Create the log file if it doesn't exist

        try:
            with open(self.current_log_file, "a") as log_file:
                log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        except IOError as e:
            print(f"Failed to write to log: {e}")

    def log_latest_csv(self, latest_file):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {latest_file}\n"
        
        try:
            with open(self.log_file_path, "a") as log_file:
                log_file.write(log_entry)
            print(f"Logged: {log_entry.strip()}")
        except IOError as e:
            print(f"Error writing to log file: {e}")

    def cleanup_old_files(self, directory):
        one_week_ago = time.time() - (7 * 24 * 60 * 60)  # Current time minus 7 days in seconds

        for file_name in os.listdir(directory):
            file_path = os.path.join(directory, file_name)

            # Ensure we're only looking at files (not directories)
            if os.path.isfile(file_path):
                file_mod_time = os.path.getmtime(file_path)

                if file_mod_time < one_week_ago:
                    try:
                        os.remove(file_path)
                        # Optional: Log deletion
                        with open("cleanup_log.txt", "a") as log_file:
                            log_file.write(f"{time.ctime()}: Deleted {file_name}\n")
                    except Exception as e:
                        print(f"Error deleting file {file_name}: {e}")
                        self.write_to_log(f"Error deleting file {file_name}: {e}")

class LogViewerDialog(QDialog):
    def __init__(self, log_dir, log_files):
        super().__init__()

        self.log_dir = log_dir
        self.setWindowTitle("View Logs")
        self.setGeometry(300, 200, 600, 400)

        layout = QVBoxLayout()

        # List of log files
        self.log_list = QListWidget(self)
        self.log_list.addItems(log_files)
        self.log_list.itemClicked.connect(self.load_log_content)
        layout.addWidget(self.log_list)

        # Log content display
        self.log_content = QTextEdit(self)
        self.log_content.setReadOnly(True)
        layout.addWidget(self.log_content)

        # Close button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def load_log_content(self, item):
        """Load and display the content of the selected log file."""
        selected_log_file = item.text()
        log_file_path = os.path.join(self.log_dir, selected_log_file)
        try:
            with open(log_file_path, "r") as file:
                content = file.read()
                self.log_content.setText(content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unable to load log file: {e}")

def main():
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon("images/your-logo.png")) 

    app_version = "1.0.0"

    window = DirectoryBrowser(version=app_version)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
