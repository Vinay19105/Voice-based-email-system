import customtkinter as ctk
from bridge import GUI_LOG_QUEUE, GUI_COMMAND_QUEUE, INPUT_QUEUE

ctk.set_appearance_mode("dark")

# ---- palette ----
BG = "#2A0664"
SURFACE = "#1C1E17"
SURFACE_RAISED = "#44540E"
BORDER = "#33352A"
TEXT = "#EDEAE1"
TEXT_MUTED = "#8B8A7E"
AMBER = "#E8A33D"
AMBER_DIM = "#4A3A1E"
TEAL = "#3FA796"
TEAL_DIM = "#1E3B36"
RED = "#C4574A"

FONT_HEAD = ("Segoe UI Semibold", 18)
FONT_LABEL = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 11)
FONT_MONO_SMALL = ("Consolas", 10)


class VoiceEmailGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Voice E-Mail System")
        self.root.geometry("1180x760")
        self.root.configure(fg_color=BG)

        self.mode = "voice"
        self.logged_in = False
        self.user_email = ""
        self.status_state = "idle"
        self.language = "english"
        self.emails = []          # last EMAIL_LIST payload
        self.email_scope = "unseen"
        self.open_email = None    # last EMAIL_OPENED payload
        self.contacts = {}

        self._build_layout()
        self.root.after(120, self.poll_queues)

    # ---------------------------------------------------------------- layout
    def _build_layout(self):
        self._build_header()

        body = ctk.CTkFrame(self.root, fg_color=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=3)
        body.grid_columnconfigure(2, weight=2)
        body.grid_rowconfigure(0, weight=1)

        self._build_inbox_panel(body)
        self._build_center_panel(body)
        self._build_side_panel(body)

    def _build_header(self):
        header = ctk.CTkFrame(self.root, fg_color=BG, height=64)
        header.pack(fill="x", padx=16, pady=(16, 8))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="y")

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")

        self.status_dot = ctk.CTkLabel(
            title_row, text="●", text_color=TEXT_MUTED, font=("Segoe UI", 16)
        )
        self.status_dot.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(title_row, text="Voice Mail", font=FONT_HEAD, text_color=TEXT).pack(
            side="left"
        )

        self.status_line = ctk.CTkLabel(
            left, text="idle — waiting for a command", font=FONT_SMALL, text_color=TEXT_MUTED
        )
        self.status_line.pack(anchor="w", pady=(2, 0))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", fill="y")

        self.login_badge = ctk.CTkLabel(
            right, text="logged out", font=FONT_SMALL, text_color=TEXT_MUTED,
            fg_color=SURFACE_RAISED, corner_radius=6, padx=10, pady=4,
        )
        self.login_badge.pack(side="right", padx=(8, 0))

        self.mode_badge = ctk.CTkLabel(
            right, text="mode: voice", font=FONT_SMALL, text_color=AMBER,
            fg_color=AMBER_DIM, corner_radius=6, padx=10, pady=4,
        )
        self.mode_badge.pack(side="right", padx=(8, 0))

        self.language_badge = ctk.CTkLabel(
            right, text="language: english", font=FONT_SMALL, text_color=TEAL,
            fg_color=TEAL_DIM, corner_radius=6, padx=10, pady=4,
        )
        self.language_badge.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            right, text="Voice", width=64, fg_color=SURFACE_RAISED, hover_color=BORDER,
            text_color=TEXT, command=lambda: self._request_mode("voice"),
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            right, text="Typing", width=64, fg_color=SURFACE_RAISED, hover_color=BORDER,
            text_color=TEXT, command=lambda: self._request_mode("typing"),
        ).pack(side="right")

    def _request_mode(self, mode):
        GUI_COMMAND_QUEUE.put({"action": "SET_MODE", "mode": mode})
        INPUT_QUEUE.put(f"switch to {mode}")

    # ---------------------------------------------------------- inbox panel
    def _build_inbox_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=10, width=280)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        panel.grid_propagate(False)

        ctk.CTkLabel(
            panel, text="INBOX", font=("Segoe UI Semibold", 11), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=14, pady=(14, 6))

        self.inbox_count_label = ctk.CTkLabel(
            panel, text="no messages fetched yet", font=FONT_SMALL, text_color=TEXT_MUTED
        )
        self.inbox_count_label.pack(anchor="w", padx=14, pady=(0, 4))

        self.inbox_scope_label = ctk.CTkLabel(
            panel, text="", font=FONT_SMALL, text_color=TEAL
        )
        self.inbox_scope_label.pack(anchor="w", padx=14, pady=(0, 8))

        self.inbox_scroll = ctk.CTkScrollableFrame(
            panel, fg_color="transparent", scrollbar_button_color=BORDER
        )
        self.inbox_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _render_inbox(self):
        for child in self.inbox_scroll.winfo_children():
            child.destroy()

        if not self.emails:
            ctk.CTkLabel(
                self.inbox_scroll, text="Say \"read email\" to fetch your inbox.",
                font=FONT_SMALL, text_color=TEXT_MUTED, wraplength=220, justify="left",
            ).pack(anchor="w", padx=6, pady=6)
            return

        for item in self.emails:
            is_open = self.open_email and self.open_email.get("index") == item["index"]
            row = ctk.CTkFrame(
                self.inbox_scroll,
                fg_color=AMBER_DIM if is_open else SURFACE_RAISED,
                corner_radius=8,
            )
            row.pack(fill="x", pady=3)

            header_row = ctk.CTkFrame(row, fg_color="transparent")
            header_row.pack(fill="x", padx=10, pady=(8, 0))

            ctk.CTkLabel(
                header_row, text=str(item["index"]), font=FONT_MONO_SMALL,
                text_color=AMBER if is_open else TEXT_MUTED, width=18,
            ).pack(side="left")

            ctk.CTkLabel(
                header_row, text=item.get("from") or "(unknown sender)", font=FONT_LABEL,
                text_color=TEXT, anchor="w",
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                row, text=item.get("subject") or "(no subject)", font=FONT_SMALL,
                text_color=TEXT_MUTED, anchor="w", wraplength=230, justify="left",
            ).pack(anchor="w", padx=10, pady=(2, 8))

    # --------------------------------------------------------- center panel
    def _build_center_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.grid(row=0, column=1, sticky="nsew", padx=(0, 12))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # -- reader --
        reader = ctk.CTkFrame(panel, fg_color=SURFACE_RAISED, corner_radius=10)
        reader.grid(row=0, column=0, sticky="new", pady=(0, 12))

        ctk.CTkLabel(
            reader, text="OPEN MESSAGE", font=("Segoe UI Semibold", 11), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(14, 4))

        self.reader_meta = ctk.CTkLabel(
            reader, text="Nothing open yet.", font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w"
        )
        self.reader_meta.pack(anchor="w", padx=16)

        self.reader_subject = ctk.CTkLabel(
            reader, text="", font=("Segoe UI Semibold", 14), text_color=TEXT,
            anchor="w", wraplength=520, justify="left",
        )
        self.reader_subject.pack(anchor="w", padx=16, pady=(6, 4))

        self.reader_body = ctk.CTkLabel(
            reader, text="", font=FONT_LABEL, text_color=TEXT, anchor="w",
            wraplength=520, justify="left",
        )
        self.reader_body.pack(anchor="w", padx=16, pady=(0, 16))

        # -- transcript --
        transcript_panel = ctk.CTkFrame(panel, fg_color=SURFACE, corner_radius=10)
        transcript_panel.grid(row=1, column=0, sticky="nsew")
        transcript_panel.grid_rowconfigure(1, weight=1)
        transcript_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            transcript_panel, text="TRANSCRIPT", font=("Segoe UI Semibold", 11),
            text_color=TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        self.transcript_box = ctk.CTkTextbox(
            transcript_panel, fg_color=BG, text_color=TEXT, font=FONT_MONO,
            wrap="word", corner_radius=8,
        )
        self.transcript_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.transcript_box.configure(state="disabled")

        input_row = ctk.CTkFrame(transcript_panel, fg_color="transparent")
        input_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        input_row.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            input_row, placeholder_text="Type a command (typing mode) and press Enter…",
            fg_color=SURFACE_RAISED, border_color=BORDER, text_color=TEXT,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry.bind("<Return>", self._submit_text)

        ctk.CTkButton(
            input_row, text="Send", width=70, fg_color=TEAL_DIM, hover_color=TEAL_DIM,
            text_color=TEAL, border_color=TEAL, border_width=1, command=self._submit_text,
        ).grid(row=0, column=1)

    def _submit_text(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._log(f"you  {text}")
        INPUT_QUEUE.put(text)

    # ----------------------------------------------------------- side panel
    def _build_side_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent", width=260)
        panel.grid(row=0, column=2, sticky="nsew")
        panel.grid_propagate(False)

        # -- listening indicator --
        mic_panel = ctk.CTkFrame(panel, fg_color=SURFACE_RAISED, corner_radius=10)
        mic_panel.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            mic_panel, text="ENGINE STATE", font=("Segoe UI Semibold", 11), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(14, 6))

        self.mic_state_label = ctk.CTkLabel(
            mic_panel, text="idle", font=("Segoe UI Semibold", 16), text_color=TEXT_MUTED
        )
        self.mic_state_label.pack(anchor="w", padx=16, pady=(0, 14))

        # -- last email sent --
        sent_panel = ctk.CTkFrame(panel, fg_color=SURFACE_RAISED, corner_radius=10)
        sent_panel.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            sent_panel, text="LAST SENT", font=("Segoe UI Semibold", 11), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(14, 6))

        self.sent_label = ctk.CTkLabel(
            sent_panel, text="Nothing sent yet.", font=FONT_SMALL, text_color=TEXT_MUTED,
            anchor="w", wraplength=200, justify="left",
        )
        self.sent_label.pack(anchor="w", padx=16, pady=(0, 14))

        # -- contacts --
        contacts_panel = ctk.CTkFrame(panel, fg_color=SURFACE, corner_radius=10)
        contacts_panel.pack(fill="both", expand=True)

        ctk.CTkLabel(
            contacts_panel, text="CONTACTS", font=("Segoe UI Semibold", 11), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(14, 6))

        self.contacts_scroll = ctk.CTkScrollableFrame(
            contacts_panel, fg_color="transparent", scrollbar_button_color=BORDER
        )
        self.contacts_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _render_contacts(self):
        for child in self.contacts_scroll.winfo_children():
            child.destroy()

        if not self.contacts:
            ctk.CTkLabel(
                self.contacts_scroll, text="No saved contacts yet.", font=FONT_SMALL,
                text_color=TEXT_MUTED,
            ).pack(anchor="w", padx=6, pady=6)
            return

        for name, addr in self.contacts.items():
            row = ctk.CTkFrame(self.contacts_scroll, fg_color=SURFACE_RAISED, corner_radius=6)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=name, font=FONT_LABEL, text_color=TEXT, anchor="w").pack(
                anchor="w", padx=10, pady=(6, 0)
            )
            ctk.CTkLabel(
                row, text=addr, font=FONT_MONO_SMALL, text_color=TEXT_MUTED, anchor="w"
            ).pack(anchor="w", padx=10, pady=(0, 6))

    # ------------------------------------------------------------- logging
    def _log(self, text):
        self.transcript_box.configure(state="normal")
        self.transcript_box.insert("end", text + "\n")
        self.transcript_box.see("end")
        self.transcript_box.configure(state="disabled")

    # ----------------------------------------------------------- queue loop
    def poll_queues(self):
        while not GUI_LOG_QUEUE.empty():
            raw = GUI_LOG_QUEUE.get_nowait()
            tag = "app "
            text = raw
            if raw.startswith("SYSTEM:"):
                tag, text = "app ", raw[len("SYSTEM:"):].strip()
            elif raw.startswith("USER"):
                tag, text = "you ", raw.split(":", 1)[-1].strip()
            self._log(f"{tag} {text}")

        while not GUI_COMMAND_QUEUE.empty():
            self._handle_event(GUI_COMMAND_QUEUE.get_nowait())

        self.root.after(120, self.poll_queues)

    def _handle_event(self, event):
        action = event.get("action")

        if action == "SET_MODE":
            self.mode = event.get("mode", self.mode)
            self.mode_badge.configure(text=f"mode: {self.mode}")

        elif action == "LOGIN_SUCCESS":
            self.logged_in = True
            self.user_email = event.get("email", "")
            self.login_badge.configure(
                text=f"logged in — {self.user_email}" if self.user_email else "logged in",
                text_color=TEAL, fg_color=TEAL_DIM,
            )

        elif action == "LOGOUT":
            self.logged_in = False
            self.login_badge.configure(text="logged out", text_color=TEXT_MUTED, fg_color=SURFACE_RAISED)

        elif action == "EMAIL_COUNT":
            self.inbox_count_label.configure(text=f"{event.get('count', 0)} messages")
            scope = event.get("scope", "unseen")
            scope_text = {"unseen": "showing: unread", "seen": "showing: previously read", "all": "showing: all mail"}.get(scope, "")
            self.inbox_scope_label.configure(text=scope_text)

        elif action == "EMAIL_LIST":
            self.emails = event.get("emails", [])
            self.email_scope = event.get("scope", "unseen")
            self._render_inbox()

        elif action == "LANGUAGE_CHANGED":
            self.language = event.get("language", "english")
            self.language_badge.configure(text=f"language: {self.language}")

        elif action == "EMAIL_OPENED":
            self.open_email = event
            self.reader_meta.configure(
                text=f"From {event.get('from', '')} · message {event.get('index', '?')}"
            )
            self.reader_subject.configure(text=event.get("subject", ""))
            body = (event.get("body") or "").strip()
            self.reader_body.configure(text=body[:600] if body else "(empty body)")
            self._render_inbox()

        elif action == "EMAIL_SENT":
            to = event.get("to", "")
            subject = event.get("subject", "")
            body = event.get("body", "")
            summary = f"To: {to}\nSubject: {subject}\n\n{body[:200]}"
            self.sent_label.configure(text=summary)

        elif action == "CONTACTS_UPDATED":
            self.contacts = event.get("contacts", {})
            self._render_contacts()

        elif action == "VOICE_REGISTERED":
            self._log("app  voice profile registered")

        elif action == "WAKEWORD":
            self._log("app  wake word detected, access granted")

        elif action == "STATUS":
            state = event.get("state", "idle")
            self.status_state = state
            if state == "listening":
                self.status_dot.configure(text_color=AMBER)
                self.status_line.configure(text="listening…", text_color=AMBER)
                self.mic_state_label.configure(text="listening", text_color=AMBER)
            elif state == "speaking":
                self.status_dot.configure(text_color=TEAL)
                self.status_line.configure(text="speaking…", text_color=TEAL)
                self.mic_state_label.configure(text="speaking", text_color=TEAL)
            else:
                self.status_dot.configure(text_color=TEXT_MUTED)
                self.status_line.configure(text="idle — waiting for a command", text_color=TEXT_MUTED)
                self.mic_state_label.configure(text="idle", text_color=TEXT_MUTED)


def launch_gui():
    root = ctk.CTk()
    VoiceEmailGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
