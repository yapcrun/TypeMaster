from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QComboBox, QApplication, QWidget, QPushButton, QMainWindow, QLabel, QVBoxLayout, QLineEdit, QHBoxLayout, QListWidget, QCheckBox
from PyQt6.QtGui import QIcon
import sys
from pynput import keyboard
from random import choice
import os
import tracker2

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# TODO: Test on Windows
# TODO: Implement the tray functionality w/ qt6 (or old method)
# TODO: Implement hotkey functionality. 
# TODO: Make the list fancy
# TODO: Add another default sound pack
# TODO: Update README
# TODO: Add a WPM counter
# TODO: Comment and add definitions to functions/methods
# TODO: research graph support (https://www.pyqtgraph.org/)
# TODO: Rename file extention to pyw
# TODO: Make the selected sound pack persistant
# TODO: get argv and handle a --no-gui flag
# TODO: Don't save emojis in the stats list (breaks windows saving) | Maybe use a library like emoji to convert them

class TrackerThread(QThread):
    apm_signal = pyqtSignal(int)
    stats_list_signal = pyqtSignal(dict)
    last_key_signal = pyqtSignal(str)

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
        last_key = data["last_key"]
        self.apm_signal.emit(apm)
        self.stats_list_signal.emit(stats)
        self.last_key_signal.emit(last_key)
        self.need_update = True

    def update_apm(self):
        apm = self.tracker.update_apm(False)
        self.apm_signal.emit(apm)

    def save(self):
        if self.need_update == False: return
        self.tracker.logfile("save")
        self.need_update = False

    def change_sounds(self, pack: str):
        self.tracker.sounds.load_sounds(pack)

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
        # Main window setup
        self.setWindowTitle("TypeMaster")
        self.setGeometry(100, 100, 300, 700)
        self.setWindowIcon(QIcon("COMP_ICON.png"))
        # Tracker Thread Setup
        self.tracker_thread = TrackerThread()
        self.tracker_thread.apm_signal.connect(self.update_apm)
        self.tracker_thread.stats_list_signal.connect(self.populate_list)
        self.tracker_thread.last_key_signal.connect(self.update_hist_label)
        self.tracker_thread.start()
        # Main Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # Main Layout
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        # APM Header Label
        self.apm_h_label = QLabel("APM")
        self.apm_h_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apm_h_label.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.apm_h_label)
        # APM Label
        self.apm_label = QLabel("0")
        self.apm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apm_label.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.apm_label)
        # Key Stats
        self.key_stats = QListWidget()
        self.layout.addWidget(self.key_stats)
        # HORIZONTAL LAYOUT
        self.controls_layout = QHBoxLayout()
        # Sound Pack Selector
        self.sound_pack_combo = QComboBox()
        sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
        items = [name for name in os.listdir(sounds_dir) if os.path.isdir(os.path.join(sounds_dir, name))]
        print(items)
        self.sound_pack_combo.addItems(items)
        self.sound_pack_combo.currentTextChanged.connect(self.on_sound_pack_changed)
        self.controls_layout.addWidget(self.sound_pack_combo, 1)
        # AOT Toggle
        self.aot_toggle = QCheckBox(text="On Top")
        self.aot_toggle.stateChanged.connect(self.toggle_always_on_top)
        self.controls_layout.addWidget(self.aot_toggle, 0)
        # Mute Toggle
        self.mute_toggle = QCheckBox(text="mute")
        self.mute_toggle.stateChanged.connect(self.toggle_mute)
        self.controls_layout.addWidget(self.mute_toggle, 0)
        # Add Horizontal controls layout
        self.layout.addLayout(self.controls_layout)
        # Hist Label
        self.hist_label = QLabel()
        self.hist_label.setText("************"*3)
        self.hist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.hist_label)

        # --- QTimer setup ---
        self.apm_timer = QTimer(self)
        self.apm_timer.timeout.connect(self.tracker_thread.update_apm)
        self.apm_timer.start(1000) 

        self.save_timer = QTimer(self)
        self.save_timer.timeout.connect(self.tracker_thread.save)
        self.save_timer.start(1000 * 60) # Save every 1m

    def on_sound_pack_changed(self, text):
        print(f"Selected sound pack: {text}")
        self.tracker_thread.change_sounds(text)
                
    def update_apm(self, apm):
        self.apm_label.setText(f"{apm}")
        # Set text color & size based on apm
        if apm in range(0,89):
            self.apm_label.setStyleSheet("color: green; font-size: 24px;")
        elif apm in range(90, 174):
            self.apm_label.setStyleSheet("color: yellow; font-size: 30px;")
        elif apm > 175:
            self.apm_label.setStyleSheet("color: red; font-size: 34px;")

    def populate_list(self, data: dict):
        self.key_stats.clear()
        for key, taps in data.items():
            self.key_stats.addItem(f"{key}: {taps}")

    def toggle_mute(self):
        self.tracker_thread.tracker.sounds.toggle_sound()

    def toggle_always_on_top(self):
        flags = self.windowFlags()
        if flags & Qt.WindowType.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def update_hist_label(self, text):
        if len(text) > 1: return
        txt = self.hist_label.text()[1:]
        self.hist_label.setText(txt + text)
        color = choice(["red", "blue", "green", "yellow"])
        self.hist_label.setStyleSheet(f"color: {color}")


if __name__ == "__main__":    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    app.exec()