from os import path

def load_config(reset = False):
    if path.exists(".config") and reset == False:
        with open(".config", 'r') as file:
            return file.read().strip()
    else: 
        with open(".config", "w") as file:
            file.write("default")
        return "default"
    
def save_config(pack: str):
        with open(".config", "w") as file:
            file.write(pack.strip())
    
if __name__ == "__main__":
    x = load_config()
    print(x)