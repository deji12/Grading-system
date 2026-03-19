import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from formatter import format_user_input
import threading    
import os
from utils import (
    load_config, create_required_folders, 
    save_formatted_data, reset_grading_session
)
from grade_calculations import execute_calculations

# Set appearance and theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class BeautifulSchoolSessionForm:
    def __init__(self, root):
        create_required_folders()

        self.root = root
        self.root.title("School Session Form")
        
        try:
            self.config = load_config()
        except FileNotFoundError as e:
            # Config file missing - show error and don't create UI
            self.show_config_error_and_exit(str(e), "config")
            return
        except ValueError as e:
            # Invalid config or missing API key - show error and don't create UI
            self.show_config_error_and_exit(str(e), "config")
            return
        
        # Configure main grid (1 column, 1 row, expand)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

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

        # ---------- Bottom row (submit + reset + dark mode switch) ----------
        self.bottom_frame = ctk.CTkFrame(self.mainframe, fg_color="transparent")
        self.bottom_frame.grid(row=4, column=0, padx=15, pady=(0, 10), sticky="ew")
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

        # Check if classes directory exists and is not empty
        classes_dir = "classes"
        show_reset_button = os.path.exists(classes_dir) and len(os.listdir(classes_dir)) > 0

        # Reset button (red) - only shown if classes directory is not empty
        if show_reset_button:
            self.reset_btn = ctk.CTkButton(
                self.bottom_frame,
                text="Reset Session",
                font=ctk.CTkFont(size=13, weight="bold"),
                corner_radius=12,
                height=40,
                width=130,
                fg_color="#dc3545",  # Red color
                hover_color="#c82333",
                command=self.confirm_reset
            )
            self.reset_btn.grid(row=0, column=1, padx=(0, 10), sticky="w")

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
        self.dark_mode_switch.grid(row=0, column=2, padx=10, sticky="e")
        
        # NOW set the window to full screen/maximized after all UI elements are created
        self.root.after(10, self.maximize_window)  # Small delay to ensure proper rendering

    def maximize_window(self):
        """Set the window to maximized/full screen."""
        try:
            self.root.state('zoomed')  # Windows
        except:
            try:
                self.root.attributes('-fullscreen', True)  # Alternative for some systems
            except:
                pass  # Fall back to default size if both fail

    def toggle_appearance(self):
        """Switch between light and dark mode."""
        if self.dark_mode_var.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def confirm_reset(self):
        """Show confirmation dialog before resetting."""
        result = messagebox.askyesno(
            "Confirm Reset",
            "⚠️ WARNING: This will permanently delete ALL grading session data.\n\n"
            "This action cannot be undone. Are you sure you want to continue?",
            icon='warning'
        )
        
        if result:
            self.process_reset()

    def safe_destroy(self, widget):
        """Safely destroy a widget and handle any errors."""
        try:
            if widget and widget.winfo_exists():
                # Cancel any pending after callbacks
                try:
                    for after_id in getattr(widget, '_after_ids', []):
                        widget.after_cancel(after_id)
                except:
                    pass
                
                # Remove grab and withdraw before destroying
                try:
                    widget.grab_release()
                except:
                    pass
                
                # Destroy the widget
                widget.destroy()
        except:
            pass  # Ignore any errors during destruction

    def process_reset(self):
        """Process the reset with loading animation."""
        
        # Create loading dialog
        loading_dialog = ctk.CTkToplevel(self.root)
        loading_dialog.title("Resetting")
        loading_dialog.geometry("300x150")
        loading_dialog.resizable(False, False)
        loading_dialog.transient(self.root)
        loading_dialog.grab_set()
        
        # Center the loading dialog
        loading_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (150 // 2)
        loading_dialog.geometry(f"+{x}+{y}")
        
        # Configure dialog to prevent the title bar color issue
        loading_dialog.attributes('-alpha', 0.99)
        
        # Loading spinner
        spinner = ctk.CTkProgressBar(loading_dialog, mode="indeterminate", width=200)
        spinner.pack(pady=(30, 10))
        spinner.start()
        
        # Loading text
        loading_label = ctk.CTkLabel(
            loading_dialog, 
            text="Deleting grading session...",
            font=ctk.CTkFont(size=13)
        )
        loading_label.pack()
        
        # Variable to store result
        result = {"success": False, "error": None}
        
        # Flag to track if dialog is still active
        dialog_active = True
        
        def run_reset():
            """Run the reset in a separate thread."""
            try:
                # Call the reset function
                reset_grading_session()
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
            finally:
                # Schedule the UI update on the main thread
                if dialog_active:
                    loading_dialog.after(0, on_reset_complete)
        
        def on_reset_complete():
            """Called when reset is complete (runs on main thread)."""
            nonlocal dialog_active
            dialog_active = False
            
            # Cancel spinner animation
            try:
                if hasattr(spinner, '_after_id') and spinner._after_id:
                    loading_dialog.after_cancel(spinner._after_id)
            except:
                pass
            
            # Store reference to dialog before destroying
            dialog_to_destroy = loading_dialog
            
            # Schedule destruction with a tiny delay to allow any pending callbacks to complete
            def do_destroy():
                self.safe_destroy(dialog_to_destroy)
                
                # Now show result
                if result["error"]:
                    # Show error message
                    self.root.after(10, lambda: messagebox.showerror(
                        "Error",
                        f"An error occurred while resetting:\n\n{result['error']}"
                    ))
                else:
                    # Show success message
                    self.root.after(10, lambda: self.show_reset_success_dialog())
                    
                    # Refresh the UI to hide reset button if classes directory is now empty
                    self.root.after(20, self.refresh_reset_button)
            
            # Use after with a small delay to avoid the title bar color issue
            loading_dialog.after(50, do_destroy)
        
        # Start the reset in a background thread
        thread = threading.Thread(target=run_reset)
        thread.daemon = True
        thread.start()

    def show_reset_success_dialog(self):
        """Show success message for reset."""
        success_dialog = ctk.CTkToplevel(self.root)
        success_dialog.title("Success")
        success_dialog.geometry("300x150")
        success_dialog.resizable(False, False)
        success_dialog.transient(self.root)
        success_dialog.grab_set()
        
        # Center success dialog
        success_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (150 // 2)
        success_dialog.geometry(f"+{x}+{y}")
        
        # Configure dialog to prevent the title bar color issue
        success_dialog.attributes('-alpha', 0.99)
        
        # Success message
        ctk.CTkLabel(
            success_dialog,
            text="✅",
            font=ctk.CTkFont(size=48)
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            success_dialog,
            text="Grading session deleted successfully!",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack()
        
        # Store the after ID so we can cancel it if needed
        after_id = None
        
        def close_dialog():
            """Close the dialog and cancel any pending callbacks."""
            nonlocal after_id
            if after_id:
                try:
                    success_dialog.after_cancel(after_id)
                except:
                    pass
            self.safe_destroy(success_dialog)
        
        ctk.CTkButton(
            success_dialog,
            text="OK",
            width=100,
            command=close_dialog
        ).pack(pady=15)
        
        # Auto-close after 2 seconds - store the ID
        after_id = success_dialog.after(2000, close_dialog)
        
        # Make sure to clean up if dialog is closed manually
        def on_closing():
            nonlocal after_id
            if after_id:
                try:
                    success_dialog.after_cancel(after_id)
                except:
                    pass
            self.safe_destroy(success_dialog)
        
        success_dialog.protocol("WM_DELETE_WINDOW", on_closing)
        
        print("\n" + "="*50)
        print("GRADING SESSION RESET")
        print("All grading data has been deleted.")
        print("="*50 + "\n")

    def refresh_reset_button(self):
        """Check if reset button should still be visible and update UI accordingly."""
        classes_dir = "classes"
        show_reset_button = os.path.exists(classes_dir) and len(os.listdir(classes_dir)) > 0
        
        # Check if reset button exists and if it should be shown/hidden
        if hasattr(self, 'reset_btn'):
            if not show_reset_button:
                # Hide and destroy the reset button if it exists
                self.reset_btn.grid_forget()
                self.reset_btn.destroy()
                delattr(self, 'reset_btn')

    def submit(self):
        """Show a confirmation dialog with scrollable preview before final submission."""
        notes = self.text_area.get("1.0", tk.END).strip()
        
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
        
        # Configure dialog to prevent title bar issues
        confirm_dialog.attributes('-alpha', 0.99)
        
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
📝 NOTES:
{'-' * 50}
{notes if notes else "(No notes entered)"}
{'-' * 50}

Please confirm that the information above is correct.
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
            command=lambda: self.safe_destroy(confirm_dialog)
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 10), sticky="e")
        
        # Confirm button
        def confirm_and_submit():
            """Called when user confirms the input."""
            self.safe_destroy(confirm_dialog)
            
            # Now process the actual submission
            self.process_submission(notes)
        
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
        confirm_dialog.bind('<Escape>', lambda event: self.safe_destroy(confirm_dialog))

    def process_submission(self, notes):
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
        
        # Configure dialog to prevent title bar issues
        loading_dialog.attributes('-alpha', 0.99)
        
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
        result = {"data": None, "error": None, "error_type": None}
        
        # Flag to track if dialog is still active
        dialog_active = True
        
        def run_api_call():
            """Run the API call in a separate thread."""
            try:
                # Check if API key is configured
                api_key = self.config.get('app', {}).get('openai_api_key')
                if not api_key or api_key == "YOUR_API_KEY_HERE":
                    result["error"] = "OpenAI API key is not configured. Please add your API key to config.json"
                    result["error_type"] = "config"
                    return
                
                # Call your formatting function
                response = format_user_input(notes, api_key)
                
                # Check if the response contains an error
                if "error" in response:
                    result["error"] = response["error"]
                    result["error_type"] = response["error_type"]
                else:
                    # Success case - response contains "data" key
                    result["data"] = response["data"]
                    save_formatted_data(response["data"], execute_calculations)
                    
            except Exception as e:
                # Handle any unexpected exceptions
                result["error"] = f"An unexpected error occurred: {str(e)}"
                result["error_type"] = "general"
            finally:
                # Schedule the UI update on the main thread
                if dialog_active:
                    loading_dialog.after(0, on_api_complete)

        def on_api_complete():
            """Called when API call is complete (runs on main thread)."""
            nonlocal dialog_active
            dialog_active = False
            
            # Cancel spinner animation
            try:
                if hasattr(spinner, '_after_id') and spinner._after_id:
                    loading_dialog.after_cancel(spinner._after_id)
            except:
                pass
            
            # Store reference to dialog before destroying
            dialog_to_destroy = loading_dialog
            
            # Schedule destruction with a tiny delay
            def do_destroy():
                self.safe_destroy(dialog_to_destroy)
                
                if result["error"]:
                    # Show appropriate error message
                    if result["error_type"] == "validation":
                        self.show_validation_error_dialog(result["error"])
                    elif result["error_type"] in ["config", "auth", "quota", "model", "library"]:
                        self.show_config_error_dialog(result["error"], result["error_type"])
                    elif result["error_type"] in ["network", "timeout"]:
                        self.show_network_error_dialog(result["error"])
                    else:
                        self.show_general_error_dialog(result["error"])
                else:
                    # Show success message
                    self.root.after(10, lambda: self.show_success_dialog(result["data"]))
                    
                    # Refresh reset button visibility (classes directory now has data)
                    self.root.after(20, self.refresh_reset_button)
            
            # Use after with a small delay
            loading_dialog.after(50, do_destroy)
        
        # Start the API call in a background thread
        thread = threading.Thread(target=run_api_call)
        thread.daemon = True
        thread.start()

    def show_config_error_and_exit(self, error_message, error_type):
        """Show configuration error dialog and exit the application after user clicks OK."""
        
        # Create a dialog that will close the app when OK is clicked
        error_dialog = ctk.CTkToplevel(self.root)
        error_dialog.title("Configuration Error")
        error_dialog.geometry("450x250")
        error_dialog.resizable(False, False)
        error_dialog.transient(self.root)
        error_dialog.grab_set()
        error_dialog.focus_set()
        
        # Get screen dimensions for centering
        screen_width = error_dialog.winfo_screenwidth()
        screen_height = error_dialog.winfo_screenheight()
        
        # Calculate position to center on screen
        dialog_width = 450
        dialog_height = 250
        x = (screen_width // 2) - (dialog_width // 2)
        y = (screen_height // 2) - (dialog_height // 2)
        
        # Set the position
        error_dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        error_dialog.attributes('-alpha', 0.99)
        
        # Configure grid
        error_dialog.grid_columnconfigure(0, weight=1)
        error_dialog.grid_rowconfigure(2, weight=1)
        
        # Icon based on error type
        icon = "🔑" if error_type == "auth" else "⚙️" if error_type == "config" else "💰" if error_type == "quota" else "📚"
        
        ctk.CTkLabel(
            error_dialog,
            text=icon,
            font=ctk.CTkFont(size=48)
        ).grid(row=0, column=0, pady=(20, 5))
        
        # Title
        title = "Configuration Error"
        
        ctk.CTkLabel(
            error_dialog,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#dc3545"
        ).grid(row=1, column=0, pady=(0, 10))
        
        # Error message
        message_frame = ctk.CTkFrame(error_dialog, fg_color="transparent")
        message_frame.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="nsew")
        message_frame.grid_columnconfigure(0, weight=1)
        message_frame.grid_rowconfigure(0, weight=1)
        
        message_text = ctk.CTkTextbox(
            message_frame,
            wrap="word",
            font=ctk.CTkFont(size=11),
            height=80,
            corner_radius=8
        )
        message_text.grid(row=0, column=0, sticky="nsew")
        message_text.insert("1.0", error_message)
        message_text.configure(state="disabled")
        
        # OK button - this will close the dialog AND the entire app
        def close_and_exit():
            error_dialog.destroy()
            self.root.quit()  # Use quit() instead of destroy() to properly exit the app
            self.root.destroy()
        
        ctk.CTkButton(
            error_dialog,
                text="OK",
            width=100,
            command=close_and_exit
        ).grid(row=3, column=0, pady=(0, 15))
        
        # Bind Enter and Escape keys to exit
        error_dialog.bind('<Return>', lambda event: close_and_exit())
        error_dialog.bind('<Escape>', lambda event: close_and_exit())
        
        # Prevent the main window from showing
        self.root.withdraw()  # Hide the main window
        
        # Keep the dialog open until user clicks OK
        self.root.wait_window(error_dialog)

    def show_config_error_dialog(self, error_message, error_type):
        """Show configuration error dialog (non-fatal, doesn't close app)."""
        error_dialog = ctk.CTkToplevel(self.root)
        error_dialog.title("Configuration Error")
        error_dialog.geometry("450x250")
        error_dialog.resizable(False, False)
        error_dialog.transient(self.root)
        error_dialog.grab_set()
        
        # Center the dialog
        error_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (450 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (250 // 2)
        error_dialog.geometry(f"+{x}+{y}")
        
        error_dialog.attributes('-alpha', 0.99)
        
        # Configure grid
        error_dialog.grid_columnconfigure(0, weight=1)
        error_dialog.grid_rowconfigure(2, weight=1)
        
        # Icon based on error type
        icon = "🔑" if error_type == "auth" else "⚙️" if error_type == "config" else "💰" if error_type == "quota" else "📚"
        
        ctk.CTkLabel(
            error_dialog,
            text=icon,
            font=ctk.CTkFont(size=48)
        ).grid(row=0, column=0, pady=(20, 5))
        
        # Title
        title = "API Key Required" if error_type == "config" else "Invalid API Key" if error_type == "auth" else "API Quota Exceeded" if error_type == "quota" else "Configuration Error"
        
        ctk.CTkLabel(
            error_dialog,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#dc3545"
        ).grid(row=1, column=0, pady=(0, 10))
        
        # Error message
        message_frame = ctk.CTkFrame(error_dialog, fg_color="transparent")
        message_frame.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="nsew")
        message_frame.grid_columnconfigure(0, weight=1)
        message_frame.grid_rowconfigure(0, weight=1)
        
        message_text = ctk.CTkTextbox(
            message_frame,
            wrap="word",
            font=ctk.CTkFont(size=11),
            height=80,
            corner_radius=8
        )
        message_text.grid(row=0, column=0, sticky="nsew")
        message_text.insert("1.0", error_message)
        message_text.configure(state="disabled")
        
        # OK button - just close the dialog
        def close_dialog():
            error_dialog.destroy()
        
        ctk.CTkButton(
            error_dialog,
            text="OK",
            width=100,
            command=close_dialog
        ).grid(row=3, column=0, pady=(0, 15))
        
        error_dialog.bind('<Return>', lambda event: close_dialog())
        error_dialog.bind('<Escape>', lambda event: close_dialog())

    def show_network_error_dialog(self, error_message):
        """Show network error dialog."""
        error_dialog = ctk.CTkToplevel(self.root)
        error_dialog.title("Network Error")
        error_dialog.geometry("400x200")
        error_dialog.resizable(False, False)
        error_dialog.transient(self.root)
        error_dialog.grab_set()
        
        # Center the dialog
        error_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (400 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (200 // 2)
        error_dialog.geometry(f"+{x}+{y}")
        
        error_dialog.attributes('-alpha', 0.99)
        
        # Icon
        ctk.CTkLabel(
            error_dialog,
            text="🌐",
            font=ctk.CTkFont(size=48)
        ).pack(pady=(20, 5))
        
        # Title
        ctk.CTkLabel(
            error_dialog,
            text="Network Connection Error",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#dc3545"
        ).pack(pady=(0, 10))
        
        # Message
        message_label = ctk.CTkLabel(
            error_dialog,
            text=error_message,
            font=ctk.CTkFont(size=11),
            wraplength=350
        )
        message_label.pack(padx=20, pady=(0, 15))
        
        # OK button
        def close_dialog():
            error_dialog.destroy()
        
        ctk.CTkButton(
            error_dialog,
            text="OK",
            width=100,
            command=close_dialog
        ).pack(pady=(0, 15))
        
        error_dialog.bind('<Return>', lambda event: close_dialog())
        error_dialog.bind('<Escape>', lambda event: close_dialog())

    def show_general_error_dialog(self, error_message):
        """Show general error dialog."""
        error_dialog = ctk.CTkToplevel(self.root)
        error_dialog.title("Error")
        error_dialog.geometry("400x200")
        error_dialog.resizable(False, False)
        error_dialog.transient(self.root)
        error_dialog.grab_set()
        
        # Center the dialog
        error_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (400 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (200 // 2)
        error_dialog.geometry(f"+{x}+{y}")
        
        error_dialog.attributes('-alpha', 0.99)
        
        # Icon
        ctk.CTkLabel(
            error_dialog,
            text="❌",
            font=ctk.CTkFont(size=48)
        ).pack(pady=(20, 5))
        
        # Title
        ctk.CTkLabel(
            error_dialog,
            text="An Error Occurred",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#dc3545"
        ).pack(pady=(0, 10))
        
        # Message
        message_label = ctk.CTkLabel(
            error_dialog,
            text=error_message,
            font=ctk.CTkFont(size=11),
            wraplength=350
        )
        message_label.pack(padx=20, pady=(0, 15))
        
        # OK button
        def close_dialog():
            error_dialog.destroy()
        
        ctk.CTkButton(
            error_dialog,
            text="OK",
            width=100,
            command=close_dialog
        ).pack(pady=(0, 15))
        
        error_dialog.bind('<Return>', lambda event: close_dialog())
        error_dialog.bind('<Escape>', lambda event: close_dialog())

    def show_validation_error_dialog(self, error_message):
        """Show a user-friendly validation error dialog that fits the screen."""
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate dialog size (80% of screen width, 70% of screen height)
        dialog_width = min(700, int(screen_width * 0.8))
        dialog_height = min(600, int(screen_height * 0.7))
        
        # Ensure minimum size
        dialog_width = max(500, dialog_width)
        dialog_height = max(450, dialog_height)
        
        # Create dialog with calculated size
        error_dialog = ctk.CTkToplevel(self.root)
        error_dialog.title("Invalid Input Format")
        error_dialog.geometry(f"{dialog_width}x{dialog_height}")
        error_dialog.resizable(True, True)
        error_dialog.minsize(450, 400)
        error_dialog.transient(self.root)
        error_dialog.grab_set()
        
        # Center the dialog
        error_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog_width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog_height // 2)
        error_dialog.geometry(f"+{x}+{y}")
        
        # Configure dialog
        error_dialog.attributes('-alpha', 0.99)
        
        # Configure grid for better expansion
        error_dialog.grid_columnconfigure(0, weight=1)
        error_dialog.grid_rowconfigure(3, weight=1)  # The text area row expands
        
        # Error icon - make it smaller to save space
        icon_label = ctk.CTkLabel(
            error_dialog,
            text="⚠️",
            font=ctk.CTkFont(size=36)  # Reduced from 48
        )
        icon_label.grid(row=0, column=0, pady=(10, 2))  # Reduced padding
        
        # Error title
        title_label = ctk.CTkLabel(
            error_dialog,
            text="Invalid Input Format",
            font=ctk.CTkFont(size=18, weight="bold"),  # Slightly smaller
            text_color="#dc3545"
        )
        title_label.grid(row=1, column=0, pady=(0, 5))  # Reduced padding
        
        # Instructions label
        instructions_label = ctk.CTkLabel(
            error_dialog,
            text="Your input doesn't match the expected format. Please follow the example below:",
            font=ctk.CTkFont(size=11),  # Smaller font
            wraplength=dialog_width - 60
        )
        instructions_label.grid(row=2, column=0, padx=20, pady=(0, 8))
        
        # Error message with expected format instructions
        error_frame = ctk.CTkFrame(error_dialog, fg_color="transparent")
        error_frame.grid(row=3, column=0, padx=15, pady=(0, 10), sticky="nsew")
        error_frame.grid_columnconfigure(0, weight=1)
        error_frame.grid_rowconfigure(0, weight=1)
        
        error_text = ctk.CTkTextbox(
            error_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=10),  # Smaller font
            corner_radius=8,
            border_width=1,
            border_color="#a0a0a0"
        )
        error_text.grid(row=0, column=0, sticky="nsew")
    
        # Compact instructions with clear formatting
        instructions = """📋 REQUIRED FORMAT:
• Class header (e.g., "SS2F Report (Third Term)")
• 3 position lines with names & averages
• "BEST IN SUBJECTS" section with numbered entries
• "MOST IMPROVED" section with numbered entries

✅ EXAMPLE (truncated - scroll for full):
────────────────────────────────
SS2F Report (Third Term)
1st position - Orjiakor Chisom Perpetual . Ave- 86.7
2nd position - Nweke Miracle Onyinye. Ave- 82.4
3rd position - Odinchefu Uchechukwu. Ave- 71.7

BEST IN SUBJECTS
1. English language - Omaba Favour Iruoma. Score- 78
2. Mathematics - Ezeh Chioma Mary Cynthia. Score- 72
3. Igbo - Amaechi Judith - 76
4. Civic Education - Omaba Favour Iruoma - 84
5. Commerce - Nweke Miracle Onyinye - 87
6. Fin. Accounting - Ezeogu Ifeoma Favour - 85
7. Economics - Unamba Oluebube Maryann - 85
8. Data processing - Umunna Chioma MaryJane - 91
9. C.C.P - Okeke Adachukwu Deborah - 82
10. Marketing - Obasi Chidimma - 90
11. Moral - Nwakwesili Chinenye Gift - 88

MOST IMPROVED
1. Ezechukwu Oluebube - 41st to 37th
2. Ezeogu Ifeoma - 37th to 5th
3. Ezekwe Chinenye - 38th to 34th
4. Isong Nkemdilim - 12th to 7th
5. Martin Chimma - 36th to 23rd
6. Mbanusi Oluebube - 20th to 8th
7. Nwakwesili Chinenye - 50th to 16th
8. Odinchefu Uchechukwu - 23rd to 4th
9. Okeke Adachukwu - 46th to 24th
10. Okwesa Kosara - 42nd to 32nd
11. Okeke Onyinye - 30th to 11th
12. Nweke Miracle - 31st to 3rd
13. Uchegbu Chinemerem - 15th to 6th
14. Ugwuoke Chisom - 32nd to 26th
15. Umunna Chimma - 40th to 8th
16. Agu Mmasi - 57th to 50th

❌ COMMON MISTAKES:
• Missing header or sections
• Wrong number formatting
• Missing numbered lists

Scroll for full example. Check your input and try again."""
    
        error_text.insert("1.0", instructions)
        error_text.configure(state="disabled")
        
        # OK Button frame
        button_frame = ctk.CTkFrame(error_dialog, fg_color="transparent")
        button_frame.grid(row=4, column=0, pady=(0, 12))
        
        # OK button
        def close_dialog():
            error_dialog.destroy()
        
        ctk.CTkButton(
            button_frame,
            text="OK",
            width=100,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=close_dialog
        ).pack()
        
        # Bind Enter and Escape keys
        error_dialog.bind('<Return>', lambda event: close_dialog())
        error_dialog.bind('<Escape>', lambda event: close_dialog())

    def show_success_dialog(self, formatted_data):
        """Show success message."""

        # Clear the text area
        self.text_area.delete("1.0", tk.END)

        success_dialog = ctk.CTkToplevel(self.root)
        success_dialog.title("Success")
        success_dialog.geometry("300x150")
        success_dialog.resizable(False, False)
        success_dialog.transient(self.root)
        success_dialog.grab_set()
        
        # Center success dialog
        success_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (150 // 2)
        success_dialog.geometry(f"+{x}+{y}")
        
        # Configure dialog to prevent title bar issues
        success_dialog.attributes('-alpha', 0.99)
        
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
        
        # Store the after ID
        after_id = None
        
        def close_dialog():
            nonlocal after_id
            if after_id:
                try:
                    success_dialog.after_cancel(after_id)
                except:
                    pass
            self.safe_destroy(success_dialog)
        
        ctk.CTkButton(
            success_dialog,
            text="OK",
            width=100,
            command=close_dialog
        ).pack(pady=15)
        
        # Auto-close after 2 seconds
        after_id = success_dialog.after(2000, close_dialog)
        
        # Handle manual close
        def on_closing():
            nonlocal after_id
            if after_id:
                try:
                    success_dialog.after_cancel(after_id)
                except:
                    pass
            self.safe_destroy(success_dialog)
        
        success_dialog.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Print to console
        print("\n" + "="*50)
        print("FORM SUBMITTED:")
        print(formatted_data)
        print("="*50 + "\n")