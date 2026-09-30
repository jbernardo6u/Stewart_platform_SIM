#!/usr/bin/env python3
"""
GUI Launcher for Stewart Platform.
Provides a menu to select and launch different GUI interfaces.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import subprocess
from pathlib import Path


class GUILauncher:
    """
    Launcher interface for selecting Stewart Platform GUIs.
    """
    
    def __init__(self, root):
        """Initialize the launcher."""
        self.root = root
        self.root.title("🤖 Stewart Platform - GUI Launcher")
        self.root.geometry("600x500")
        self.root.configure(bg='#2E86AB')
        
        # GUI options
        self.gui_options = {
            "Simple GUI": {
                "description": "Basic control interface with essential features.\nIdeal for quick testing and simple operations.",
                "script": "simple_gui.py",
                "features": ["Position control", "Rotation control", "Real-time feedback", "Emergency stop"]
            },
            "Advanced GUI": {
                "description": "Full-featured interface with animations and presets.\nIncludes automation and advanced controls.",
                "script": "advanced_gui.py", 
                "features": ["All simple features", "Animation sequences", "Position presets", "Auto mode", "Trajectory generation"]
            },
            "PyBullet GUI": {
                "description": "GUI with integrated 3D simulation.\nProvides real-time visualization and physics simulation.",
                "script": "pybullet_gui.py",
                "features": ["All advanced features", "3D visualization", "Physics simulation", "Camera controls", "Recording"]
            }
        }
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the launcher interface."""
        # Title
        title_frame = tk.Frame(self.root, bg='#2E86AB')
        title_frame.pack(fill=tk.X, pady=20)
        
        title_label = tk.Label(
            title_frame, 
            text="🤖 STEWART PLATFORM\nGUI LAUNCHER",
            font=('Arial', 20, 'bold'),
            fg='white',
            bg='#2E86AB'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Select the interface that best suits your needs",
            font=('Arial', 12),
            fg='#E8F4FD',
            bg='#2E86AB'
        )
        subtitle_label.pack(pady=(10, 0))
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#2E86AB')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Create GUI option cards
        for i, (gui_name, gui_info) in enumerate(self.gui_options.items()):
            self.create_gui_card(main_frame, gui_name, gui_info, i)
        
        # Footer with info
        footer_frame = tk.Frame(self.root, bg='#2E86AB')
        footer_frame.pack(fill=tk.X, pady=(0, 20))
        
        info_label = tk.Label(
            footer_frame,
            text="💡 Tip: Start with Simple GUI for basic testing, then move to Advanced or PyBullet for more features",
            font=('Arial', 10),
            fg='#E8F4FD',
            bg='#2E86AB',
            wraplength=500
        )
        info_label.pack()
    
    def create_gui_card(self, parent, gui_name, gui_info, index):
        """Create a card for each GUI option."""
        # Card frame
        card_frame = tk.Frame(parent, bg='#4A90C2', relief='raised', borderwidth=2)
        card_frame.pack(fill=tk.X, pady=10)
        
        # Header
        header_frame = tk.Frame(card_frame, bg='#4A90C2')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        title_label = tk.Label(
            header_frame,
            text=gui_name,
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#4A90C2'
        )
        title_label.pack(side=tk.LEFT)
        
        launch_btn = tk.Button(
            header_frame,
            text="🚀 LAUNCH",
            font=('Arial', 12, 'bold'),
            bg='#2ECC40',
            fg='white',
            command=lambda: self.launch_gui(gui_name),
            relief='raised',
            borderwidth=2,
            width=10
        )
        launch_btn.pack(side=tk.RIGHT)
        
        # Description
        desc_label = tk.Label(
            card_frame,
            text=gui_info["description"],
            font=('Arial', 11),
            fg='white',
            bg='#4A90C2',
            wraplength=400,
            justify=tk.LEFT
        )
        desc_label.pack(anchor=tk.W, padx=15, pady=(0, 10))
        
        # Features
        features_frame = tk.Frame(card_frame, bg='#4A90C2')
        features_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        features_label = tk.Label(
            features_frame,
            text="Features:",
            font=('Arial', 10, 'bold'),
            fg='#E8F4FD',
            bg='#4A90C2'
        )
        features_label.pack(anchor=tk.W)
        
        for feature in gui_info["features"]:
            feature_label = tk.Label(
                features_frame,
                text=f"• {feature}",
                font=('Arial', 9),
                fg='#E8F4FD',
                bg='#4A90C2'
            )
            feature_label.pack(anchor=tk.W, padx=(20, 0))
    
    def launch_gui(self, gui_name):
        """Launch the selected GUI."""
        try:
            gui_info = self.gui_options[gui_name]
            script_name = gui_info["script"]
            
            # Get the path to the GUI script
            current_dir = Path(__file__).parent
            gui_script_path = current_dir / "src" / "gui" / script_name
            
            if not gui_script_path.exists():
                # Try direct execution of the GUI class
                self.launch_gui_direct(gui_name)
                return
            
            # Launch as subprocess
            subprocess.Popen([sys.executable, str(gui_script_path)])
            
            messagebox.showinfo(
                "GUI Launched", 
                f"{gui_name} has been launched successfully!\n\nYou can close this launcher window now."
            )
            
        except Exception as e:
            messagebox.showerror(
                "Launch Error", 
                f"Failed to launch {gui_name}:\n{str(e)}\n\nTrying direct launch..."
            )
            self.launch_gui_direct(gui_name)
    
    def launch_gui_direct(self, gui_name):
        """Launch GUI directly by importing and running the class."""
        try:
            import tkinter as tk
            
            if gui_name == "Simple GUI":
                from src.gui.simple_gui import SimpleStewartGUI
                root = tk.Tk()
                app = SimpleStewartGUI(root)
                
            elif gui_name == "Advanced GUI":
                from src.gui.advanced_gui import AdvancedStewartGUI
                root = tk.Tk()
                app = AdvancedStewartGUI(root)
                
            elif gui_name == "PyBullet GUI":
                from src.gui.pybullet_gui import PyBulletStewartGUI
                root = tk.Tk()
                app = PyBulletStewartGUI(root)
            
            else:
                raise ValueError(f"Unknown GUI: {gui_name}")
            
            # Handle window closing
            root.protocol("WM_DELETE_WINDOW", app.on_closing)
            
            # Hide launcher and run GUI
            self.root.withdraw()
            
            def on_gui_close():
                app.on_closing()
                self.root.deiconify()  # Show launcher again
            
            root.protocol("WM_DELETE_WINDOW", on_gui_close)
            root.mainloop()
            
        except ImportError as e:
            messagebox.showerror(
                "Import Error",
                f"Failed to import {gui_name}:\n{str(e)}\n\nPlease ensure all dependencies are installed."
            )
        except Exception as e:
            messagebox.showerror(
                "Launch Error",
                f"Failed to launch {gui_name}:\n{str(e)}"
            )
    
    def show_system_info(self):
        """Show system and dependency information."""
        try:
            import platform
            import numpy
            import matplotlib
            
            info = f"""System Information:
            
Platform: {platform.platform()}
Python: {platform.python_version()}
NumPy: {numpy.__version__}
Matplotlib: {matplotlib.__version__}

GUI Dependencies:
✓ Tkinter (built-in)
✓ NumPy (installed)
✓ Matplotlib (installed)
"""
            
            try:
                import pybullet
                info += f"✓ PyBullet: {pybullet.__version__}\n"
            except ImportError:
                info += "✗ PyBullet (not installed - required for PyBullet GUI)\n"
            
            messagebox.showinfo("System Information", info)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get system info: {str(e)}")


def main():
    """Main function to run the GUI launcher."""
    root = tk.Tk()
    
    # Add system info menu
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)
    
    launcher = GUILauncher(root)
    help_menu.add_command(label="System Info", command=launcher.show_system_info)
    help_menu.add_separator()
    help_menu.add_command(label="Exit", command=root.quit)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.quit()


if __name__ == "__main__":
    main()
