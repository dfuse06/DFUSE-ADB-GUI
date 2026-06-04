# DFUSE ADB GUI 🔧📱

A lightweight ADB control panel built with Python + Tkinter.

## ✨ Features

* List devices
* Reboot (system / recovery / bootloader)
* Install APKs
* ADB shell commands
* ADB Wi-Fi (tcpip + connect)
* Wireless pairing (Android 11+)
* Dark theme UI
* Windows Support Coming Soon

## 📦 Dependencies

### Arch Linux / EndeavourOS

```bash
sudo pacman -S python tk android-tools
```

### Verify Dependencies

```bash
python --version
adb version
```

## Install via Pacman (Arch Linux / EndeavourOS)

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

## 🚀 Run from Source

```bash
python main.py
```

## 🛠️ Troubleshooting

If you receive:

```text
ImportError: libtk8.6.so: cannot open shared object file
```

Install Tk:

```bash
sudo pacman -S tk
```

<img src="https://raw.githubusercontent.com/dfuse06/DFUSE-ADB-GUI/main/main-ui.png">
<img src="https://raw.githubusercontent.com/dfuse06/DFUSE-ADB-GUI/main/ui_2.png">
