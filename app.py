import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List, Dict, Type
from pw_encryptor import (
    encrypt_files_password_mode, decrypt_files_password_mode,
    encrypt_folder_password_mode, decrypt_folder_password_mode
)
from share import generate_rsa_keypair, create_share_package, extract_share_package

# --- Global Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class FrameBase(ctk.CTkFrame):
    """Base class for all functional frames."""
    def __init__(self, master, title: str, icon: str):
        super().__init__(master, corner_radius=10)
        self.title = title
        self.icon = icon
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(99, weight=1) # Filler row

        # Title Label
        title_font = ctk.CTkFont(size=24, weight="bold")
        ctk.CTkLabel(self, text=f"{self.icon} {self.title}", font=title_font).grid(
            row=0, column=0, padx=20, pady=(20, 10), sticky="w"
        )
        ctk.CTkFrame(self, height=2, fg_color="gray50").grid(
            row=1, column=0, padx=20, pady=(0, 15), sticky="ew"
        )

# --- Frame 1: Password Encrypt/Decrypt ---

class PasswordFrame(FrameBase):
    def __init__(self, master, app):
        super().__init__(master, title="Password Encrypt/Decrypt", icon="🔒")
        self.app = app
        self.pw_process_type = ctk.StringVar(value="File")
        self._build_ui()

    def _build_ui(self):
        # 1. Password Row
        password_section = ctk.CTkFrame(self, fg_color="transparent")
        password_section.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        password_section.columnconfigure(1, weight=1)

        ctk.CTkLabel(password_section, text="Password:").grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.pw_entry = ctk.CTkEntry(password_section, show="*")
        self.pw_entry.grid(row=0, column=1, padx=10, sticky="ew")
        
        self.pw_show = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(password_section, text="Show", variable=self.pw_show, 
                        command=lambda: self.pw_entry.configure(show="" if self.pw_show.get() else "*")).grid(row=0, column=2, padx=10, sticky="e")

        # 2. File/Folder List
        ctk.CTkLabel(self, text="Selected Paths:").grid(row=3, column=0, padx=20, pady=(5, 0), sticky="w")
        self.pw_files_list = ctk.CTkTextbox(self, height=100, state="disabled", activate_scrollbars=True)
        self.pw_files_list.grid(row=4, column=0, padx=20, pady=6, sticky="ew")

        # 3. Path Selection and Mode
        selection_row = ctk.CTkFrame(self, fg_color="transparent")
        selection_row.grid(row=5, column=0, padx=20, pady=6, sticky="ew")
        selection_row.columnconfigure(0, weight=1)

        ctk.CTkButton(selection_row, text="➕ Add Files", command=self._pick_pw_files).pack(side="left", padx=5)
        ctk.CTkButton(selection_row, text="📁 Add Folder", command=self._pick_pw_folder).pack(side="left", padx=5)
        ctk.CTkButton(selection_row, text="🗑️ Clear List", command=self._clear_pw_list).pack(side="left", padx=5)

        ctk.CTkOptionMenu(selection_row, values=["File", "Folder"], variable=self.pw_process_type).pack(side="right", padx=5)
        ctk.CTkLabel(selection_row, text="Mode:").pack(side="right", padx=(20, 0))

        # 4. Action Buttons
        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=6, column=0, padx=20, pady=20, sticky="ew")
        action_row.columnconfigure((0, 1), weight=1)

        ctk.CTkButton(action_row, text="Encrypt (In-Place)", command=self._do_pw_encrypt, fg_color="#10B981").grid(row=0, column=0, padx=10, sticky="ew")
        ctk.CTkButton(action_row, text="Decrypt (In-Place)", command=self._do_pw_decrypt, fg_color="#F97316").grid(row=0, column=1, padx=10, sticky="ew")
        
        hint = ("Uses strong PBKDF2 for key derivation. Encrypting/decrypting is done directly on the original files.")
        ctk.CTkLabel(self, text=hint, wraplength=720, text_color="gray").grid(row=7, column=0, padx=20, pady=(0, 10), sticky="w")

    # --- Command Handlers ---

    def _update_textbox(self, paths: List[str]):
        self.pw_files_list.configure(state="normal")
        self.pw_files_list.delete("1.0", "end")
        for f in paths:
            self.pw_files_list.insert("end", f + "\n")
        self.pw_files_list.configure(state="disabled")

    def _pick_pw_files(self):
        files = filedialog.askopenfilenames(title="Choose files to encrypt/decrypt")
        if files:
            self.pw_process_type.set("File")
            self._update_textbox(list(files))

    def _pick_pw_folder(self):
        folder = filedialog.askdirectory(title="Choose a folder to encrypt/decrypt")
        if folder:
            self.pw_process_type.set("Folder")
            self._update_textbox([folder])

    def _clear_pw_list(self):
        self._update_textbox([])

    def _get_pw_input(self):
        pw = self.pw_entry.get().strip()
        files = self.pw_files_list.get("1.0", "end").strip().split('\n')
        paths = [p for p in files if p]
        if not pw or not paths:
            self.app.update_status("Error: Enter password and select path(s).", "red")
            return None, None
        return pw, paths

    def _do_pw_encrypt(self):
        pw, paths = self._get_pw_input()
        if not pw: return
        try:
            if self.pw_process_type.get() == "File":
                encrypt_files_password_mode(paths, pw)
                self.app.update_status(f"Success: Encrypted {len(paths)} file(s) (In-Place).", "#10B981")
            else:
                encrypt_folder_password_mode(paths[0], pw)
                self.app.update_status(f"Success: Encrypted folder: {paths[0]} (In-Place).", "#10B981")
        except Exception as e:
            self.app.update_status(f"Encryption Error: {e}", "red")

    def _do_pw_decrypt(self):
        pw, paths = self._get_pw_input()
        if not pw: return
        try:
            if self.pw_process_type.get() == "File":
                decrypt_files_password_mode(paths, pw)
                self.app.update_status(f"Success: Decrypted {len(paths)} file(s) (In-Place).", "#F97316")
            else:
                decrypt_folder_password_mode(paths[0], pw)
                self.app.update_status(f"Success: Decrypted folder: {paths[0]} (In-Place).", "#F97316")
        except Exception as e:
            self.app.update_status(f"Decryption Error: {e}. Check password or file integrity.", "red")


# --- Frame 2: Share (Send) ---

class ShareFrame(FrameBase):
    def __init__(self, master, app):
        super().__init__(master, title="Secure Share (Sender)", icon="📤")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # 1. Files to Share
        self.app.share_files_list_obj = [] # Reference for file list
        ctk.CTkLabel(self, text="1. Files to Encrypt & Share:").grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        
        file_list_row = ctk.CTkFrame(self, fg_color="transparent")
        file_list_row.grid(row=3, column=0, padx=20, pady=6, sticky="ew")
        file_list_row.columnconfigure(0, weight=1)
        
        self.share_files_textbox = ctk.CTkTextbox(file_list_row, height=80, state="disabled")
        self.share_files_textbox.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        file_buttons = ctk.CTkFrame(file_list_row, fg_color="transparent")
        file_buttons.grid(row=0, column=1, sticky="e")
        ctk.CTkButton(file_buttons, text="➕ Add Files", command=self._pick_share_files).pack(pady=3)
        ctk.CTkButton(file_buttons, text="🗑️ Clear", command=self._clear_share_list).pack(pady=3)

        # 2. Recipient's Public Key
        ctk.CTkLabel(self, text="2. Recipient's Public Key (.pem) - *Automatic Encryption*:").grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        key_row = ctk.CTkFrame(self, fg_color="transparent")
        key_row.grid(row=5, column=0, padx=20, pady=6, sticky="ew")
        key_row.columnconfigure(0, weight=1)
        self.share_pub_entry = ctk.CTkEntry(key_row, textvariable=self.app.share_recipient_pub_key)
        self.share_pub_entry.grid(row=0, column=0, padx=(0, 12), sticky="ew")
        ctk.CTkButton(key_row, text="Select Key", command=self._pick_share_pub_key).grid(row=0, column=1)
        
        # 3. Output Path
        ctk.CTkLabel(self, text="3. Output Folder for Secure Package (.sfs):").grid(row=6, column=0, padx=20, pady=(10, 0), sticky="w")
        output_row = ctk.CTkFrame(self, fg_color="transparent")
        output_row.grid(row=7, column=0, padx=20, pady=6, sticky="ew")
        output_row.columnconfigure(0, weight=1)
        self.share_output_entry = ctk.CTkEntry(output_row, textvariable=self.app.share_output_path)
        self.share_output_entry.grid(row=0, column=0, padx=(0, 12), sticky="ew")
        ctk.CTkButton(output_row, text="Select Folder", command=self._pick_share_output_folder).grid(row=0, column=1)
        
        # 4. Action Button
        ctk.CTkButton(self, text="🔑 Encrypt Files & Create .sfs Package (SEND)", command=self._do_share, fg_color="#3B82F6", height=40, font=ctk.CTkFont(size=16, weight="bold")).grid(row=8, column=0, padx=20, pady=20, sticky="ew")
        
        hint = ("This is End-to-End Encryption. The app automatically wraps the symmetric key with the recipient's "
                "Public Key, ensuring only they can decrypt the contents.")
        ctk.CTkLabel(self, text=hint, wraplength=720, text_color="gray").grid(row=9, column=0, padx=20, pady=(0, 10), sticky="w")

    # --- Command Handlers ---
    def _update_file_textbox(self, paths: List[str]):
        self.share_files_textbox.configure(state="normal")
        self.share_files_textbox.delete("1.0", "end")
        for f in paths:
            self.share_files_textbox.insert("end", f + "\n")
        self.share_files_textbox.configure(state="disabled")

    def _pick_share_files(self):
        files = filedialog.askopenfilenames(title="Choose files to share")
        if files:
            self.app.share_files_list_obj = list(files)
            self._update_file_textbox(self.app.share_files_list_obj)

    def _clear_share_list(self):
        self.app.share_files_list_obj = []
        self._update_file_textbox(self.app.share_files_list_obj)
        
    def _pick_share_pub_key(self):
        p = filedialog.askopenfilename(title="Select Recipient's Public Key (.pem)", filetypes=[("PEM Files", "*.pem")])
        if p:
            self.app.share_recipient_pub_key.set(p)

    def _pick_share_output_folder(self):
        p = filedialog.askdirectory(title="Choose folder to save .sfs package")
        if p:
            self.app.share_output_path.set(p)

    def _do_share(self):
        files = self.app.share_files_list_obj
        pub_key = self.app.share_recipient_pub_key.get().strip()
        output_folder = self.app.share_output_path.get().strip()
        
        if not files or not pub_key or not output_folder:
            self.app.update_status("Error: Select files, recipient key, and output folder.", "red")
            return

        try:
            output_path = create_share_package(files, pub_key, output_folder)
            self.app.update_status(f"Success: Package created at: {output_path}", "#3B82F6")
            self._clear_share_list()
        except Exception as e:
            self.app.update_status(f"Sharing Error: Failed to create package. {e}", "red")

# --- Frame 3: Receive (.sfs) ---

class ReceiveFrame(FrameBase):
    def __init__(self, master, app):
        super().__init__(master, title="Receive Secure Package (Receiver)", icon="📥")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # 1. .sfs File to Decrypt
        ctk.CTkLabel(self, text="1. Select Secure File Share Package (.sfs):").grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        r1 = ctk.CTkFrame(self, fg_color="transparent")
        r1.grid(row=3, column=0, padx=20, pady=6, sticky="ew")
        r1.columnconfigure(0, weight=1)
        ctk.CTkEntry(r1, textvariable=self.app.receive_sfs_file).grid(row=0, column=0, padx=(0, 12), sticky="ew")
        ctk.CTkButton(r1, text="Select .sfs", command=self._pick_receive_sfs).grid(row=0, column=1)

        # 2. Receiver's Private Key
        ctk.CTkLabel(self, text="2. Your Private Key (.pem) - *Automatic Decryption*:").grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        r2 = ctk.CTkFrame(self, fg_color="transparent")
        r2.grid(row=5, column=0, padx=20, pady=6, sticky="ew")
        r2.columnconfigure(0, weight=1)
        ctk.CTkEntry(r2, textvariable=self.app.receive_private_key).grid(row=0, column=0, padx=(0, 12), sticky="ew")
        ctk.CTkButton(r2, text="Select Key", command=self._pick_receive_priv_key).grid(row=0, column=1)
        
        # 3. Private Key Password
        pw_frame = ctk.CTkFrame(self, fg_color="transparent")
        pw_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        pw_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(pw_frame, text="3. Private Key Password (if set):").grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.receive_pw_entry = ctk.CTkEntry(pw_frame, textvariable=self.app.receive_private_key_pw, show="*")
        self.receive_pw_entry.grid(row=0, column=1, padx=10, sticky="ew")
        self.receive_pw_show = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(pw_frame, text="Show", variable=self.receive_pw_show, 
                        command=lambda: self.receive_pw_entry.configure(show="" if self.receive_pw_show.get() else "*")).grid(row=0, column=2, padx=10, sticky="e")

        # 4. Output Path for Decrypted Files
        ctk.CTkLabel(self, text="4. Output Folder for Decrypted Files:").grid(row=7, column=0, padx=20, pady=(10, 0), sticky="w")
        r4 = ctk.CTkFrame(self, fg_color="transparent")
        r4.grid(row=8, column=0, padx=20, pady=6, sticky="ew")
        r4.columnconfigure(0, weight=1)
        ctk.CTkEntry(r4, textvariable=self.app.receive_output_path).grid(row=0, column=0, padx=(0, 12), sticky="ew")
        ctk.CTkButton(r4, text="Select Folder", command=self._pick_receive_output_folder).grid(row=0, column=1)

        # 5. Action Button
        ctk.CTkButton(self, text="🔓 Decrypt .sfs Package (RECEIVE)", command=self._do_receive, fg_color="#F97316", height=40, font=ctk.CTkFont(size=16, weight="bold")).grid(row=9, column=0, padx=20, pady=20, sticky="ew")
        
        hint = ("This is the automatic decryption process. Your private key is used to unwrap the secret file key, "
                "allowing for seamless file retrieval.")
        ctk.CTkLabel(self, text=hint, wraplength=720, text_color="gray").grid(row=10, column=0, padx=20, pady=(0, 10), sticky="w")

    # --- Command Handlers ---
    def _pick_receive_sfs(self):
        p = filedialog.askopenfilename(title="Select .sfs Package", filetypes=[("Secure File Share", "*.sfs")])
        if p:
            self.app.receive_sfs_file.set(p)

    def _pick_receive_priv_key(self):
        p = filedialog.askopenfilename(title="Select Your Private Key (.pem)", filetypes=[("PEM Files", "*.pem")])
        if p:
            self.app.receive_private_key.set(p)

    def _pick_receive_output_folder(self):
        p = filedialog.askdirectory(title="Choose folder to save decrypted files")
        if p:
            self.app.receive_output_path.set(p)

    def _do_receive(self):
        sfs_path = self.app.receive_sfs_file.get().strip()
        priv_key = self.app.receive_private_key.get().strip()
        priv_pw = self.app.receive_private_key_pw.get().strip() or None
        output_folder = self.app.receive_output_path.get().strip()

        if not sfs_path or not priv_key or not output_folder:
            self.app.update_status("Error: Select .sfs file, private key, and output folder.", "red")
            return

        try:
            extract_share_package(sfs_path, priv_key, output_folder, private_key_password=priv_pw)
            self.app.update_status(f"Success: Files decrypted to: {output_folder}", "#F97316")
        except Exception as e:
            self.app.update_status(f"Decryption Error: Check key/password or file integrity. {e}", "red")

# --- Frame 4: Keys ---

class KeysFrame(FrameBase):
    def __init__(self, master, app):
        super().__init__(master, title="RSA Keypair Generator", icon="🔑")
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # 1. Save Folder
        ctk.CTkLabel(self, text="1. Save Folder for Keys:").grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        r1 = ctk.CTkFrame(self, fg_color="transparent")
        r1.grid(row=3, column=0, padx=20, pady=6, sticky="ew")
        r1.columnconfigure(0, weight=1)
        self.keys_save_entry = ctk.CTkEntry(r1, placeholder_text=os.path.join(os.path.expanduser("~"), "Desktop"))
        self.keys_save_entry.grid(row=0, column=0, padx=(0, 12), sticky="ew")
        ctk.CTkButton(r1, text="Browse", command=self._pick_keys_folder).grid(row=0, column=1)

        # 2. Base Key Name
        ctk.CTkLabel(self, text="2. Base Key Name (e.g., 'alice'):").grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        self.keys_name_entry = ctk.CTkEntry(self, placeholder_text="mykey")
        self.keys_name_entry.grid(row=5, column=0, padx=20, pady=6, sticky="w")

        # 3. Private Key Password
        pw_frame = ctk.CTkFrame(self, fg_color="transparent")
        pw_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        pw_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(pw_frame, text="3. Private Key Password (Optional, Recommended):").grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.keys_pw_entry = ctk.CTkEntry(pw_frame, show="*")
        self.keys_pw_entry.grid(row=0, column=1, padx=10, sticky="ew")
        self.keys_pw_show = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(pw_frame, text="Show", variable=self.keys_pw_show, 
                        command=lambda: self.keys_pw_entry.configure(show="" if self.keys_pw_show.get() else "*")).grid(row=0, column=2, padx=10, sticky="e")

        # 4. Action Button
        ctk.CTkButton(self, text="✨ Generate Keypair (RSA 2048)", command=self._do_gen_keys, fg_color="#1E40AF", height=40, font=ctk.CTkFont(size=16, weight="bold")).grid(row=7, column=0, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(self, text="Public Key (.pem) is for **sharing** with senders.", text_color="#10B981").grid(row=8, column=0, padx=20, pady=(0, 5), sticky="w")
        ctk.CTkLabel(self, text="Private Key (.pem) is for **receiving** and must be kept secret.", text_color="#F97316").grid(row=9, column=0, padx=20, pady=(0, 10), sticky="w")
        

    # --- Command Handlers ---
    def _pick_keys_folder(self):
        p = filedialog.askdirectory(title="Choose folder to save keys")
        if p:
            self.keys_save_entry.delete(0, "end")
            self.keys_save_entry.insert(0, p)

    def _do_gen_keys(self):
        save = self.keys_save_entry.get().strip() or os.path.join(os.path.expanduser("~"), "Desktop")
        name = self.keys_name_entry.get().strip() or "mykey"
        pw = self.keys_pw_entry.get().strip() or None
        
        try:
            pub_path, priv_path = generate_rsa_keypair(save, name, pw)
            self.app.update_status(f"Success: Keypair created. Public key at: {pub_path}", "#1E40AF")
            
            # Auto-populate the receive tab for convenience
            self.app.receive_private_key.set(priv_path)
            self.app.receive_private_key_pw.set(pw or "")
            
        except Exception as e:
            self.app.update_status(f"Key Generation Error: {e}", "red")


# --- Main Application ---

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🔐 Secure File Share Platform")
        self.geometry("900x680")
        self.minsize(800, 600)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Session variables
        self.share_files_list_obj: List[str] = [] # Files for sharing
        self.share_recipient_pub_key = ctk.StringVar(value="")
        self.share_output_path = ctk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop"))
        self.receive_sfs_file = ctk.StringVar(value="")
        self.receive_private_key = ctk.StringVar(value="")
        self.receive_private_key_pw = ctk.StringVar(value="")
        self.receive_output_path = ctk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "Decrypted_Files"))

        self.frames: Dict[str, FrameBase] = {}
        self._build_sidebar()
        self._build_main_frames()
        self._build_status_bar()
        
        self.show_frame("ShareFrame") # Default view

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="gray20")
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1) # Filler row

        # Logo/Title
        logo_font = ctk.CTkFont(size=20, weight="bold")
        ctk.CTkLabel(self.sidebar, text="Secure Share", font=logo_font).grid(row=0, column=0, padx=20, pady=(30, 10))
        
        # Navigation Buttons
        self.nav_buttons = [
            ("Share (Sender)", "📤", "ShareFrame"),
            ("Receive (.sfs)", "📥", "ReceiveFrame"),
            ("Keys Generator", "🔑", "KeysFrame"),
            ("Password Tools", "🔒", "PasswordFrame"),
        ]
        
        for i, (text, icon, name) in enumerate(self.nav_buttons):
            ctk.CTkButton(self.sidebar, text=f"{icon} {text}", command=lambda n=name: self.show_frame(n), 
                          fg_color="transparent", hover_color="gray30", anchor="w").grid(row=i + 1, column=0, padx=10, pady=5, sticky="ew")

        # Separator and Version
        ctk.CTkLabel(self.sidebar, text="v1.0.0", text_color="gray60").grid(row=10, column=0, pady=10)

    def _build_main_frames(self):
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color=self.cget("fg_color"))
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Frame definitions
        frame_classes: Dict[str, Type[FrameBase]] = {
            "ShareFrame": ShareFrame, 
            "ReceiveFrame": ReceiveFrame, 
            "KeysFrame": KeysFrame, 
            "PasswordFrame": PasswordFrame
        }
        
        for name, FrameClass in frame_classes.items():
            frame = FrameClass(self.container, self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar.grid(row=1, column=1, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready to secure your files.", text_color="gray70", padx=10)
        self.status_label.grid(row=0, column=0, sticky="w", pady=5)
        
    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()

    def update_status(self, message: str, color: str = "gray70"):
        """Updates the status bar with a message and color."""
        self.status_label.configure(text=message, text_color=color)
        
if __name__ == "__main__":
    app = App()
    app.mainloop()
