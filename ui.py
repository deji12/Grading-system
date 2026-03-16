import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from formatter import format_user_input
import threading    
from utils import (
    load_config, create_required_folders, 
    save_formatted_data
)
from grade_calculations import execute_calculations

class BeautifulSchoolSessionForm:
    def __init__(self, root):
        create_required_folders()
        self.config = load_config()
        self.root = root
        self.root.title("School Session Form")
        self.root.geometry("720x600")
        self.root.minsize(600, 450)

        # Configure main grid (1 column, 1 row, expand)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Session data
        self.sessions = [
            "2020/2021", "2021/2022", "2022/2023",
            "2023/2024", "2024/2025", "2025/2026"
        ]
        self.terms = ["First", "Second", "Third"]

        # ---------- Main container (card) ----------
        self.mainframe = ctk.CTkFrame(
            root,
            corner_radius=20,
            fg_color=("white", "#2b2b2b")  # light/dark adaptive
        )
        self.mainframe.grid(row=0, column=0, padx=25, pady=(15, 25), sticky="nsew")
        self.mainframe.grid_columnconfigure(0, weight=1)
        self.mainframe.grid_rowconfigure(2, weight=1)   # text area row expands

        # ---------- Header with accent bar ----------
        self.header_frame = ctk.CTkFrame(
            self.mainframe,
            height=50,
            corner_radius=15,
            fg_color="transparent"
        )
        self.header_frame.grid(row=0, column=0, pady=(5, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="School Session Form",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color=("#1e3c72", "#d0e0ff")  # dark blue / light blue
        )
        self.header_label.grid(row=0, column=0, padx=15, pady=5, sticky="w")

        # Accent line (a simple separator)
        self.separator = ctk.CTkFrame(
            self.mainframe,
            height=3,
            corner_radius=2,
            fg_color="#0078d4"
        )
        self.separator.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="ew")

        # ---------- Notes label ----------
        self.notes_label = ctk.CTkLabel(
            self.mainframe,
            text="Notes",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self.notes_label.grid(row=2, column=0, padx=15, pady=(0, 5), sticky="w")

        # ---------- Text area ----------
        self.text_area = ctk.CTkTextbox(
            self.mainframe,
            wrap="word",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=12,
            border_width=1,
            border_color="#a0a0a0"
        )
        self.text_area.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="nsew")

        # ---------- Controls row (session + term) ----------
        self.controls_frame = ctk.CTkFrame(self.mainframe, fg_color="transparent")
        self.controls_frame.grid(row=4, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.controls_frame.grid_columnconfigure(1, weight=1)   # spacer
        self.controls_frame.grid_columnconfigure(3, weight=0)

        # Session dropdown
        self.session_label = ctk.CTkLabel(
            self.controls_frame,
            text="Session",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.session_label.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.session_combo = ctk.CTkComboBox(
            self.controls_frame,
            values=self.sessions,
            width=210,
            corner_radius=10,
            state="readonly",
            dropdown_font=ctk.CTkFont(size=12),
            font=ctk.CTkFont(size=12)
        )
        self.session_combo.grid(row=0, column=1, padx=(0, 5), sticky="w")
        self.session_combo.set(self.sessions[-1])

        # Add session button (with plus symbol)
        self.add_session_btn = ctk.CTkButton(
            self.controls_frame,
            text="➕",                # Unicode heavy plus sign
            width=40,
            corner_radius=10,
            fg_color="#0078d4",
            hover_color="#005a9e",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.open_add_session_popup
        )
        self.add_session_btn.grid(row=0, column=2, padx=(0, 25), sticky="w")

        # Term dropdown
        self.term_label = ctk.CTkLabel(
            self.controls_frame,
            text="Term",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.term_label.grid(row=0, column=3, padx=(0, 10), sticky="w")

        self.term_combo = ctk.CTkComboBox(
            self.controls_frame,
            values=self.terms,
            width=150,
            corner_radius=10,
            state="readonly",
            dropdown_font=ctk.CTkFont(size=12),
            font=ctk.CTkFont(size=12)
        )
        self.term_combo.grid(row=0, column=4, sticky="w")
        self.term_combo.set(self.terms[0])

        # ---------- Bottom row (submit + dark mode switch) ----------
        self.bottom_frame = ctk.CTkFrame(self.mainframe, fg_color="transparent")
        self.bottom_frame.grid(row=5, column=0, padx=15, pady=(0, 10), sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        # Submit button (prominent)
        self.submit_btn = ctk.CTkButton(
            self.bottom_frame,
            text="Submit",
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=12,
            height=45,
            width=200,
            fg_color="#0078d4",
            hover_color="#005a9e",
            command=self.submit
        )
        self.submit_btn.grid(row=0, column=0, padx=(0, 10), sticky="w")

        # Dark mode switch (modern)
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.dark_mode_switch = ctk.CTkSwitch(
            self.bottom_frame,
            text="Dark Mode",
            font=ctk.CTkFont(size=12),
            variable=self.dark_mode_var,
            command=self.toggle_appearance,
            progress_color="#0078d4",
            button_color="#0078d4",
            button_hover_color="#005a9e"
        )
        self.dark_mode_switch.grid(row=0, column=1, padx=10, sticky="e")

    def toggle_appearance(self):
        """Switch between light and dark mode."""
        if self.dark_mode_var.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def open_add_session_popup(self):
        """Opens a modern popup to add a new session."""
        popup = ctk.CTkToplevel(self.root)
        popup.title("Add New Session")
        popup.geometry("360x200")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.focus_set()

        # Center popup
        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (360 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (200 // 2)
        popup.geometry(f"+{x}+{y}")

        # Instruction
        label = ctk.CTkLabel(
            popup,
            text="Enter new session (e.g., 2026/2027):",
            font=ctk.CTkFont(size=13)
        )
        label.pack(pady=(20, 5))

        # Entry
        entry_var = tk.StringVar()
        entry = ctk.CTkEntry(
            popup,
            textvariable=entry_var,
            width=260,
            corner_radius=10,
            placeholder_text="e.g. 2026/2027"
        )
        entry.pack(pady=5, padx=20)
        entry.focus()

        # Error label
        error_label = ctk.CTkLabel(popup, text="", text_color="red", font=ctk.CTkFont(size=11))
        error_label.pack()

        def add_session():
            new_session = entry_var.get().strip()
            if not new_session:
                error_label.configure(text="Please enter a session.")
                return
            if new_session in self.sessions:
                error_label.configure(text="Session already exists.")
                return
            self.sessions.append(new_session)
            self.session_combo.configure(values=self.sessions)
            self.session_combo.set(new_session)
            popup.destroy()

        # Add button
        add_btn = ctk.CTkButton(
            popup,
            text="Add Session",
            corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#0078d4",
            hover_color="#005a9e",
            command=add_session
        )
        add_btn.pack(pady=10)

        popup.bind('<Return>', lambda event: add_session())

    def submit(self):
        """Show a confirmation dialog with scrollable preview before final submission."""
        notes = self.text_area.get("1.0", tk.END).strip()
        session = self.session_combo.get()
        term = self.term_combo.get()
        
        # Create confirmation dialog
        confirm_dialog = ctk.CTkToplevel(self.root)
        confirm_dialog.title("Confirm Your Input")
        confirm_dialog.geometry("500x450")
        confirm_dialog.resizable(True, True)
        confirm_dialog.minsize(450, 400)
        
        # Make it modal
        confirm_dialog.transient(self.root)
        confirm_dialog.grab_set()
        confirm_dialog.focus_set()
        
        # Center the dialog
        confirm_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (450 // 2)
        confirm_dialog.geometry(f"+{x}+{y}")
        
        # Configure grid for the dialog
        confirm_dialog.grid_columnconfigure(0, weight=1)
        confirm_dialog.grid_rowconfigure(1, weight=1)  # Preview area expands
        
        # Header with icon and title
        header_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="ew")
        header_frame.grid_columnconfigure(1, weight=1)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text="🔍 Please Review Your Input",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1e3c72", "#d0e0ff")
        )
        header_label.grid(row=0, column=0, sticky="w")
        
        # Preview area with scrollable text
        preview_frame = ctk.CTkFrame(confirm_dialog)
        preview_frame.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="nsew")
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=1)
        
        # Scrollable text widget for preview
        preview_text = ctk.CTkTextbox(
            preview_frame,
            wrap="word",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=10,
            border_width=1,
            border_color="#a0a0a0"
        )
        preview_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Format the preview content nicely
        preview_content = f"""
📋 SESSION INFORMATION:
• Session: {session}
• Term: {term}

📝 NOTES:
{'-' * 50}
{notes if notes else "(No notes entered)"}
{'-' * 50}

Please confirm that all information above is correct.
        """
        
        preview_text.insert("1.0", preview_content)
        preview_text.configure(state="disabled")  # Make read-only
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="✗ Cancel",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10,
            height=40,
            fg_color="#6c757d",
            hover_color="#5a6268",
            command=confirm_dialog.destroy
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 10), sticky="e")
        
        # Confirm button
        def confirm_and_submit():
            """Called when user confirms the input."""
            confirm_dialog.destroy()
            
            # Now process the actual submission
            self.process_submission(notes, session, term)
        
        confirm_btn = ctk.CTkButton(
            buttons_frame,
            text="✓ Confirm & Submit",
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=10,
            height=40,
            fg_color="#28a745",  # Green for confirmation
            hover_color="#218838",
            command=confirm_and_submit
        )
        confirm_btn.grid(row=0, column=1, padx=(10, 0), sticky="w")
        
        # Bind Enter key to confirm
        confirm_dialog.bind('<Return>', lambda event: confirm_and_submit())
        # Bind Escape key to cancel
        confirm_dialog.bind('<Escape>', lambda event: confirm_dialog.destroy())

    def process_submission(self, notes, session, term):
        """Process the confirmed submission with loading animation (non-blocking)."""
        
        # Create loading dialog
        loading_dialog = ctk.CTkToplevel(self.root)
        loading_dialog.title("Processing")
        loading_dialog.geometry("300x150")
        loading_dialog.resizable(False, False)
        loading_dialog.transient(self.root)
        loading_dialog.grab_set()
        
        # Center the loading dialog
        loading_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (150 // 2)
        loading_dialog.geometry(f"+{x}+{y}")
        
        # Loading spinner
        spinner = ctk.CTkProgressBar(loading_dialog, mode="indeterminate", width=200)
        spinner.pack(pady=(30, 10))
        spinner.start()
        
        # Loading text
        loading_label = ctk.CTkLabel(
            loading_dialog, 
            text="Processing your request...",
            font=ctk.CTkFont(size=13)
        )
        loading_label.pack()
        
        # Variable to store result
        result = {"data": None, "error": None}
        
        def run_api_call():
            """Run the API call in a separate thread."""
            try:
                # Call your formatting function
                formatted_data = format_user_input(notes, self.config['app']['openai_api_key'])
                result["data"] = formatted_data
                save_formatted_data(formatted_data, execute_calculations)
            except Exception as e:
                result["error"] = str(e)
            finally:
                # Schedule the UI update on the main thread
                loading_dialog.after(0, on_api_complete)
        
        def on_api_complete():
            """Called when API call is complete (runs on main thread)."""
            # Close loading dialog
            loading_dialog.destroy()
            
            if result["error"]:
                # Show error message
                messagebox.showerror(
                    "Error",
                    f"An error occurred while processing:\n\n{result['error']}"
                )
            else:
                # Show success message
                self.show_success_dialog(result["data"])
        
        # Start the API call in a background thread
        thread = threading.Thread(target=run_api_call)
        thread.daemon = True  # Thread will close when main program closes
        thread.start()

    def show_success_dialog(self, formatted_data):
        """Show success message."""
        success_dialog = ctk.CTkToplevel(self.root)
        success_dialog.title("Success")
        success_dialog.geometry("300x150")
        success_dialog.transient(self.root)
        success_dialog.grab_set()
        
        # Center success dialog
        success_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (150 // 2)
        success_dialog.geometry(f"+{x}+{y}")
        
        # Success message
        ctk.CTkLabel(
            success_dialog,
            text="✅",
            font=ctk.CTkFont(size=48)
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            success_dialog,
            text="Form submitted successfully!",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack()
        
        ctk.CTkButton(
            success_dialog,
            text="OK",
            width=100,
            command=success_dialog.destroy
        ).pack(pady=15)
        
        # Auto-close after 2 seconds
        success_dialog.after(2000, success_dialog.destroy)
        
        # Print to console
        print("\n" + "="*50)
        print("FORM SUBMITTED:")
        print(formatted_data)
        print("="*50 + "\n")