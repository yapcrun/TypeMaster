import os
import time
import threading
import subprocess
from random import choice
from pynput import keyboard
if os.name == 'nt': import winsound


# TODO: Display key press stats (in a GUI?)
# TODO: Make the exit hotkey more complex
# TODO: Make the sounds loaded into memory to minimize disk reads
# TODO: Fix windows audio so sounds can play in parallel


print(f"{'-'*10}Typemaster v0.1.0{'-'*10}")

SOUNDS = "default"
DEBUG = False
DO_PRINT = False
DO_LOGGING = True
EXIT_KEY = "q"
PAUSE_KEY = "l"
if not DO_LOGGING: print("Logging disabled!!")

# TODO: Test best backend for psytray on linux
# os.environ["PYSTRAY_BACKEND"] = # appindicator gtk xorg

os.chdir(os.path.dirname(os.path.abspath(__file__)))
cwd = os.getcwd()
print(cwd)
os_type = os.name
print(os_type)


class Sound:
    def __init__(self, sounds = SOUNDS):
        self.sounds = sounds
        self.tap_sounds = []
        self.special_sounds = []
        self.arrow_sounds = []
        self.enter_sounds = []
        self.backspace_sounds = []
        self.space_sounds = []
        self.play = True
        self.sound_dir = cwd + "/sounds/" + self.sounds

        for file in os.listdir(self.sound_dir + "/tap"):
            if file.endswith(".wav"):
                self.tap_sounds.append(self.sound_dir + "/tap/" + file)
        for file in os.listdir(self.sound_dir + "/special"):
            if file.endswith(".wav"):
                self.special_sounds.append(self.sound_dir + "/special/" + file)
        for file in os.listdir(self.sound_dir + "/enter"):
            if file.endswith(".wav"):
                self.enter_sounds.append(self.sound_dir + "/enter/" + file)
        for file in os.listdir(self.sound_dir + "/arrow"):
            if file.endswith(".wav"):
                self.arrow_sounds.append(self.sound_dir + "/arrow/" + file)
        for file in os.listdir(self.sound_dir + "/backspace"):
            if file.endswith(".wav"):
                self.backspace_sounds.append(self.sound_dir + "/backspace/" + file)
        for file in os.listdir(self.sound_dir + "/space"):
            if file.endswith(".wav"):
                self.space_sounds.append(self.sound_dir + "/space/" + file)

        if DEBUG:
            print(f"tap sounds: {self.tap_sounds}")
            print(f"special sounds: {self.special_sounds}")
            print(f"arrow sounds: {self.arrow_sounds}")
            print(f"enter sounds: {self.enter_sounds}")
            print(f"backspace sounds: {self.backspace_sounds}")


    def play_sound(self, key_type = "generic"):
        if not self.play:
            return
        if key_type == "special":
            sound = choice(self.special_sounds)
        elif key_type == "arrow":
            sound = choice(self.arrow_sounds)
        elif key_type == "enter":
            sound = choice(self.enter_sounds)
        elif key_type == "backspace":
            sound = choice(self.backspace_sounds)
        elif key_type == "space":
            sound = choice(self.space_sounds)
        else:
            sound = choice(self.tap_sounds)
        
        if os.name == 'nt':  # Windows
            winsound.PlaySound(sound, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        else:  # Linux or other OS
            subprocess.run("aplay -q " + sound, cwd=cwd, shell=True)

    def ps(self, key_type = "generic"):
        if key_type == "special":
            threading.Thread(target=self.play_sound, args=["special"]).start()
        elif key_type == "arrow":
            threading.Thread(target=self.play_sound, args=["arrow"]).start()
        elif key_type == "enter":
            threading.Thread(target=self.play_sound, args=["enter"]).start()
        elif key_type == "backspace":
            threading.Thread(target=self.play_sound, args=["backspace"]).start()
        elif key_type == "space":
            threading.Thread(target=self.play_sound, args=["space"]).start()
        else:
            threading.Thread(target=self.play_sound).start()

    def toggle_sound(self):
        self.play = not self.play


class InputTracker:
    def __init__(self):
        self.sound = Sound()
        self.key_dict = {}
        self.load_keys()
        self.last_save_time = time.time()
        self.mod_key_pressed = False

    def toggle_sound(self):
        self.sound.toggle_sound()
        
    def on_press(self, key):
        if DEBUG: print(key.__dict__)
        try:
            if hasattr(key, 'char') and key.char is not None: # if is a character key

                # Hotkey to toggle sound
                if self.mod_key_pressed and key.char == PAUSE_KEY:
                    self.sound.play = not self.sound.play
                    if self.sound.play:
                        print("Sound enabled")
                    else:
                        print("Sound disabled")
                    return
                elif self.mod_key_pressed and key.char == EXIT_KEY:
                    self.save_keys()
                    os._exit(0)

                if DO_LOGGING: self.key_dict[key.char] = self.key_dict.get(key.char, 0) + 1
                if DO_PRINT: print(f'Key pressed: {key.char}')

                self.sound.ps()
                
            elif hasattr(key, 'name') and key.name is not None: # if is a special key\
                # Handle modifier toggle
                if key == keyboard.Key.ctrl:
                    self.mod_key_pressed = True
                
                if key.name in ["up", "down", "left", "right"]:
                    self.sound.ps(key_type="arrow")
                elif key.name == "space":
                    self.sound.ps(key_type="space")
                elif key.name == "enter":
                    self.sound.ps(key_type="enter")
                elif key.name == "backspace":
                    self.sound.ps(key_type="backspace")
                else:
                    self.sound.ps(key_type="special")
                
                if DO_LOGGING: self.key_dict[str(key.name)] = self.key_dict.get(str(key.name), 0) + 1
                if DO_PRINT: print(f'Special key pressed: {key.name}')

        except Exception as e:
            print(f"Error in on_press: {e}")

        if time.time() - self.last_save_time > 60:
            if DO_LOGGING: self.save_keys()
            self.last_save_time = time.time()

    def on_release(self, key):
        if DEBUG: print(f"Release:{key}")
        try:
            if key == keyboard.Key.ctrl:
                self.mod_key_pressed = False
        except Exception as e:
            print(f"Error in on_release: {e}")

    def save_keys(self):
        try:
            with open('key_log.txt', 'w') as f:
                for key, count in self.key_dict.items():
                    f.write(f'{key}: {count}\n')
            print("Keys saved to key_log.txt")
        except Exception as e:
            print(f"Error saving keys: {e}")

    def load_keys(self):
        try:
            if os.path.exists('key_log.txt'):
                with open('key_log.txt', 'r') as f:
                    for line in f:
                        key, count = line.strip().split(': ')
                        self.key_dict[key] = int(count)
                print("Keys loaded from key_log.txt")
            else:
                print("No previous key log found.")
        except Exception as e:
            print(f"Error loading keys: {e}")




input_tracker = InputTracker()

# TODO: Fix AssertionError (I think this happens when the display is disabled(only on linux?))
try:
    import pystray
    from PIL import Image
    
    def after_click(icon, item):
        print(f"Clicked on {item}")
        if str(item) == "Toggle Audio":
            input_tracker.toggle_sound()
            print("Audio Toggled")
        elif str(item) == "Exit":
            icon.stop()
            os._exit(0)

    image = Image.open("COMP_ICON.png")
    icon = pystray.Icon("TypeMaster", image, "TypeMaster", menu=pystray.Menu(
        pystray.MenuItem("Toggle Audio", after_click),
        pystray.MenuItem("Exit", after_click)
    ))

    threading.Thread(target=icon.run).start()

except ImportError:
    print("pystray or pillow not found, tray icon support disabled.")
except AssertionError:
        print("AssertionError: Tray icon support disabled.")


with keyboard.Listener(
        on_press=input_tracker.on_press,
        on_release=input_tracker.on_release
) as listener:
    try:
        listener.join()
    except KeyboardInterrupt:
        print("Listener stopped.")
        os._exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")

