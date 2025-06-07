# from pynput import keyboard
import time
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import sounds

# BUG: [WINDOWS] when pressing a modifier key and a normal key at the same time, the pressed character becomes a non-standard symbol character
# EG: pressing "shift + c" results in " ♥" 

class KeyHandler:
    '''
    Class to handle key stats, apm
    '''
    def __init__(self):
        self.key_stats = {}
        self.logfile("load")
        self.apm = 0
        self.apm_times = []
        self.sounds = sounds.Sound()
        self.last_press = ["*", 0]
        self.last_save = time.time()

    def on_press(self, key):
        # BUG: pynput doesn't like the media_stop key (does not crash the program)
        # determine key type
        try: 
            if hasattr(key, "char") and key.char is not None: # is a alpha numeric key
                actual_key = key.char.lower()
            elif hasattr(key, "name"): # is mod, arrow, etc.
                actual_key = key.name.lower()
        except Exception as e:
            print("Failed to determine key type\n\t{e}")

        # actual_key = convert_keys(actual_key) # Convert relevent keys to emoji form

        # Logic to prevent registering heald keys multiple times
        if actual_key == self.last_press[0] and time.time() - self.last_press[1] < 0.09:
            self.last_press = [actual_key, time.time()]
            return {"apm": self.apm,
                    "stats": self.key_stats,
                    "last_key": actual_key}

        if actual_key == ":": actual_key = "semicolon" # To prevent parsing issues 

        self.key_stats[actual_key] = self.key_stats.get(actual_key, 0) + 1 # Update stats
        self.update_apm()
        self.last_press = [actual_key, time.time()]
        self.sound(actual_key)
        print(f"Tracker: Pressed {actual_key}")
        return {"apm": self.apm,
                "stats": sort_dict_by_value(self.key_stats),
                "last_key": actual_key}

    def get_apm(self):
        return self.apm

    def get_key_stats(self):
        return self.key_stats

    def update_apm(self, is_increasing = True):
        '''
        Method for calculating APM
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

    def logfile(self, mode="load"):
        '''
        Method for saving/loading the key_stats from a txt file
        '''
        if mode == "load": # Load the key stats
            try:
                if os.path.exists('key_log.txt'):
                    with open('key_log.txt', 'r') as f:
                        for line in f:
                            key, count = line.strip().split(': ')
                            self.key_stats[key] = int(count)
                    print("Keys loaded from key_log.txt")
                else:
                    print("No previous key log found.")
            except Exception as e:
                print(f"Error loading keys: {e}")
        elif mode == "save": # Save the key stats
            try:
                with open('key_log.txt', 'w') as f:
                    for key, count in sort_dict_by_value(self.key_stats).items():
                        f.write(f'{key}: {count}\n')
                print("Keys saved to key_log.txt")
            except Exception as e:
                print(f"Error saving keys: {e}")

    def sound(self, key_name):
        '''
        
        '''
        # TODO: Find a better way to make this logic better
        if len(key_name) == 1:
            self.sounds.ps("generic")
        elif key_name in ['up', 'down', 'left', 'right', "➡️", "⬅️","⬇️", "⬆️"]:
            self.sounds.ps("arrow")
        elif key_name in ["space", "☄️"]:
            self.sounds.ps("space")
        elif key_name in ["backspace", "🗑️", "🕳️"]:
            self.sounds.ps("backspace")
        elif key_name in ["enter", "↩️"]:
            self.sounds.ps("enter")
        else:
            self.sounds.ps("special")


def sort_dict_by_value(d):
    """
    Sort a dictionary by its integer values in descending order.
    Returns a new sorted dictionary.
    """
    return dict(sorted(
        ((k, v) for k, v in d.items() if isinstance(v, int)),
        key=lambda item: item[1],
        reverse=True
    ))



if __name__ == "__main__":
    pass