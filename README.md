# TypeMaster

TypeMaster is a cross-platform, GUI, Python-based typing enhancer that plays sound effects when keys are pressed. It is designed to enhance the typing experience by associating key presses with customizable sound effects.

## Features

- **GUI**: User interface to interact with the program and view stats..
- **Tray Support**: Control functionality through a system tray icon.
- **Key Sound Effects**: Plays different sound effects for specific keys based on their function.
- **Customizable Sound Packs**: Supports multiple sound packs stored in the `sounds/` directory.
- **Key Stat Tracking**: Tracks the total key presses to a file (`key_log`).
- **Threaded Sound Playback**: Ensures non-blocking sound playback using pygame's mixer.

## Project Structure

- `tmgui.pyw`: The main entry point to the application.
- `sounds/`: Directory containing sound packs. Each pack has subdirectories for key sounds based on their category.
- `key_log`: Json file where key press counts are logged.


## Requirements

### Python

- `Python 3.6+`
- `pynput` library for keyboard event handling.
- `pystray` library for tray functionality.
- `pillow` library for loading images.
- `pygame` library for sound playback

Install python dependencies using:

```bash
pip install -r requirements.txt
```

### Linux


##### If PyQt6 fails to load on linux you must install
`libxcb-xinerama0` `libxcb-xinerama0-dev` `libxcb-cursor0`

Install PyQt6 dependencies using:

```bash
sudo apt-get install libxcb-xinerama0 libxcb-xinerama0-dev libxcb-cursor0
```

## Known Issues

- Linux tray icon will not work correctly if operating in a venv
- Display freezes when operating in a venv
