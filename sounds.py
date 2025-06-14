
# Loaded from tracker2
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import mixer
from random import choice


DEBUG = False
SOUNDS = "default"
cwd = os.getcwd()
if DEBUG: print(f"sounds.py cwd: {cwd}")

class Sound:
    def __init__(self):
        self.mixer = mixer.init()
        mixer.set_num_channels(28)
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
        # Tap Sounds
        for file in os.listdir(self.sound_dir + "/tap"):
            if file.endswith(".wav"):
                sound = self.sound_dir + "/tap/" + file
                sound = mixer.Sound(sound)
                self.tap_sounds.append(sound)
        for file in os.listdir(self.sound_dir + "/special"):
            if file.endswith(".wav"):
                sound = self.sound_dir + "/special/" + file
                sound = mixer.Sound(sound)
                self.special_sounds.append(sound)
        for file in os.listdir(self.sound_dir + "/enter"):
            if file.endswith(".wav"):
                sound = self.sound_dir + "/enter/" + file
                sound = mixer.Sound(sound)
                self.enter_sounds.append(sound)
        for file in os.listdir(self.sound_dir + "/arrow"):
            if file.endswith(".wav"):
                sound = self.sound_dir + "/arrow/" + file
                sound = mixer.Sound(sound)
                self.arrow_sounds.append(sound)
        for file in os.listdir(self.sound_dir + "/backspace"):
            if file.endswith(".wav"):
                sound = self.sound_dir + "/backspace/" + file
                sound = mixer.Sound(sound)
                self.backspace_sounds.append(sound)
        for file in os.listdir(self.sound_dir + "/space"):
            if file.endswith(".wav"):
                sound = self.sound_dir + "/space/" + file
                sound = mixer.Sound(sound)
                self.space_sounds.append(sound)

        if DEBUG:
            print(f"tap sounds: {self.tap_sounds}")
            print(f"special sounds: {self.special_sounds}")
            print(f"arrow sounds: {self.arrow_sounds}")
            print(f"enter sounds: {self.enter_sounds}")
            print(f"backspace sounds: {self.backspace_sounds}")

    def ps(self, key_type = "generic"):
        if not self.play: return
        if key_type == "special":
            choice(self.special_sounds).play()
        elif key_type == "arrow":
            choice(self.arrow_sounds).play()
        elif key_type == "enter":
            choice(self.enter_sounds).play()
        elif key_type == "backspace":
            choice(self.backspace_sounds).play()
        elif key_type == "space":
            choice(self.space_sounds).play()
        else:
            choice(self.tap_sounds).play()

    def toggle_sound(self):
        self.play = not self.play
