import threading
import customtkinter
import mss
from ai import get_response
from blender_client import check_blender_connection, get_blender_client
from dedup import FrameGate
from tutor import get_tutor_response
from screen import screen_capture_image
from watch_loop import WatchLoop


class ControlsPanel(customtkinter.CTkFrame):
    def __init__(self, parent, on_analyze, on_backend_change, default_backend):
        super().__init__(parent, fg_color="#2b2b2b", corner_radius=0)
        self.on_analyze = on_analyze
        self.on_backend_change = on_backend_change

        # Row 0 is the expanding response area; row 1 is the fixed control bar.
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)

        self.context_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="What are you working on?",
        )
        self.analyze_button = customtkinter.CTkButton(
            self,
            text="Analyze Screen",
            command=self.handle_analyze,
        )
        self.optionmenu = customtkinter.CTkOptionMenu(
            self,
            values=["ollama", "anthropic"],
            command=self.optionmenu_callback,
        )
        self.context_response = customtkinter.CTkTextbox(
            self,
            wrap="word",
        )
        self.context_response.insert("1.0", "Response will appear here.")
        self.context_response.configure(state="disabled")

        self.context_response.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="nsew")
        # Control bar at the bottom.
        self.context_entry.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        # enter key triggers analysis and backspace deletes last word
        self.context_entry.bind("<Return>", self.on_enter_pressed)
        self.analyze_button.grid(row=1, column=1, padx=20, pady=10, sticky="ew")
        self.context_entry.bind("<Control-BackSpace>", self.delete_word)
        self.optionmenu.grid(row=1, column=2, padx=20, pady=10, sticky="ew")
        self.optionmenu.set(default_backend)

        self.watch_label = customtkinter.CTkLabel(
            self,
            text="Screen watch: starting…",
            anchor="w",
            font=customtkinter.CTkFont(size=11),
        )
        self.watch_label.grid(
            row=2, column=0, columnspan=3, padx=20, pady=(0, 4), sticky="w"
        )

        self.blender_label = customtkinter.CTkLabel(
            self,
            text="Blender: checking…",
            anchor="w",
            font=customtkinter.CTkFont(size=11),
        )
        self.blender_label.grid(
            row=3, column=0, columnspan=3, padx=20, pady=(0, 12), sticky="w"
        )

    def set_watch_label(self, text):
        self.watch_label.configure(text=text)

    def set_blender_label(self, text):
        self.blender_label.configure(text=text)

    def get_context(self):
        return self.context_entry.get().strip()

    def clear_input(self):
        self.context_entry.delete(0, "end")

    def set_response(self, text):
        self.context_response.configure(state="normal")
        self.context_response.delete("1.0", "end")
        self.context_response.insert("1.0", text)
        self.context_response.configure(state="disabled")

    def set_loading(self, is_loading):
        if is_loading:
            self.analyze_button.configure(text="Analyzing...", state="disabled")
        else:
            self.analyze_button.configure(text="Analyze Screen", state="normal")

    def delete_word(self, _event):
        current_text = self.context_entry.get()
        if current_text:
            # Find the last space and delete everything after it.
            last_space_index = current_text.rfind(" ")
            if last_space_index != -1:
                self.context_entry.delete(last_space_index + 1, "end")
            else:
                self.context_entry.delete(0, "end")

    def handle_analyze(self):
        self.on_analyze()

    def on_enter_pressed(self, _event):
        self.handle_analyze()

    def optionmenu_callback(self, choice):
        self.on_backend_change(choice)


class App(customtkinter.CTk):
    def __init__(self, config):
        super().__init__()
        self.title("BlenderTutor")
        self.config = config
        self.user_context = ""
        self.monitor_index = 1
        self.border_size = 10
        # Reserve space for taskbar/window chrome so controls are not cut off.
        self.bottom_safe_margin = 70

        self.attributes("-topmost", True)
        self.configure(fg_color="#1f1f1f")

        monitor = self.get_monitor()
        self.panel_height = int(monitor["height"] - self.bottom_safe_margin)
        self.panel_width = int(monitor["width"] * 0.25)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        default_backend = "ollama" if self.config["use_local"] else "anthropic"
        self.controls_panel = ControlsPanel(
            self,
            on_analyze=self.button_click,
            on_backend_change=self.set_backend,
            default_backend=default_backend,
        )
        self.controls_panel.grid(
            row=0,
            column=0,
            padx=self.border_size,
            pady=self.border_size,
            sticky="nsew",
        )

        self.position_panel()

        get_blender_client().host = self.config["blender_host"]
        get_blender_client().port = self.config["blender_port"]

        # Background capture + dedup (same monitor as the panel). Stops on window close.
        self._frame_gate = FrameGate(max_hamming=6)
        self._watch_loop = WatchLoop(
            capture_fn=lambda: screen_capture_image(self.monitor_index),
            should_forward_fn=self._frame_gate.should_forward,
            on_forward=self._on_watch_forward,
            interval_ms=500,
        )
        self._watch_loop.start()
        self.protocol("WM_DELETE_WINDOW", self._on_app_close)
        self.after(1000, self._poll_watch_metrics)
        self.after(500, self._poll_blender_connection)

    def _on_watch_forward(self, _img):
        """Hook when dedup says the screen changed enough to forward a frame."""
        pass

    def _poll_watch_metrics(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        wl = getattr(self, "_watch_loop", None)
        if wl is not None:
            m = wl.metrics
            line = (
                f"Screen watch • seen {m['frames_seen']} • "
                f"forwarded {m['frames_forwarded']} • skipped {m['frames_skipped']}"
            )
            if m.get("last_error"):
                line += f" • error: {m['last_error']}"
            self.controls_panel.set_watch_label(line)
        self.after(1000, self._poll_watch_metrics)

    def _poll_blender_connection(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        if self.config.get("use_blender"):
            ok, msg = check_blender_connection()
            prefix = "Blender"
            line = f"{prefix} • {msg}" if ok else f"{prefix} • not connected — {msg}"
            self.controls_panel.set_blender_label(line)
        else:
            self.controls_panel.set_blender_label("Blender • disabled (USE_BLENDER=false)")
        self.after(5000, self._poll_blender_connection)

    def _on_app_close(self):
        wl = getattr(self, "_watch_loop", None)
        if wl is not None:
            wl.stop()
        self.destroy()

    def button_click(self):
        self.user_context = self.controls_panel.get_context()
        self.controls_panel.clear_input()
        self.controls_panel.set_loading(True)
        threading.Thread(target=self.run_ai_request, daemon=True).start()

    def set_backend(self, backend_choice):
        # ollama means local runtime, anthropic means cloud API runtime.
        self.config["use_local"] = backend_choice == "ollama"
        print(f"Backend set to: {backend_choice}")

    def run_ai_request(self):
        try:
            use_blender = self.config.get("use_blender") and not self.config["use_local"]
            if use_blender:
                ok, _ = check_blender_connection()
                if not ok:
                    raise RuntimeError(
                        "Blender is not connected. Open Blender, enable the MCP addon, "
                        "and click Connect (port 9876)."
                    )
                response = get_tutor_response(self.config, user_context=self.user_context)
            else:
                response = get_response(self.config, user_context=self.user_context)
            self.after(0, lambda: self.show_response(response))
        except Exception as e:
            error_text = f"Error: {e}"
            self.after(0, lambda msg=error_text: self.show_response(msg))

    def show_response(self, text):
        self.controls_panel.set_response(text)
        self.controls_panel.set_loading(False)

    def get_monitor(self):
        with mss.MSS() as sct:
            return sct.monitors[self.monitor_index]

    def position_panel(self):
        mon = self.get_monitor()
        x = mon["left"] + mon["width"] - self.panel_width
        y = mon["top"]
        self.geometry(f"{self.panel_width}x{self.panel_height}+{x}+{y}")

    def exit_app(self):
        self.destroy()

    def minimize_app(self):
        self.iconify()