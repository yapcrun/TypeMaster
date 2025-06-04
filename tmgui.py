from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QLabel, QVBoxLayout, QLineEdit, QHBoxLayout, QListWidget
from PyQt6.QtGui import QIcon
import sys
from pynput import keyboard
from time import sleep
import os
import tracker2




class TrackerThread(QThread):
    apm_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.running = True
        self.tracker = tracker2.KeyHandler()

    def on_press(self, key):
        print("AAAAAAAAAAAAA")
        data = self.tracker.on_press(key)
        print(f"data: {data}")
        apm = data["apm"]
        print(f"apm: {apm}")
        self.apm_signal.emit(apm)

    def run(self):
        print("Tracker thread started.")
        while self.running:
            with keyboard.Listener(
            on_press=self.on_press,
            # on_release=x
            ) as listener:
                try:
                    listener.join()
                except KeyboardInterrupt:
                    print("Listener stopped.")
                    os._exit(0)
                except Exception as e:
                    print(f"An error occurred: {e}")

            # self.update_signal.emit(apm, key_stats) # figure out signal emission


    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tracker_thread = TrackerThread()
        self.tracker_thread.apm_signal.connect(self.update_apm)
        self.tracker_thread.start()

        self.setWindowTitle("TypeMaster")
        self.setGeometry(100, 100, 300, 200)
        self.setWindowIcon(QIcon("COMP_ICON.png"))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # APM Label
        self.label = QLabel("APM: 0")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.label)

        # Key Stats
        self.key_stats = QListWidget()
        self.layout.addWidget(self.key_stats)

        self.button = QPushButton("Submit")
        self.button.clicked.connect(self.on_submit)
        self.layout.addWidget(self.button)

    def on_submit(self):
        self.update_apm(100)
        self.update_key_stats({"A": 5, "B": 3, "C": 2})

    def update_apm(self, apm):
        # TODO: Change text color based on apm
        print("UPDATE APM")
        self.label.setText(f"APM: {apm}")

    def update_key_stats(self, key_stats: dict):
        self.key_stats.clear()
        for key, count in key_stats.items():
            self.key_stats.addItem(f"{key}: {count}")


if __name__ == "__main__":    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    app.exec()