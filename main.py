import os
import sys
import subprocess
import threading
import zipfile
import shutil
import urllib.request
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox


BG_COLOR = "#121212"
PANEL_COLOR = "#1E1E1E"
INPUT_COLOR = "#2A2A2A"
BUTTON_COLOR = "#2F2F2F"
BUTTON_ACTIVE = "#3A3A3A"
TEXT_COLOR = "#FFFFFF"
MUTED_TEXT = "#BBBBBB"

PLATFORM_TOOLS_URLS = {
    "linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip",
    "windows": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
    "mac": "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip",
}


def get_base_path() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_platform_tools_dir() -> str:
    return os.path.join(get_base_path(), "platform-tools")


def get_adb_path() -> str:
    base = get_platform_tools_dir()

    if sys.platform.startswith("linux"):
        return os.path.join(base, "linux", "adb")

    if sys.platform.startswith("win"):
        return os.path.join(base, "windows", "adb.exe")

    if sys.platform == "darwin":
        return os.path.join(base, "mac", "adb")

    return "adb"

def detect_platform_tools_url() -> str:
    if sys.platform.startswith("linux"):
        return PLATFORM_TOOLS_URLS["linux"]
    if sys.platform.startswith("win"):
        return PLATFORM_TOOLS_URLS["windows"]
    if sys.platform == "darwin":
        return PLATFORM_TOOLS_URLS["mac"]
    raise RuntimeError(f"Unsupported OS: {sys.platform}")


def check_adb_status() -> tuple[bool, str]:
    adb_path = get_adb_path()

    if os.path.isabs(adb_path) and os.path.exists(adb_path):
        if not os.access(adb_path, os.X_OK):
            return False, (
                f"Bundled adb is not executable:\n{adb_path}\n\n"
                f"Run:\nchmod +x \"{adb_path}\""
            )

    return True, adb_path


def run_adb_command(command: list[str], input_text: str | None = None, timeout: int = 90) -> str:
    ok, status = check_adb_status()
    if not ok:
        return status

    adb_path = get_adb_path()
    full_command = [adb_path] + command

    try:
        result = subprocess.run(
            full_command,
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        parts = []
        if stdout:
            parts.append(stdout)
        if stderr:
            parts.append(stderr)

        if not parts:
            return f"Command finished with exit code {result.returncode}"

        return "\n".join(parts)

    except FileNotFoundError:
        return "ADB not found. Bundle platform-tools with the app or install adb on the system."
    except PermissionError:
        return (
            f"Permission denied running adb:\n{adb_path}\n\n"
            f"Run:\nchmod +x \"{adb_path}\""
        )
    except subprocess.TimeoutExpired:
        return "ADB command timed out."
    except Exception as e:
        return f"Error: {e}"


def safe_ui(callback, *args):
    root.after(0, lambda: callback(*args))


def run_in_thread(task):
    threading.Thread(target=task, daemon=True).start()


def show_output(text: str) -> None:
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, text)
    output_box.see(tk.END)


def append_output(text: str) -> None:
    output_box.insert(tk.END, text + "\n")
    output_box.see(tk.END)


def clear_output() -> None:
    show_output("")


def styled_button(parent, text, command, width=16):
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


# ---------------------------
# Core ADB actions
# ---------------------------

def adb_version() -> None:
    run_in_thread(lambda: safe_ui(show_output, run_adb_command(["version"])))


def list_devices() -> None:
    run_in_thread(lambda: safe_ui(show_output, run_adb_command(["devices"])))


def restart_adb() -> None:
    def task():
        out1 = run_adb_command(["kill-server"])
        out2 = run_adb_command(["start-server"])
        safe_ui(show_output, f"{out1}\n\n{out2}")

    run_in_thread(task)


def reboot_device() -> None:
    run_in_thread(lambda: safe_ui(show_output, run_adb_command(["reboot"])))


def reboot_recovery() -> None:
    run_in_thread(lambda: safe_ui(show_output, run_adb_command(["reboot", "recovery"])))


def reboot_bootloader() -> None:
    run_in_thread(lambda: safe_ui(show_output, run_adb_command(["reboot", "bootloader"])))


def device_info() -> None:
    run_in_thread(lambda: safe_ui(show_output, run_adb_command(["shell", "getprop"], timeout=120)))


def install_apk() -> None:
    apk_path = filedialog.askopenfilename(
        title="Select APK",
        filetypes=[("APK files", "*.apk")]
    )
    if not apk_path:
        return

    def task():
        safe_ui(show_output, f"Installing APK...\n{apk_path}\n")
        result = run_adb_command(["install", apk_path], timeout=300)
        safe_ui(append_output, result)

    run_in_thread(task)


def adb_shell() -> None:
    cmd = shell_entry.get().strip()
    if not cmd:
        messagebox.showwarning("Missing command", "Enter a shell command first.")
        return

    def task():
        result = run_adb_command(["shell", cmd], timeout=120)
        safe_ui(show_output, result)

    run_in_thread(task)


def get_device_ip() -> None:
    def task():
        result = run_adb_command(["shell", "ip", "addr", "show", "wlan0"], timeout=120)
        safe_ui(show_output, result)

    run_in_thread(task)


# ---------------------------
# ADB updater
# ---------------------------

def update_platform_tools() -> None:
    def task():
        try:
            safe_ui(show_output, "Checking for latest platform-tools...\n")

            url = detect_platform_tools_url()
            base_path = get_base_path()
            zip_path = os.path.join(base_path, "platform-tools-latest.zip")
            temp_extract_dir = os.path.join(base_path, "_platform_tools_temp")
            final_tools_dir = get_platform_tools_dir()
            backup_dir = final_tools_dir + "_old"

            safe_ui(append_output, f"Downloading:\n{url}\n")
            urllib.request.urlretrieve(url, zip_path)

            safe_ui(append_output, "Extracting update...\n")

            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            os.makedirs(temp_extract_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_extract_dir)

            extracted_tools_dir = os.path.join(temp_extract_dir, "platform-tools")
            if not os.path.exists(extracted_tools_dir):
                raise RuntimeError("Downloaded archive did not contain a platform-tools folder.")

            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)

            if os.path.exists(final_tools_dir):
                os.rename(final_tools_dir, backup_dir)

            shutil.move(extracted_tools_dir, final_tools_dir)

            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)

            if os.name != "nt":
                adb_path = os.path.join(final_tools_dir, "adb")
                fastboot_path = os.path.join(final_tools_dir, "fastboot")
                if os.path.exists(adb_path):
                    os.chmod(adb_path, 0o755)
                if os.path.exists(fastboot_path):
                    os.chmod(fastboot_path, 0o755)

            run_adb_command(["kill-server"])
            start_result = run_adb_command(["start-server"])
            version_result = run_adb_command(["version"])

            safe_ui(append_output, "Update complete.\n")
            safe_ui(append_output, start_result + "\n")
            safe_ui(append_output, version_result)

        except Exception as e:
            safe_ui(append_output, f"Update failed:\n{e}")

    run_in_thread(task)


# ---------------------------
# Legacy Wi-Fi TCP/IP
# ---------------------------

def enable_tcpip() -> None:
    port = tcpip_port_entry.get().strip() or "5555"

    def task():
        result = run_adb_command(["tcpip", port])
        safe_ui(show_output, result)

    run_in_thread(task)


def connect_wifi() -> None:
    ip = wifi_ip_entry.get().strip()
    port = wifi_port_entry.get().strip() or "5555"

    if not ip:
        messagebox.showwarning("Missing IP", "Enter the device IP address.")
        return

    def task():
        result = run_adb_command(["connect", f"{ip}:{port}"])
        safe_ui(show_output, result)

    run_in_thread(task)


def disconnect_wifi() -> None:
    ip = wifi_ip_entry.get().strip()
    port = wifi_port_entry.get().strip() or "5555"

    def task():
        if ip:
            result = run_adb_command(["disconnect", f"{ip}:{port}"])
        else:
            result = run_adb_command(["disconnect"])
        safe_ui(show_output, result)

    run_in_thread(task)


# ---------------------------
# Wireless Pairing Dialogs
# ---------------------------

class PairUsingCodeDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result_ip = None
        self.result_port = None
        self.result_code = None
        self.entries: list[tk.Entry] = []

        self.top = tk.Toplevel(parent)
        self.top.title("Pair using code")
        self.top.configure(bg=BG_COLOR)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        self.build_ui()
        self.center_window()

    def build_ui(self):
        main = tk.Frame(self.top, bg=BG_COLOR, padx=24, pady=20)
        main.pack(fill="both", expand=True)

        tk.Label(
            main,
            text="Pair device over Wi-Fi",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 18, "bold")
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(
            main,
            text="Enter the pairing IP, pairing port, and the 6 digit code shown on the device.",
            bg=BG_COLOR,
            fg=MUTED_TEXT,
            justify="left"
        ).pack(anchor="w", pady=(0, 14))

        form = tk.Frame(main, bg=BG_COLOR)
        form.pack(fill="x", pady=(0, 14))

        tk.Label(form, text="Pair IP:", bg=BG_COLOR, fg=MUTED_TEXT).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=6)
        self.ip_entry = styled_entry(form, width=20)
        self.ip_entry.grid(row=0, column=1, sticky="w", pady=6)

        tk.Label(form, text="Pair Port:", bg=BG_COLOR, fg=MUTED_TEXT).grid(row=0, column=2, sticky="w", padx=(18, 8), pady=6)
        self.port_entry = styled_entry(form, width=12)
        self.port_entry.grid(row=0, column=3, sticky="w", pady=6)

        tk.Label(
            main,
            text="Enter the 6 digit pairing code",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 11)
        ).pack(anchor="w", pady=(4, 10))

        digits_frame = tk.Frame(main, bg=BG_COLOR)
        digits_frame.pack(pady=(0, 14))

        for i in range(6):
            entry = tk.Entry(
                digits_frame,
                width=2,
                justify="center",
                font=("Arial", 18, "bold"),
                bg=INPUT_COLOR,
                fg=TEXT_COLOR,
                insertbackground=TEXT_COLOR,
                relief="flat",
                bd=8
            )
            entry.grid(row=0, column=i, padx=6)
            entry.bind("<KeyRelease>", lambda event, idx=i: self.on_key(event, idx))
            entry.bind("<BackSpace>", lambda event, idx=i: self.on_backspace(event, idx))
            self.entries.append(entry)

        self.ip_entry.bind("<KeyRelease>", lambda event: self.update_pair_button())
        self.port_entry.bind("<KeyRelease>", lambda event: self.update_pair_button())

        self.ip_entry.focus_set()

        tk.Label(
            main,
            text="This may take up to 2 minutes.",
            bg=BG_COLOR,
            fg=MUTED_TEXT,
            font=("Arial", 10)
        ).pack(pady=(0, 18))

        btn_row = tk.Frame(main, bg=BG_COLOR)
        btn_row.pack(fill="x")

        self.pair_btn = tk.Button(
            btn_row,
            text="Pair",
            width=10,
            command=self.submit,
            bg=BUTTON_COLOR,
            fg=TEXT_COLOR,
            activebackground=BUTTON_ACTIVE,
            activeforeground=TEXT_COLOR,
            relief="flat",
            bd=0,
            padx=8,
            pady=6,
            state="disabled"
        )
        self.pair_btn.pack(side="right", padx=(8, 0))

        cancel_btn = tk.Button(
            btn_row,
            text="Cancel",
            width=10,
            command=self.close,
            bg=BUTTON_COLOR,
            fg=TEXT_COLOR,
            activebackground=BUTTON_ACTIVE,
            activeforeground=TEXT_COLOR,
            relief="flat",
            bd=0,
            padx=8,
            pady=6
        )
        cancel_btn.pack(side="right")

        self.top.bind("<Return>", lambda event: self.submit())
        self.top.bind("<Escape>", lambda event: self.close())
        self.top.protocol("WM_DELETE_WINDOW", self.close)

    def center_window(self):
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - (height // 2)
        self.top.geometry(f"+{x}+{y}")

    def get_code(self) -> str:
        return "".join(entry.get().strip() for entry in self.entries)

    def update_pair_button(self):
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        code = self.get_code()

        if ip and port and len(code) == 6 and code.isdigit():
            self.pair_btn.config(state="normal")
        else:
            self.pair_btn.config(state="disabled")

    def on_key(self, event, idx: int):
        value = self.entries[idx].get()
        filtered = "".join(ch for ch in value if ch.isdigit())

        if len(filtered) > 1:
            filtered = filtered[-1]

        self.entries[idx].delete(0, tk.END)
        self.entries[idx].insert(0, filtered)

        if filtered and idx < len(self.entries) - 1:
            self.entries[idx + 1].focus_set()
            self.entries[idx + 1].selection_range(0, tk.END)

        self.update_pair_button()

    def on_backspace(self, event, idx: int):
        current = self.entries[idx].get()
        if current:
            return

        if idx > 0:
            self.entries[idx - 1].focus_set()
            self.entries[idx - 1].delete(0, tk.END)

        self.update_pair_button()

    def submit(self):
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        code = self.get_code()

        if not ip:
            messagebox.showwarning("Missing IP", "Enter the pairing IP address.", parent=self.top)
            return
        if not port:
            messagebox.showwarning("Missing port", "Enter the pairing port.", parent=self.top)
            return
        if len(code) != 6 or not code.isdigit():
            messagebox.showwarning("Invalid code", "Enter a valid 6 digit pairing code.", parent=self.top)
            return

        self.result_ip = ip
        self.result_port = port
        self.result_code = code
        self.top.destroy()

    def close(self):
        self.result_ip = None
        self.result_port = None
        self.result_code = None
        self.top.destroy()


class PairUsingQrDialog:
    def __init__(self, parent):
        self.parent = parent

        self.top = tk.Toplevel(parent)
        self.top.title("Pair using QR")
        self.top.configure(bg=BG_COLOR)
        self.top.resizable(False, False)
        self.top.transient(parent)
        self.top.grab_set()

        self.build_ui()
        self.center_window()

    def build_ui(self):
        main = tk.Frame(self.top, bg=BG_COLOR, padx=24, pady=20)
        main.pack(fill="both", expand=True)

        tk.Label(
            main,
            text="Pair device using QR",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Arial", 18, "bold")
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(
            main,
            text=(
                "QR pairing UI is ready.\n\n"
                "The actual Android wireless debugging QR backend\n"
                "still needs to be implemented."
            ),
            bg=BG_COLOR,
            fg=MUTED_TEXT,
            justify="left"
        ).pack(anchor="w", pady=(0, 14))

        qr_frame = tk.Frame(
            main,
            bg="#0D0D0D",
            bd=1,
            relief="solid",
            padx=20,
            pady=20
        )
        qr_frame.pack(pady=(0, 16))

        tk.Label(
            qr_frame,
            text="QR CODE\nCOMING NEXT",
            bg="#0D0D0D",
            fg=TEXT_COLOR,
            font=("Arial", 18, "bold"),
            justify="center",
            width=18,
            height=8
        ).pack()

        tk.Label(
            main,
            text=(
                "Phone steps:\n"
                "Developer options > Wireless debugging > Pair device with QR code\n"
                "Then scan the QR shown here."
            ),
            bg=BG_COLOR,
            fg=MUTED_TEXT,
            justify="left"
        ).pack(anchor="w", pady=(0, 18))

        btn_row = tk.Frame(main, bg=BG_COLOR)
        btn_row.pack(fill="x")

        close_btn = tk.Button(
            btn_row,
            text="Close",
            width=10,
            command=self.close,
            bg=BUTTON_COLOR,
            fg=TEXT_COLOR,
            activebackground=BUTTON_ACTIVE,
            activeforeground=TEXT_COLOR,
            relief="flat",
            bd=0,
            padx=8,
            pady=6
        )
        close_btn.pack(side="right")

        self.top.bind("<Escape>", lambda event: self.close())
        self.top.protocol("WM_DELETE_WINDOW", self.close)

    def center_window(self):
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - (height // 2)
        self.top.geometry(f"+{x}+{y}")

    def close(self):
        self.top.destroy()


def pair_using_code_popup() -> None:
    dialog = PairUsingCodeDialog(root)
    root.wait_window(dialog.top)

    if not dialog.result_ip or not dialog.result_port or not dialog.result_code:
        return

    ip = dialog.result_ip
    pair_port = dialog.result_port
    code = dialog.result_code

    def task():
        pair_target = f"{ip}:{pair_port}"
        safe_ui(show_output, f"Pairing with {pair_target} ...")
        pair_result = run_adb_command(
            ["pair", pair_target],
            input_text=code + "\n",
            timeout=120
        )
        safe_ui(append_output, "\n" + pair_result)

    run_in_thread(task)


def pair_using_qr_popup() -> None:
    dialog = PairUsingQrDialog(root)
    root.wait_window(dialog.top)


# ---------------------------
# UI
# ---------------------------

root = tk.Tk()
root.title("DFUSE ADB GUI")
root.geometry("1180x860")
root.configure(bg=BG_COLOR)

header = tk.Frame(root, bg=BG_COLOR)
header.pack(fill="x", padx=10, pady=(10, 0))

tk.Label(
    header,
    text="DFUSE ADB GUI",
    bg=BG_COLOR,
    fg=TEXT_COLOR,
    font=("Arial", 20, "bold")
).pack(anchor="w")

tk.Label(
    header,
    text=f"ADB Path: {get_adb_path()}",
    bg=BG_COLOR,
    fg=MUTED_TEXT,
    font=("Arial", 10)
).pack(anchor="w", pady=(2, 0))

top_buttons = tk.Frame(root, bg=BG_COLOR)
top_buttons.pack(fill="x", padx=10, pady=8)

styled_button(top_buttons, "ADB Version", adb_version, 14).grid(row=0, column=0, padx=4, pady=4)
styled_button(top_buttons, "List Devices", list_devices, 14).grid(row=0, column=1, padx=4, pady=4)
styled_button(top_buttons, "Restart ADB", restart_adb, 14).grid(row=0, column=2, padx=4, pady=4)
styled_button(top_buttons, "Update ADB", update_platform_tools, 14).grid(row=0, column=3, padx=4, pady=4)
styled_button(top_buttons, "Install APK", install_apk, 14).grid(row=0, column=4, padx=4, pady=4)
styled_button(top_buttons, "Device Info", device_info, 14).grid(row=0, column=5, padx=4, pady=4)
styled_button(top_buttons, "Get Wi-Fi IP", get_device_ip, 14).grid(row=0, column=6, padx=4, pady=4)
styled_button(top_buttons, "Clear Output", clear_output, 14).grid(row=0, column=7, padx=4, pady=4)

reboot_buttons = tk.Frame(root, bg=BG_COLOR)
reboot_buttons.pack(fill="x", padx=10, pady=(0, 8))

styled_button(reboot_buttons, "Reboot", reboot_device, 14).grid(row=0, column=0, padx=4, pady=4)
styled_button(reboot_buttons, "Recovery", reboot_recovery, 14).grid(row=0, column=1, padx=4, pady=4)
styled_button(reboot_buttons, "Bootloader", reboot_bootloader, 14).grid(row=0, column=2, padx=4, pady=4)

shell_frame = tk.LabelFrame(
    root,
    text="ADB Shell",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    bd=1,
    relief="solid",
    padx=10,
    pady=8
)
shell_frame.pack(fill="x", padx=10, pady=8)

tk.Label(shell_frame, text="ADB Shell Command:", bg=PANEL_COLOR, fg=MUTED_TEXT).pack(anchor="w")
shell_entry = styled_entry(shell_frame)
shell_entry.pack(fill="x", pady=4)
styled_button(shell_frame, "Run Shell Command", adb_shell, 16).pack(anchor="w", pady=(4, 0))

legacy_wifi_frame = tk.LabelFrame(
    root,
    text="ADB Wi-Fi (Legacy TCP/IP Method)",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    bd=1,
    relief="solid",
    padx=10,
    pady=8
)
legacy_wifi_frame.pack(fill="x", padx=10, pady=8)

tk.Label(legacy_wifi_frame, text="TCP/IP Port:", bg=PANEL_COLOR, fg=MUTED_TEXT).grid(row=0, column=0, padx=5, pady=4, sticky="w")
tcpip_port_entry = styled_entry(legacy_wifi_frame, width=12)
tcpip_port_entry.insert(0, "5555")
tcpip_port_entry.grid(row=0, column=1, padx=5, pady=4, sticky="w")
styled_button(legacy_wifi_frame, "Enable TCP/IP", enable_tcpip, 14).grid(row=0, column=2, padx=5, pady=4)

tk.Label(legacy_wifi_frame, text="Device IP:", bg=PANEL_COLOR, fg=MUTED_TEXT).grid(row=1, column=0, padx=5, pady=4, sticky="w")
wifi_ip_entry = styled_entry(legacy_wifi_frame, width=20)
wifi_ip_entry.grid(row=1, column=1, padx=5, pady=4, sticky="w")

tk.Label(legacy_wifi_frame, text="Port:", bg=PANEL_COLOR, fg=MUTED_TEXT).grid(row=1, column=2, padx=5, pady=4, sticky="w")
wifi_port_entry = styled_entry(legacy_wifi_frame, width=12)
wifi_port_entry.insert(0, "5555")
wifi_port_entry.grid(row=1, column=3, padx=5, pady=4, sticky="w")

styled_button(legacy_wifi_frame, "Connect", connect_wifi, 12).grid(row=1, column=4, padx=5, pady=4)
styled_button(legacy_wifi_frame, "Disconnect", disconnect_wifi, 12).grid(row=1, column=5, padx=5, pady=4)

pair_frame = tk.LabelFrame(
    root,
    text="ADB Wireless Pairing (Android 11+)",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    bd=1,
    relief="solid",
    padx=10,
    pady=8
)
pair_frame.pack(fill="x", padx=10, pady=8)

tk.Label(
    pair_frame,
    text="Use a dialog for code pairing or QR pairing.",
    bg=PANEL_COLOR,
    fg=MUTED_TEXT,
    justify="left"
).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

styled_button(pair_frame, "Pair using code", pair_using_code_popup, 16).grid(row=1, column=0, padx=4, pady=4, sticky="w")
styled_button(pair_frame, "Pair using QR", pair_using_qr_popup, 16).grid(row=1, column=1, padx=4, pady=4, sticky="w")

help_text = (
    "Android steps:\n"
    "Developer options > Wireless debugging > Pair device with pairing code or Pair device with QR code\n"
    "Use 'Pair using code' to enter Pair IP, Pair Port, and the 6 digit pairing code."
)

tk.Label(
    pair_frame,
    text=help_text,
    bg=PANEL_COLOR,
    fg=MUTED_TEXT,
    justify="left"
).grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 0))

output_frame = tk.LabelFrame(
    root,
    text="Output",
    bg=PANEL_COLOR,
    fg=TEXT_COLOR,
    bd=1,
    relief="solid",
    padx=8,
    pady=8
)
output_frame.pack(fill="both", expand=True, padx=10, pady=8)

output_box = scrolledtext.ScrolledText(
    output_frame,
    wrap=tk.WORD,
    bg="#0D0D0D",
    fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR,
    relief="flat",
    bd=0,
    font=("Consolas", 10)
)
output_box.pack(fill="both", expand=True)

show_output("DFUSE ADB GUI ready.")
root.mainloop()