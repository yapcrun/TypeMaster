import os
from random import choice
import threading
import subprocess
if os.name == 'nt': import winsound  # Only available on Windows


DEBUG = False
SOUNDS = "default"
cwd = os.getcwd()
if DEBUG: print(f"sounds.py cwd: {cwd}")

class Sound:
    # TODO: load sound into memory to minimize disk reads
    def __init__(self):
        self.tap_sounds = []
        self.special_sounds = []
        self.arrow_sounds = []
        self.enter_sounds = []
        self.backspace_sounds = []
        self.space_sounds = []
        self.play = True
        self.load_sounds("default")

    def load_sounds(self, sound_pack):
        self.sounds = sound_pack
        self.sound_dir = cwd + "/sounds/" + self.sounds
        # Empty sounds so we don't load multiple packs
        self.tap_sounds = []
        self.special_sounds = []
        self.arrow_sounds = []
        self.enter_sounds = []
        self.backspace_sounds = []
        self.space_sounds = []

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
            # TODO: Fix windows audio so sounds can play in parallel
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
