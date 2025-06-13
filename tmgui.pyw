from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QComboBox, QApplication, QWidget, QPushButton, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QListWidget, QCheckBox
from PyQt6.QtGui import QIcon
import sys
from pynput import keyboard
from random import randint
import os
import tracker2
import config


# Set cwd to make sure paths are correct
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DO_EMOJI = False # Enable emoji output

# TODO: Test on Windows
# TODO: Figure out new sound emission method.
# BUG: Figure out why sounds stop then play all @ once on linux. (fix w/ above todo?)
# TODO: Implement hotkey functionality. 
# TODO: Make the list fancy
# TODO: Add a WPM counter
# TODO: Comment and add definitions to functions/methods
# TODO: research graph support (https://www.pyqtgraph.org/)
# TODO: get argv and handle a --no-gui flag
# TODO: Add a window to track hi scores of burst and apm and wpm
# TODO: Color combo
# TODO: Make file handling consistant [wip]
# TODO: Unify the signals down to one?

class TrayThread(QThread):
    '''
    QThread object that creats a pystray menu to interface with the main gui window
    '''
    # TODO: Make an exit signal and save stats on exit from main thread.
    toggle_audio_signal = pyqtSignal()
    show_window_signal = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.success = False
        try:
            import pystray
            from PIL import Image
            self.running = True
            image = Image.open("COMP_ICON.png")
            self.icon = pystray.Icon("TypeMaster", image, "TypeMaster", menu=pystray.Menu(
                pystray.MenuItem("Show GUI", self.after_click),
                pystray.MenuItem("Toggle Audio", self.after_click),
                pystray.MenuItem("Exit", self.after_click)
            ))
            self.success = True
        except ImportError:
            print("pystray or pillow not found, tray icon support disabled.")
        except AssertionError:
                print("AssertionError: Tray icon support disabled.")
        except Exception as e:
            print(f"Error starting tray icon: {e}\nTray icon support disabled.")
                # icon.stop()
                # os._exit(0)

    def after_click(self, _icon, item):
        item = str(item)  # Convert item to string for comparison
        if item == "Toggle Audio":
            print("Audio Toggled")
            self.toggle_audio_signal.emit()
        elif item == "Exit":
            os._exit(0)
        elif item == "Show GUI":
            self.show_window_signal.emit()

    def run(self):
        if self.success: # if pystray loaded successfully
            self.icon.run()

class TrackerThread(QThread):
    '''
    QThread object that runs the keyboard event listener, plays audio and returns data relevent to the gui
    '''
    apm_signal = pyqtSignal(int)
    stats_list_signal = pyqtSignal(dict)
    last_key_signal = pyqtSignal(str)
    combo_signal = pyqtSignal(int)
    hi_score_signal = pyqtSignal(dict)
    def __init__(self):
        super().__init__()
        self.running = True
        self.tracker = tracker2.KeyHandler()
        self.need_update = False # Is there new data to save?

        # TODO: Handle the case where the default sound pack is missing
        self.pack = config.load_config() # Get the name of the last used pack
        if self.pack in os.listdir("sounds"): # If the pack exists
            self.change_sounds(self.pack) # Change sound pack to last used
        else:
            self.pack = config.load_config(reset=True) # Else reset the sound pack back to default

    def on_press(self, key):
        if hasattr(key, "char") and key.char == None: return # couldn't identify the key pressed, do nothing
        data = self.tracker.on_press(key)

        apm = data["apm"]
        stats = data["stats"]
        last_key = data["last_key"]
        combo = data["combo"]
        hi_score = data["hiscore"]
        self.apm_signal.emit(apm)
        self.stats_list_signal.emit(stats)
        self.last_key_signal.emit(last_key)
        self.combo_signal.emit(combo)
        self.hi_score_signal.emit((hi_score))
        self.need_update = True

    def update_apm(self):
        apm = self.tracker.update_apm(False)
        self.apm_signal.emit(apm)

    def save(self):
        if self.need_update == False: return
        self.tracker.save()
        self.need_update = False

    def change_sounds(self, pack: str):
        self.tracker.sounds.load_sounds(pack)
        config.save_config(pack)

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
    '''
    TypeMaster main gui window.
    '''
    def __init__(self):
        super().__init__()
        self.last_chars = ['*']*16 # List for hist_label 
        # Main window setup
        self.setWindowTitle("TypeMaster")
        self.setGeometry(100, 100, 300, 700)
        self.setWindowIcon(QIcon("COMP_ICON.png"))

        # Tracker Thread Setup
        self.tracker_thread = TrackerThread()
        self.tracker_thread.apm_signal.connect(self.update_apm)
        self.tracker_thread.stats_list_signal.connect(self.populate_list)
        self.tracker_thread.last_key_signal.connect(self.update_hist_label)
        self.tracker_thread.combo_signal.connect(self.update_combo)
        self.tracker_thread.hi_score_signal.connect(self.update_hi_score)
        self.tracker_thread.start()
        # Tray Thread Setup
        self.tray_thread = TrayThread()
        self.tray_thread.toggle_audio_signal.connect(self.toggle_mute)
        self.tray_thread.show_window_signal.connect(self.show)
        self.tray_thread.start()

        # Main Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # Main Layout
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        # --- APM/Combo Layout ---
        apm_hiscore_combo_hbox = QHBoxLayout()
        # Hi Scores Label
        self.hi_score_label = QLabel("Hi-Scores\nAPM: []\nWPM: []\ncombo: []")
        self.hi_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Left (APM) vertical layout
        apm_vbox = QVBoxLayout()
        self.apm_h_label = QLabel("APM")
        self.apm_h_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.apm_h_label.setStyleSheet("font-size: 24px;")
        apm_vbox.addWidget(self.apm_h_label)
        self.apm_label = QLabel("0")
        self.apm_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.apm_label.setStyleSheet("font-size: 24px;")
        apm_vbox.addWidget(self.apm_label)
        # Right (Combo) vertical layout
        combo_vbox = QVBoxLayout()
        self.apm_combo_h_label = QLabel("combo")
        self.apm_combo_h_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.apm_combo_h_label.setStyleSheet("font-size: 17px;")
        combo_vbox.addWidget(self.apm_combo_h_label)
        self.apm_combo_label = QLabel("0")
        self.apm_combo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.apm_combo_label.setStyleSheet("font-size: 17px;")
        combo_vbox.addWidget(self.apm_combo_label)
        # Add both vboxes to the hbox
        apm_hiscore_combo_hbox.addLayout(apm_vbox, 1)
        apm_hiscore_combo_hbox.addWidget(self.hi_score_label)
        apm_hiscore_combo_hbox.addLayout(combo_vbox, 1)
        # Add the hbox to the main layout
        self.layout.addLayout(apm_hiscore_combo_hbox)
        # Key Stats
        self.key_stats = QListWidget()
        self.layout.addWidget(self.key_stats)
        # HORIZONTAL LAYOUT
        self.controls_layout = QHBoxLayout()
        # Sound Pack Selector
        self.sound_pack_combo = QComboBox()
        sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
        items = [name for name in os.listdir(sounds_dir) if os.path.isdir(os.path.join(sounds_dir, name))]
        self.sound_pack_combo.addItems(items)
        self.sound_pack_combo.setCurrentIndex(items.index(self.tracker_thread.pack))
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
        # TODO: figure out a better way to align this element so text doesn't overflow and stretch the window
        self.hist_label.setMaximumWidth(250)
        self.layout.addWidget(self.hist_label)
        # --- APM QTimer setup ---
        self.apm_timer = QTimer(self)
        self.apm_timer.timeout.connect(self.tracker_thread.update_apm)
        self.apm_timer.start(1000) 
        # --- Save QTimer setup ---
        self.save_timer = QTimer(self)
        self.save_timer.timeout.connect(self.tracker_thread.save)
        self.save_timer.start(1000 * 60) # Save every 1m

    def on_sound_pack_changed(self, text):
        print(f"Selected sound pack: {text}")
        self.tracker_thread.change_sounds(text)

    def update_apm(self, apm):
        self.apm_label.setText(f"{apm}")
        # Set text color & size based on apm
        # TODO: Make this change linearly from rgb(0,255,0) to rgb(255,0,0) so max apm is 255
        if apm in range(0,89):
            self.apm_label.setStyleSheet("color: green; font-size: 24px;")
        elif apm in range(90, 174):
            self.apm_label.setStyleSheet("color: yellow; font-size: 30px;")
        elif apm > 175:
            self.apm_label.setStyleSheet("color: red; font-size: 34px;")

    def update_combo(self, combo):
        self.apm_combo_label.setText(f"{combo}")

    def update_hi_score(self, combo):
        self.hi_score_label.setText(f"Hi-Scores\nAPM: [{combo['apm']}]\nCOMBO: [{combo['combo']}]")

    def populate_list(self, data: dict):
        self.key_stats.clear()
        for key, taps in data.items():
            self.key_stats.addItem(f"{convert_keys(key)}: {taps}")

    def toggle_mute(self):
        # BUG: RecursionError when toggled from the tray (not effecting functionality)
        print("Toggling sound")
        self.tracker_thread.tracker.sounds.toggle_sound()
        is_muted = not self.tracker_thread.tracker.sounds.play # Get the current mute state
        self.mute_toggle.setChecked(is_muted) # Update the checkbox state

    def toggle_always_on_top(self):
        flags = self.windowFlags()
        if flags & Qt.WindowType.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def update_hist_label(self, text):
        self.last_chars.append(text)
        self.last_chars.pop(0)
        set_text = ""
        for i in self.last_chars:
            set_text = set_text+convert_keys(i)
        self.hist_label.setText(set_text)

        color = f"#{hex(randint(16,255))[2:]}{hex(randint(16,255))[2:]}{hex(randint(16,255))[2:]}"
        self.hist_label.setStyleSheet(f"color: {color}")

    def closeEvent(self, event):
        if self.tray_thread.success: # maybe check if the thread is running instead?
            event.ignore()
            self.hide()
        else: # if tray was not loaded exit instead of hiding.
            os._exit(0)


def convert_keys(key):
    '''
    Function to convert keys to an emoji representation to coolness
    '''
    if DO_EMOJI:
        # TODO: Add the numeric keys (0-9)
        if key == "backspace": return "🗑️"
        elif key == "delete": return "🕳️"
        elif key == "enter": return "↩️"
        elif key == "up": return "⬆️"
        elif key == "down": return "⬇️"
        elif key == "left": return "⬅️"
        elif key == "right": return "➡️"
        elif key == "media_volume_down": return "🔉"
        elif key == "media_volume_up": return "🔊"
        elif key == "media_play_pause": return "⏯️"
        elif key == "media_next": return "⏭️"
        elif key == "media_previous": return "⏮️"
        elif key == "caps_lock": return "🔒"
        elif key == "space": return "☄️"
        # elif key == "shift": return 
        # elif key == "shift_r": return
        # elif key == "ctrl": return
        # elif key == "ctrl_r": return
        elif key == "cmd": return "🪟"
        else: return key
    else: return key


if __name__ == "__main__":    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    app.exec()