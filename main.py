import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox


BG_COLOR = "#121212"
PANEL_COLOR = "#1E1E1E"
INPUT_COLOR = "#2A2A2A"
BUTTON_COLOR = "#2F2F2F"
BUTTON_ACTIVE = "#3A3A3A"
TEXT_COLOR = "#FFFFFF"
MUTED_TEXT = "#BBBBBB"


def get_base_path() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_adb_path() -> str:
    base_path = get_base_path()

    if os.name == "nt":
        adb_name = "adb.exe"
    else:
        adb_name = "adb"

    bundled_adb = os.path.join(base_path, "platform-tools", adb_name)

    if os.path.exists(bundled_adb):
        return bundled_adb

    return adb_name


def run_adb_command(command: list[str]) -> str:
    adb_path = get_adb_path()
    full_command = [adb_path] + command

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=False
        )
        if result.stderr and not result.stdout:
            return result.stderr.strip()
        return (result.stdout + "\n" + result.stderr).strip()
    except FileNotFoundError:
        return "Bundled adb not found. Make sure platform-tools is included."


def show_output(text: str) -> None:
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, text)


def list_devices() -> None:
    show_output(run_adb_command(["devices"]))


def reboot_device() -> None:
    show_output(run_adb_command(["reboot"]))


def reboot_recovery() -> None:
    show_output(run_adb_command(["reboot", "recovery"]))


def reboot_bootloader() -> None:
    show_output(run_adb_command(["reboot", "bootloader"]))


def device_info() -> None:
    show_output(run_adb_command(["shell", "getprop"]))


def install_apk() -> None:
    apk_path = filedialog.askopenfilename(
        title="Select APK",
        filetypes=[("APK files", "*.apk")]
    )
    if not apk_path:
        return
    show_output(run_adb_command(["install", apk_path]))


def adb_shell() -> None:
    cmd = shell_entry.get().strip()
    if not cmd:
        messagebox.showwarning("Missing command", "Enter a shell command first.")
        return
    show_output(run_adb_command(["shell", cmd]))


def enable_tcpip() -> None:
    port = tcpip_port_entry.get().strip() or "5555"
    show_output(run_adb_command(["tcpip", port]))


def connect_wifi() -> None:
    ip = wifi_ip_entry.get().strip()
    port = wifi_port_entry.get().strip() or "5555"

    if not ip:
        messagebox.showwarning("Missing IP", "Enter the device IP address.")
        return

    show_output(run_adb_command(["connect", f"{ip}:{port}"]))


def disconnect_wifi() -> None:
    ip = wifi_ip_entry.get().strip()
    port = wifi_port_entry.get().strip() or "5555"

    if ip:
        show_output(run_adb_command(["disconnect", f"{ip}:{port}"]))
    else:
        show_output(run_adb_command(["disconnect"]))


def adb_pair() -> None:
    ip = pair_ip_entry.get().strip()
    port = pair_port_entry.get().strip()
    code = pair_code_entry.get().strip()

    if not ip or not port or not code:
        messagebox.showwarning(
            "Missing info",
            "Enter pairing IP, pairing port, and pairing code."
        )
        return

    show_output(run_adb_command(["pair", f"{ip}:{port}", code]))


def get_device_ip() -> None:
    show_output(run_adb_command(["shell", "ip", "addr", "show", "wlan0"]))


def styled_button(parent, text, command, width=18):
    return tk.Button(
        parent,
        text=text,
        width=width,
        command=command,
        bg=BUTTON_COLOR,
        fg=TEXT_COLOR,
        activebackground=BUTTON_ACTIVE,
        activeforeground=TEXT_COLOR,
        relief="flat",
        bd=0,
        padx=8,
        pady=6,
        highlightthickness=0
    )


def styled_entry(parent, width=None):
    return tk.Entry(
        parent,
        width=width,
        bg=INPUT_COLOR,
        fg=TEXT_COLOR,
        insertbackground=TEXT_COLOR,
        relief="flat",
        bd=6
    )


root = tk.Tk()
root.title(" DFUSE ADB GUI")
root.geometry("900x700")
root.configure(bg=BG_COLOR)

button_frame = tk.Frame(root, bg=BG_COLOR)
button_frame.pack(pady=10)

styled_button(button_frame, "List Devices", list_devices).grid(row=0, column=0, padx=5, pady=5)
styled_button(button_frame, "Reboot", reboot_device).grid(row=0, column=1, padx=5, pady=5)
styled_button(button_frame, "Recovery", reboot_recovery).grid(row=0, column=2, padx=5, pady=5)
styled_button(button_frame, "Bootloader", reboot_bootloader).grid(row=0, column=3, padx=5, pady=5)

styled_button(button_frame, "Install APK", install_apk).grid(row=1, column=0, padx=5, pady=5)
styled_button(button_frame, "Device Info", device_info).grid(row=1, column=1, padx=5, pady=5)
styled_button(button_frame, "Get Wi-Fi IP", get_device_ip).grid(row=1, column=2, padx=5, pady=5)

shell_frame = tk.LabelFrame(
    root,
    text="ADB Shell",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    bd=1,
    relief="solid",
    padx=10,
    pady=10
)
shell_frame.pack(fill="x", padx=10, pady=10)

tk.Label(shell_frame, text="ADB Shell Command:", bg=PANEL_COLOR, fg=MUTED_TEXT).pack(anchor="w")
shell_entry = styled_entry(shell_frame)
shell_entry.pack(fill="x", pady=5)

styled_button(shell_frame, "Run Shell Command", adb_shell).pack(anchor="w", pady=(5, 0))

wifi_frame = tk.LabelFrame(
    root,
    text="ADB Wi-Fi (Legacy TCP/IP Method)",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    bd=1,
    relief="solid",
    padx=10,
    pady=10
)
wifi_frame.pack(fill="x", padx=10, pady=10)

tk.Label(wifi_frame, text="TCP/IP Port:", bg=PANEL_COLOR, fg=MUTED_TEXT).grid(row=0, column=0, padx=5, pady=5, sticky="w")
tcpip_port_entry = styled_entry(wifi_frame, width=12)
tcpip_port_entry.insert(0, "5555")
tcpip_port_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

styled_button(wifi_frame, "Enable TCP/IP", enable_tcpip).grid(row=0, column=2, padx=5, pady=5)

tk.Label(wifi_frame, text="Device IP:", bg=PANEL_COLOR, fg=MUTED_TEXT).grid(row=1, column=0, padx=5, pady=5, sticky="w")
wifi_ip_entry = styled_entry(wifi_frame, width=20)
wifi_ip_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

tk.Label(wifi_frame, text="Port:", bg=PANEL_COLOR, fg=MUTED_TEXT).grid(row=1, column=2, padx=5, pady=5, sticky="w")
wifi_port_entry = styled_entry(wifi_frame, width=12)
wifi_port_entry.insert(0, "5555")
wifi_port_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")

styled_button(wifi_frame, "Connect", connect_wifi).grid(row=1, column=4, padx=5, pady=5)
styled_button(wifi_frame, "Disconnect", disconnect_wifi).grid(row=1, column=5, padx=5, pady=5)

pair_frame = tk.LabelFrame(
    root,
    text="ADB Wireless Pairing (Android 11+)",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    bd=1,
    relief="solid",
    padx=10,
    pady=10
)
pair_frame.pack(fill="x", padx=10, pady=10)

tk.Label(pair_frame, text="Pair IP:", bg=PANEL_COLOR, fg=MUTED_TEXT).grid(row=0, column=0, padx=5, pady=5, sticky="w")
pair_ip_entry = styled_entry(pair_frame, width=18)
pair_ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(pair_frame, text="Pair Port:", bg=PANEL_COLOR, fg=MUTED_TEXT).grid(row=0, column=2, padx=5, pady=5, sticky="w")
pair_port_entry = styled_entry(pair_frame, width=10)
pair_port_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

tk.Label(pair_frame, text="Pair Code:", bg=PANEL_COLOR, fg=MUTED_TEXT).grid(row=0, column=4, padx=5, pady=5, sticky="w")
pair_code_entry = styled_entry(pair_frame, width=12)
pair_code_entry.grid(row=0, column=5, padx=5, pady=5, sticky="w")

styled_button(pair_frame, "Pair Device", adb_pair).grid(row=0, column=6, padx=5, pady=5)

output_box = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    bg="#0D0D0D",
    fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR,
    relief="flat",
    bd=0
)
output_box.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()