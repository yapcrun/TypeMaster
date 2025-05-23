# TypeMaster

TypeMaster is a Python-based input tracker for linux that plays sound effects when keys are pressed. It is designed to enhance the typing experience by associating key presses with customizable sound effects.

## Features

- **Key Sound Effects**: Plays different sound effects for specific keys based on their function.
- **Customizable Sound Packs**: Supports multiple sound packs stored in the `sounds/` directory.
- **Key Logging**: Logs the frequency of key presses to a file (`key_log.txt`).
- **Threaded Sound Playback**: Ensures non-blocking sound playback using threads.

## Project Structure

- `main.py`: The main script that runs the input tracker and sound playback.
- `sounds/`: Directory containing sound packs. Each pack has subdirectories for key sounds based on their category.
- `key_log.txt`: File where key press counts are logged.

## Hotkeys

- **Exit application**: `ctrl + q`
- **Pause sounds**: `ctrl + l` 

## Requirements

### System

- `alsa-utils` to run sounds with aplay

### Python

- Python 3.6+
- `pynput` library for keyboard event handling.
- `pillow` library for loading images
- `pystray` library for tray functionality

Install python dependencies using:

```bash
pip install -r requirements.txt
```
