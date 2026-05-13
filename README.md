# DFUSE ADB GUI 🔧📱

A lightweight ADB control panel built with Python + Tkinter.

## ✨ Features
- List devices
- Reboot (system / recovery / bootloader)
- Install APKs
- ADB shell commands
- ADB Wi-Fi (tcpip + connect)
- Wireless pairing (Android 11+)
- Dark theme UI
- Windows Support Coming Soon

# Install via Pacman (CachyOS / Arch Linux)

Add the repository to `/etc/pacman.conf`:

```ini
[dfuse-repo]
SigLevel = Optional TrustAll
Server = https://dfuse06.github.io/dfuse-repo
```

Sync repositories:

```bash
sudo pacman -Syy
```

Install DFUSE ADB GUI:

```bash
sudo pacman -S dfuse-adb-gui
```

Launch:

```bash
dfuse-adb-gui
```

<img src="https://raw.githubusercontent.com/dfuse06/DFUSE-ADB-GUI/main/main-ui.png">
<img src="https://raw.githubusercontent.com/dfuse06/DFUSE-ADB-GUI/main/ui_2.png">

## 🚀 Run
```bash
python3 main.py


