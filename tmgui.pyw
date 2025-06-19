from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QComboBox, QApplication, QWidget, QPushButton, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QListWidget, QCheckBox, QListWidgetItem
from PyQt6.QtGui import QIcon, QFontDatabase, QFont, QColor
import sys
from pynput import keyboard
from random import randint
import os
import tracker2
from load_dict import load_dict, save_dict


os.chdir(os.path.dirname(os.path.abspath(__file__)))

# TODO: Make these CONSTs load from a config file
DO_EMOJI = False # Enable emoji output
START_ON_TOP = False 

# TODO: Add a WPM counter?
# TODO: research graph support (https://www.pyqtgraph.org/)
# TODO: Add a settings/info window


class TrayThread(QThread):
    '''
    QThread object that creats a pystray menu to interface with the main gui window
    '''
    toggle_audio_signal = pyqtSignal()
    show_window_signal = pyqtSignal()
    exit_signal = pyqtSignal()
    def __init__(self):
        '''
        Initialize the TrayThread, setting up the system tray icon and menu.
        '''
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
        '''
        Handle clicks on the tray icon menu items.

        Args:
            _icon: The tray icon instance.
            item: The clicked menu item.
        '''
        item = str(item)  # Convert item to string for comparison
        if item == "Toggle Audio":
            print("Audio Toggled")
            self.toggle_audio_signal.emit()
        elif item == "Exit":
            self.exit_signal.emit()
        elif item == "Show GUI":
            self.show_window_signal.emit()

    def run(self):
        '''
        Start the tray icon event loop if initialization was successful.
        '''
        if self.success: # if pystray loaded successfully
            self.icon.run()

class TrackerThread(QThread):
    '''
    QThread object that runs the keyboard event listener, plays audio and returns data relevent to the gui
    '''
    apm_signal = pyqtSignal(int)
    stats_list_signal = pyqtSignal(dict, str)
    last_key_signal = pyqtSignal(str)
    combo_signal = pyqtSignal(int)
    hi_score_signal = pyqtSignal(dict)
    def __init__(self):
        '''
        Initialize the TrackerThread, loading configuration and setting up the key tracker.
        '''
        super().__init__()
        self.running = True
        self.tracker = tracker2.KeyHandler()
        self.need_update = False # Is there new data to save?
        self.config = load_dict(".config")
        self.key_press_history = [""]*3
        if self.config == None: self.config = {"soundpack": "default"} # If there is no config file reset it
        self.pack = self.config["soundpack"] # Get the name of the last used pack
        # TODO: Handle the case where the DEFAULT sound pack is missing
        if self.pack in os.listdir("sounds"): # If the pack exists
            self.change_sounds(self.pack) # Change sound pack to last used
        else:
            self.pack = "default"  # Else reset the sound pack back to default
            self.config["soundpack"] = "default"
            save_dict(self.config, ".config")

    def on_press(self, key):
        '''
        Handle a key press event, update statistics, and emit relevant signals.

        Args:
            key: The key event object.
        '''
        if key == None or hasattr(key, "char") and key.char == None: return # couldn't identify the key pressed, do nothing
        data = self.tracker.on_press(key)
        if data == None: return # Key was heald down, we don't want to track it, so do nothing

        apm = data["apm"]
        stats = data["stats"]
        last_key = data["last_key"]
        combo = data["combo"]
        hi_score = data["hiscore"]
        self.apm_signal.emit(apm)
        self.stats_list_signal.emit(stats, last_key)
        self.last_key_signal.emit(last_key)
        self.combo_signal.emit(combo)
        self.hi_score_signal.emit((hi_score))
        self.need_update = True
        self.press_history(last_key)

    def update_apm(self):
        '''
        Update and emit the current actions per minute (APM).
        '''
        apm = self.tracker.update_apm(False)
        self.apm_signal.emit(apm)

    def save(self):
        '''
        Save the current tracker statistics if there are updates.
        '''
        if self.need_update == False: return
        self.tracker.save()
        self.need_update = False

    def change_sounds(self, pack: str):
        '''
        Change the current sound pack and update configuration.

        Args:
            pack (str): The name of the sound pack to load.
        '''
        self.tracker.sounds.load_sounds(pack)
        self.config["soundpack"] = pack
        save_dict(self.config, ".config")

    def press_history(self, key):
        '''
        Update the key_press_history with recent key

        Args:
            key (str): Name of the key to add to the list
        '''
        self.key_press_history.append(key)
        self.key_press_history.pop(0)

    def run(self):
        '''
        Start the keyboard listener and process key events in a loop.
        '''
        self.stats_list_signal.emit(self.tracker.get_key_stats(), "None")
        self.hi_score_signal.emit(self.tracker.hiscore)
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
        '''
        Stop the tracker thread.
        '''
        self.running = False


class MainWindow(QMainWindow):
    '''
    TypeMaster main gui window.
    '''
    def __init__(self):
        '''
        Initialize the main window, set up the UI, and start background threads.
        '''
        super().__init__()
        font_id = QFontDatabase.addApplicationFont("bin/font.ttf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            self.custom_font = QFont(font_family)
        else:
            print("Failed to load font.ttf")
            self.custom_font = self.font()  # Load the default PyQt font

        self.last_chars = ['*']*16 # List for hist_label 
        # Main window setup
        self.setWindowTitle("TypeMaster")
        self.setGeometry(100, 100, 300, 700)
        self.setWindowIcon(QIcon("COMP_ICON.png"))
        if START_ON_TOP:
            self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

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
        self.tray_thread.exit_signal.connect(self.exit)
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
        self.hi_score_label = QLabel("Hi-Scores\nAPM: []\nCOMBO: []")
        self.hi_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hi_score_label.setFont(self.custom_font)
        # Left (APM) vertical layout
        apm_vbox = QVBoxLayout()
        self.apm_h_label = QLabel("APM")
        self.apm_h_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.apm_h_label.setStyleSheet("font-size: 24px;")
        self.apm_h_label.setFont(self.custom_font)
        apm_vbox.addWidget(self.apm_h_label)
        self.apm_label = QLabel("0")
        self.apm_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.apm_label.setStyleSheet("font-size: 24px;")
        self.apm_label.setFont(self.custom_font)
        apm_vbox.addWidget(self.apm_label)
        # Right (Combo) vertical layout
        combo_vbox = QVBoxLayout()
        self.apm_combo_h_label = QLabel("combo")
        self.apm_combo_h_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.apm_combo_h_label.setStyleSheet("font-size: 17px;")
        self.apm_combo_h_label.setFont(self.custom_font)
        combo_vbox.addWidget(self.apm_combo_h_label)
        self.apm_combo_label = QLabel("0")
        self.apm_combo_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.apm_combo_label.setStyleSheet("font-size: 17px;")
        self.apm_combo_label.setFont(self.custom_font)
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
        if START_ON_TOP:
            self.aot_toggle.setChecked(True)
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
        self.hist_label.setFont(self.custom_font)
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
        '''
        Handle changes to the selected sound pack.

        Args:
            text (str): The name of the selected sound pack.
        '''
        print(f"Selected sound pack: {text}")
        self.tracker_thread.change_sounds(text)

    def update_apm(self, apm):
        '''
        Update the displayed actions per minute (APM) value and color.

        Args:
            apm (int): The current APM value.
        '''
        self.apm_label.setText(f"{apm}")
        if apm < 255: # if apm not past the max red value
            color = f"rgb({apm}, {255-apm}, 0)" # (apm reduces green and increases red up to 255)
        else:
            color = "rgb(255, 0, 0)"
        self.apm_label.setStyleSheet(f"color: {color}; font-size: 24px;")

    def update_combo(self, combo):
        '''
        Update the displayed combo value.

        Args:
            combo (int): The current combo count.
        '''
        self.apm_combo_label.setText(f"{combo}")

    def update_hi_score(self, combo):
        '''
        Update the displayed high score values.

        Args:
            combo (dict): Dictionary containing 'apm' and 'combo' high scores.
        '''
        self.hi_score_label.setText(f"Hi-Scores\nAPM: [{combo['apm']}]\nCOMBO: [{combo['combo']}]")

    def populate_list(self, data: dict, last_key: str):
        '''
        Populate the key statistics list widget with updated data.

        Args:
            data (dict): Dictionary of key statistics.
        '''
        self.key_stats.clear()
        keys_to_color = self.tracker_thread.key_press_history
        for key, taps in data.items():
            if key in keys_to_color:
                color = keys_to_color.index(key)
                if color == 0: # least recent
                    color = QColor("red")
                elif color == 1:
                    color = QColor("yellow")
                elif color == 2: # most recent
                    color = QColor("green")
                item = QListWidgetItem(f"{convert_keys(key)}: {taps}")
                item.setBackground(color)
                self.key_stats.addItem(item)
            else:
                self.key_stats.addItem(f"{convert_keys(key)}: {taps}")

    def toggle_mute(self):
        '''
        Toggle the mute state for key sounds and update the mute checkbox.
        '''
        self.tracker_thread.tracker.sounds.toggle_sound() 
        is_muted = not self.tracker_thread.tracker.sounds.play  # Get the current mute state
        self.mute_toggle.blockSignals(True)  # Block signals to prevent recursion
        self.mute_toggle.setChecked(is_muted)  # Update the checkbox state
        self.mute_toggle.blockSignals(False)  # Re-enable signals

    def toggle_always_on_top(self):
        '''
        Toggle the "always on top" window flag for the main window.
        '''
        flags = self.windowFlags()
        if flags & Qt.WindowType.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def update_hist_label(self, text):
        '''
        Update the history label with the latest key presses.

        Args:
            text (str): The latest key pressed.
        '''
        self.last_chars.append(text)
        self.last_chars.pop(0)
        set_text = ""
        for i in self.last_chars:
            set_text = set_text+convert_keys(i)
        self.hist_label.setText(set_text)

        color = f"#{hex(randint(16,255))[2:]}{hex(randint(16,255))[2:]}{hex(randint(16,255))[2:]}"
        self.hist_label.setStyleSheet(f"color: {color}")

    def exit(self):
        '''
        Save statistics and exit the application.
        '''
        self.tracker_thread.save()
        self.tray_thread.icon.stop()
        QApplication.quit()
        # os._exit(0)

    def closeEvent(self, event):
        '''
        Handle the window close event, hiding or exiting as appropriate.

        Args:
            event: The close event object.
        '''
        if self.tray_thread.success: # maybe check if the thread is running instead?
            event.ignore()
            self.hide()
        else: # if tray was not loaded exit instead of hiding.
            self.tracker_thread.save()
            QApplication.quit()
            # os._exit(0)


def convert_keys(key):
    '''
    Function to convert keys to an emoji representation to coolness.

    Args:
        key (str): The key name to convert.

    Returns:
        str: The emoji or string representation of the key.
    '''
    if DO_EMOJI:
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
        elif key == "1": return "1️⃣"
        elif key == "2": return "2️⃣"
        elif key == "3": return "3️⃣"
        elif key == "4": return "4️⃣"
        elif key == "5": return "5️⃣"
        elif key == "6": return "6️⃣"
        elif key == "7": return "7️⃣"
        elif key == "8": return "8️⃣"
        elif key == "9": return "9️⃣"
        elif key == "0": return "0️⃣"
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