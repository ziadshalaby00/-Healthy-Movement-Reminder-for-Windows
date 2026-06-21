import os
import sys
import json
import winreg
import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess

# ----------------------------
# UI Theme
# ----------------------------
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# ----------------------------
# Base directory (EXE-safe)
# ----------------------------
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
REG_NAME = "HealthActivityTimer"


# ----------------------------
# Load settings
# ----------------------------
def load_settings():
    if not os.path.exists(CONFIG_FILE):
        return {"interval": "20", "sound_path": "Default.mp3", "enabled": False}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"interval": "20", "sound_path": "Default.mp3", "enabled": False}


# ----------------------------
# Atomic save (safe write)
# ----------------------------
def save_settings(interval, sound_path, enabled):
    data = {
        "interval": interval,
        "sound_path": sound_path,
        "enabled": enabled
    }

    temp_path = CONFIG_FILE + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    os.replace(temp_path, CONFIG_FILE)


# ----------------------------
# Check worker process (EXE-safe)
# ----------------------------
def is_worker_running():
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == "worker.exe":
                return True
    except:
        pass
    return False


# ----------------------------
# GUI Class
# ----------------------------
class TimerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.settings = load_settings()
        self.current_sound_path = self.settings.get("sound_path", "Default.mp3")

        # Window
        self.title("Healthy Movement Reminder")
        self.geometry("450x450")
        self.resizable(False, False)

        # Title
        self.label_title = ctk.CTkLabel(
            self,
            text="⏰ Healthy Sitting Reminder Tool",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.label_title.pack(pady=20)

        # ---------------- Interval ----------------
        self.time_frame = ctk.CTkFrame(self)
        self.time_frame.pack(pady=10, padx=20, fill="x")

        self.label_time = ctk.CTkLabel(self.time_frame, text="Interval (minutes):")
        self.label_time.pack(side="right", padx=10, pady=10)

        self.entry_time = ctk.CTkEntry(self.time_frame, width=100, justify="center")
        self.entry_time.insert(0, self.settings.get("interval", "20"))
        self.entry_time.pack(side="left", padx=10, pady=10)

        # ---------------- Sound ----------------
        self.sound_frame = ctk.CTkFrame(self)
        self.sound_frame.pack(pady=10, padx=20, fill="x")

        self.btn_browse = ctk.CTkButton(
            self.sound_frame,
            text="Choose Sound",
            command=self.browse_sound,
            width=120
        )
        self.btn_browse.pack(side="left", padx=10, pady=10)

        self.lbl_sound = ctk.CTkLabel(
            self.sound_frame,
            text=os.path.basename(self.current_sound_path),
            text_color="gray"
        )
        self.lbl_sound.pack(side="right", padx=10, pady=10)

        # ---------------- Buttons ----------------
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_frame.pack(pady=30)

        self.btn_enable = ctk.CTkButton(
            self.actions_frame,
            text="Enable",
            fg_color="green",
            hover_color="darkgreen",
            command=self.enable_timer
        )
        self.btn_enable.grid(row=0, column=0, padx=10)

        self.btn_disable = ctk.CTkButton(
            self.actions_frame,
            text="Disable",
            fg_color="red",
            hover_color="darkred",
            command=self.disable_timer
        )
        self.btn_disable.grid(row=0, column=1, padx=10)

        # ---------------- Footer ----------------
        self.footer = ctk.CTkLabel(
            self,
            text="Developed by Ziad Shalaby",
            text_color="gray"
        )
        self.footer.pack(side="bottom", pady=15)

        self.update_status_ui()

    # ---------------- Browse Sound ----------------
    def browse_sound(self):
        path = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav")])
        if path:
            self.current_sound_path = path
            self.lbl_sound.configure(text=os.path.basename(path))

    # ---------------- Status ----------------
    def update_status_ui(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_READ
            )
            winreg.QueryValueEx(key, REG_NAME)

            self.btn_enable.configure(state="disabled", text="✨ Enabled")
            self.btn_disable.configure(state="normal")

        except FileNotFoundError:
            self.btn_enable.configure(state="normal", text="Enable")
            self.btn_disable.configure(state="disabled")

    # ---------------- Enable ----------------
    def enable_timer(self):
        interval = self.entry_time.get()

        if not interval.isdigit() or int(interval) <= 0:
            messagebox.showerror("Error", "Invalid interval")
            return

        save_settings(interval, self.current_sound_path, True)

        try:
            worker_path = os.path.join(BASE_DIR, "worker.exe")

            if not is_worker_running():
                subprocess.Popen(
                    worker_path,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_SET_VALUE
            )

            winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, f'"{worker_path}"')
            winreg.CloseKey(key)

        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        messagebox.showinfo("Success", "Timer enabled successfully")
        self.update_status_ui()

    # ---------------- Disable ----------------
    def disable_timer(self):
        save_settings(self.entry_time.get(), self.current_sound_path, False)

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, REG_NAME)
            winreg.CloseKey(key)

        except FileNotFoundError:
            pass

        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        messagebox.showinfo("Disabled", "Timer disabled successfully")
        self.update_status_ui()


# ---------------- Run App ----------------
if __name__ == "__main__":
    app = TimerGUI()
    app.mainloop()