import tkinter as tk
import ttkbootstrap as ttk_bs # Assuming ai_ui.py uses ttkbootstrap
from ttkbootstrap.constants import *
import importlib.util # Added for dynamic import
import os # Added to construct full path

# --- Helper function to dynamically load a module ---
def load_module_dynamically(module_name, file_path):
    """Dynamically loads a module from a given file path."""
    # Construct an absolute path to be safe, especially if main_app.py might be run from different CWDs
    # However, for simplicity, if they are in the same dir, relative path is fine.
    # For robustness, let's assume file_path is relative to this script's directory or is absolute.
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: Module file not found at {file_path}")
        return None

    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            print(f"Error: Could not create spec for module {module_name} from {file_path}")
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error loading module {module_name} from {file_path}: {e}")
        return None

# --- Dynamically load AIAssistant ---
AI_ASSISTANT_FILE_NAME = "ai_assistant.py"
# We give it a module name that's valid, e.g., "ai_assistant_module"
# The actual filename on disk is AI_ASSISTANT_FILE_NAME
ai_assistant_loaded_module = load_module_dynamically("ai_assistant_module", AI_ASSISTANT_FILE_NAME)

AIAssistant = None
if ai_assistant_loaded_module:
    if hasattr(ai_assistant_loaded_module, 'AIAssistant'):
        AIAssistant = ai_assistant_loaded_module.AIAssistant
    else:
        print(f"Error: 'AIAssistant' class not found in {AI_ASSISTANT_FILE_NAME}")
else:
    print(f"Error: Failed to load module from {AI_ASSISTANT_FILE_NAME}")

# --- Configuration (Can be moved to a config file or class later) ---
DB_NAME = "todo.db"
DEFAULT_THEME = "superhero" # Example ttkbootstrap theme

class MainApplication:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("AI驱动的智能待办事项助手")
        self.root.geometry("800x700") # Adjust size as needed

        if not AIAssistant:
            # Handle the case where AIAssistant could not be loaded
            error_label = ttk_bs.Label(self.root, text=f"Critical Error: AIAssistant class could not be loaded from {AI_ASSISTANT_FILE_NAME}. Application cannot start.", bootstyle="danger", wraplength=750)
            error_label.pack(padx=20, pady=20, expand=True, fill=BOTH)
            return # Stop initialization

        # Instantiate the AIAssistant
        self.ai_assistant = AIAssistant(config_manager=None, db_name=DB_NAME)

        if self.ai_assistant.ui:
            # Create and pack the AI panel using the AIUserInterface instance
            ai_panel = self.ai_assistant.ui.create_ai_panel(self.root)
            if ai_panel: # create_ai_panel should return the created frame
                ai_panel.pack(fill=BOTH, expand=True, padx=10, pady=10)
            else:
                error_label = ttk_bs.Label(self.root, text="AI Panel could not be loaded (create_ai_panel issue).", bootstyle="danger")
                error_label.pack(padx=20, pady=20)
        else:
            error_label = ttk_bs.Label(self.root, text="AIUserInterface not available in AIAssistant.", bootstyle="danger")
            error_label.pack(padx=20, pady=20)

if __name__ == "__main__":
    if not AIAssistant: # Check if dynamic loading was successful
        print(f"CRITICAL ERROR: AIAssistant could not be loaded from '{AI_ASSISTANT_FILE_NAME}'. UI cannot start.")
        # Optionally, show a simple Tkinter error window if Tk is available
        try:
            error_root = tk.Tk()
            error_root.title("Loading Error")
            tk.Label(error_root, text=f"Failed to load AIAssistant from\n{AI_ASSISTANT_FILE_NAME}.\nApplication cannot start.", padx=20, pady=20, fg="red").pack()
            error_root.mainloop()
        except Exception:
            pass # If Tkinter itself fails, just rely on console print
    # The check below is now less critical here since we check AIAssistant above,
    # but keeping it as a general safety for UI components.
    elif not hasattr(AIAssistant(""), 'ui') or not hasattr(AIAssistant("").ui, 'create_ai_panel'):
        print("Error: AIAssistant is loaded, but its UI components seem to be missing or not set up correctly.")
        print("Please check 'ai_ui.py' and the AIAssistant class initialization.")
    else:
        try:
            root = ttk_bs.Window(themename=DEFAULT_THEME) 
        except Exception as e:
            print(f"Failed to initialize ttkbootstrap Window (theme: {DEFAULT_THEME}). Error: {e}")
            print("Falling back to standard Tkinter window.")
            root = tk.Tk()

        app = MainApplication(root)
        root.mainloop() 