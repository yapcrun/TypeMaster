# Loaded from tmgui
import time
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sounds
from load_dict import load_dict, save_dict
# BUG: [WINDOWS] when pressing a modifier key and a normal key at the same time, the pressed character becomes a non-standard symbol character
# EG: pressing "shift + c" results in " ♥" 

COMBO_THRESHOLD = 3 # seconds

class KeyHandler:
    '''
    Class to handle key stats, apm
    '''
    def __init__(self):
        '''
        Initialize KeyHandler, loading key statistics and high scores, and setting up state.
        '''
        self.key_stats = load_dict("key_stats")
        if self.key_stats == None: self.key_stats = {}
        self.apm = 0
        self.apm_times = []
        self.sounds = sounds.Sound()
        self.last_press = ["*", 0]
        self.last_save = time.time()
        self.combo = 0
        self.hiscore = load_dict("hiscore")
        if self.hiscore == None: self.hiscore = {"apm": 0, "combo": 0}

    def on_press(self, key):
        '''
        Handle a key press event.

        Args:
            key: A pynput Key object representing the pressed key.

        Returns:
            dict: Data relevant to the GUI (APM, stats, last key, combo, hiscore), or None on error.
        '''
        actual_key = None
        combo = self.update_combo(self.last_press[1])
        try: 
            if hasattr(key, "char") and key.char is not None: # is a alpha numeric key
                actual_key = key.char.lower()
            elif hasattr(key, "name"): # is mod, arrow, etc.
                actual_key = key.name.lower()
            else:
                actual_key = "౸"
                print(f"Error identifying key\n{key.__dict__}")
        except Exception as e: 
            print("Failed to determine key type\n\t{e}")
        # Logic to prevent registering heald keys multiple times
        if actual_key == self.last_press[0] and time.time() - self.last_press[1] < 0.09: # If the key is the same as the last one and time since last press is < 90ms
            self.last_press = [actual_key, time.time()] # If the key is heald don't update data 
            return None 

        self.key_stats[actual_key] = self.key_stats.get(actual_key, 0) + 1 # Update stats
        self.update_apm()
        self.last_press = [actual_key, time.time()]
        self.update_hi_score()
        self.sound(actual_key)
        return {"apm": self.apm,
                "stats": sort_dict_by_value(self.key_stats),
                "last_key": actual_key,
                "combo": combo,
                "hiscore": self.hiscore}

    def get_key_stats(self):
        '''
        Get the current key statistics.

        Returns:
            dict: The key statistics dictionary.
        '''
        return self.key_stats
    
    def update_combo(self, last_press):
        '''
        Update and return the current combo count based on the time since the last key press.

        Args:
            last_press (float): Timestamp of the last key press.

        Returns:
            int: The updated combo count.
        '''
        if time.time() - last_press < 3.0:
            self.combo += 1
        else:
            self.combo = 0
        return self.combo

    def update_hi_score(self):
        '''
        Update the high score for APM and combo if the current values exceed the stored high scores.
        '''
        if self.hiscore["apm"] < self.apm:
            self.hiscore["apm"] = self.apm
        if self.hiscore["combo"] < self.combo:
            self.hiscore["combo"] = self.combo

    def update_apm(self, is_increasing = True):
        '''
        Calculate and update the actions per minute (APM).

        Args:
            is_increasing (bool): Whether to increment the APM counter (default: True).

        Returns:
            int: The current APM value.
        '''
        now = time.time()

        if is_increasing: self.apm_times.append(now) # add the current time to the list
        to_del = 0
        
        for i in self.apm_times: # loop thru apm_times to find & remove old entries
            if now - i > 60: # if item in list is older than 60s
                to_del += 1 # increment the ammount of outdated list items to be removed
            else: # Not outdated
                break 
        
        if to_del: # if there are items to delete
            for i in range(0,to_del): # Delete the items from the list
                self.apm_times.pop(0) # Delete the older values at the front

        self.apm = len(self.apm_times) # set the new apm value
        return self.apm

    def save(self):
        '''
        Save the current key statistics and high scores to persistent storage.
        '''
        # self.logfile("save")
        save_dict(sort_dict_by_value(self.key_stats), "key_stats")
        save_dict(self.hiscore, "hiscore")

    def sound(self, key_name):
        '''
        Play a sound corresponding to the given key name.

        Args:
            key_name (str): The name of the key pressed.
        '''
        if len(key_name) == 1:
            self.sounds.ps("generic")
        elif key_name in ['up', 'down', 'left', 'right']:
            self.sounds.ps("arrow")
        elif key_name in ["space"]:
            self.sounds.ps("space")
        elif key_name in ["backspace"]:
            self.sounds.ps("backspace")
        elif key_name in ["enter"]:
            self.sounds.ps("enter")
        else:
            self.sounds.ps("special")


def sort_dict_by_value(d):
    """
    Sort a dictionary by its integer values in descending order.

    Args:
        d (dict): The dictionary to sort.

    Returns:
        dict: A new dictionary sorted by value in descending order.
    """
    return dict(sorted(
        ((k, v) for k, v in d.items() if isinstance(v, int)),
        key=lambda item: item[1],
        reverse=True
    ))



if __name__ == "__main__":
    pass