from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QLabel, QVBoxLayout, QLineEdit, QHBoxLayout, QListWidget
from PyQt6.QtGui import QIcon
import sys
from pynput import keyboard
from time import sleep
import os
import tracker2

# TODO: Implement the tray functionality w/ qt6 (or old method)
# TODO: Implement hotkey functionality. 
# TODO: Make the list fancy
# TODO: Add a selector for sound packs

class TrackerThread(QThread):
    apm_signal = pyqtSignal(int)
    stats_list_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = True
        self.tracker = tracker2.KeyHandler()
        self.need_update = False

    def on_press(self, key):
        data = self.tracker.on_press(key)
        # print(f"data: {data}")
        apm = data["apm"]
        stats = data["stats"]
        print(f"apm: {apm}")
        self.apm_signal.emit(apm)
        self.stats_list_signal.emit(stats)
        self.need_update = True

    def update_apm(self):
        apm = self.tracker.update_apm(False)
        self.apm_signal.emit(apm)

    def save(self):
        if self.need_update == False: return
        self.tracker.logfile("save")
        self.need_update = False


    def run(self):
        self.stats_list_signal.emit(self.tracker.get_key_stats())
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

    def stop(self):
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TypeMaster")
        self.setGeometry(100, 100, 300, 700)
        self.setWindowIcon(QIcon("COMP_ICON.png"))

        self.tracker_thread = TrackerThread()
        self.tracker_thread.apm_signal.connect(self.update_apm)
        self.tracker_thread.stats_list_signal.connect(self.populate_list)
        self.tracker_thread.start()


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

        # --- QTimer setup ---
        self.apm_timer = QTimer(self)
        self.apm_timer.timeout.connect(self.tracker_thread.update_apm)
        self.apm_timer.start(1000) 

        self.save_timer = QTimer(self)
        self.save_timer.timeout.connect(self.tracker_thread.save)
        self.save_timer.start(1000 * 60) # Save every 1m


    def update_apm(self, apm):
        # TODO: Change text color based on apm
        self.label.setText(f"APM\n{apm}")


    def populate_list(self, data: dict):
        self.key_stats.clear()
        for key, taps in data.items():
            self.key_stats.addItem(f"{key}: {taps}")


if __name__ == "__main__":    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    app.exec()