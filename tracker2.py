# from pynput import keyboard
import os
import time
# TODO: Make this script sub to the GUI
# TODO: Add a WPM counter
# TODO: Handle keys repeating (a key heald down)


groups = {"space": ['space'],
          "arrow": ['up', 'down', 'left', 'right'],
          "backspace": ['backspace'],
          "enter": ['enter']}

class KeyHandler:
    '''
    Class to handle key stats, apm
    '''
    def __init__(self):
        self.key_stats = {}
        self.logfile("load")
        self.apm = 0
        self.apm_times = []

    def on_press(self, key):
        
        self.update_apm()

        # determine key type
        try: # BUG: if key is ':' it will break the parsing when loading the key stats
            if hasattr(key, "char") and key.char is not None: # is a alpha numeric key
                # Make sure char is lowercase to avoid tracking same char twice
                self.key_stats[key.char.lower()] = self.key_stats.get(key.char.lower(), 0) + 1
                actual_key = key.char.lower()
            
            elif hasattr(key, "name"): # is mod, arrow, etc.
                self.key_stats[str(key.name)] = self.key_stats.get(str(key.name), 0) + 1
                actual_key = key.name.lower()

        except Exception as e:
            print("Failed to determine key type\n\t{e}")

        print(f"Tracker: Pressed {actual_key}")
        return {"apm": self.apm}

    def get_apm(self):
        return self.apm

    def update_apm(self):
        '''
        Method for calculating APM
        '''
        now = time.time()
        self.apm_times.append(now) # add the current time to the list
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
                    for key, count in self.key_stats.items():
                        f.write(f'{key}: {count}\n')
                print("Keys saved to key_log.txt")
            except Exception as e:
                print(f"Error saving keys: {e}")


if __name__ == "__main__":
    x = KeyHandler()
    while True:
        time.sleep(0.5)
        print(x.update_apm())