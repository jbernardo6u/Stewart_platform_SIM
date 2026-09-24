#!/usr/bin/env python3
"""
Stewart Platform Project Launcher.
Main entry point for the Stewart Platform control system.
"""

import sys
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class StewartPlatformLauncher:
    """
    Main launcher for the Stewart Platform project.
    Provides access to all project components and tools.
    """
    
    def __init__(self, root):
        """Initialize the launcher."""
        self.root = root
        self.root.title("🤖 Stewart Platform - Project Launcher")
        self.root.geometry("800x600")
        self.root.configure(bg='#1B1B1B')
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the main launcher interface."""
        # Header
        header_frame = tk.Frame(self.root, bg='#2E86AB', height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🤖 STEWART PLATFORM",
            font=('Arial', 24, 'bold'),
            fg='white',
            bg='#2E86AB'
        )
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(
            header_frame,
            text="6-DOF Parallel Manipulator Control System",
            font=('Arial', 12),
            fg='#E8F4FD',
            bg='#2E86AB'
        )
        subtitle_label.pack()
        
        # Main content
        main_frame = tk.Frame(self.root, bg='#1B1B1B')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)
        
        # Create sections
        self.create_gui_section(main_frame)
        self.create_tools_section(main_frame)
        self.create_examples_section(main_frame)
        self.create_info_section(main_frame)
    
    def create_gui_section(self, parent):
        """Create GUI interfaces section."""
        gui_frame = self.create_section_frame(parent, "🎮 GUI INTERFACES")
        
        gui_buttons = [
            ("🚀 Quick Launcher", "One-click simulation access", self.launch_quick_simulation),
            ("🎮 Simulation Manager", "Complete simulation interface", self.launch_simulation_manager),
            ("🎯 Simple GUI", "Basic control interface", self.launch_simple_gui),
            ("⚡ Advanced GUI", "Full-featured interface", self.launch_advanced_gui),
            ("🔬 PyBullet GUI", "3D simulation interface", self.launch_pybullet_gui)
        ]
        
        for text, desc, command in gui_buttons:
            self.create_button(gui_frame, text, desc, command)
    
    def create_tools_section(self, parent):
        """Create tools and utilities section."""
        tools_frame = self.create_section_frame(parent, "🛠️ TOOLS & UTILITIES")
        
        tool_buttons = [
            ("📊 Kinematics Tester", "Test inverse kinematics calculations", self.launch_kinematics_test),
            ("📈 Visualization", "Matplotlib plotting tools", self.launch_visualization),
            ("⚙️ Configuration", "Platform configuration editor", self.open_config),
            ("🔧 Setup Project", "Run project setup and checks", self.run_setup)
        ]
        
        for text, desc, command in tool_buttons:
            self.create_button(tools_frame, text, desc, command)
    
    def create_examples_section(self, parent):
        """Create examples section."""
        examples_frame = self.create_section_frame(parent, "📚 SIMULATIONS & DEMOS")
        
        example_buttons = [
            ("🔄 Elliptical Demo", "Smooth elliptical trajectory", self.run_elliptical_demo),
            ("🌀 Spiral Demo", "3D spiral motion demo", self.run_spiral_demo),
            ("〰️ Sine Wave Demo", "Multi-axis sinusoidal patterns", self.run_sine_demo),
            ("🎭 Mixed Demo", "Complex combined movements", self.run_mixed_demo),
            ("🎢 Interactive Demos", "Choose demo interactively", self.run_interactive_demo),
            ("📓 Open Documentation", "View project documentation", self.open_documentation)
        ]
        
        for text, desc, command in example_buttons:
            self.create_button(examples_frame, text, desc, command)
    
    def create_info_section(self, parent):
        """Create information section."""
        info_frame = self.create_section_frame(parent, "ℹ️ INFORMATION")
        
        info_buttons = [
            ("📋 Project Structure", "View project organization", self.show_project_structure),
            ("🔍 System Check", "Check dependencies and setup", self.run_system_check),
            ("📖 User Guide", "Open usage guide", self.open_user_guide),
            ("❓ About", "About this project", self.show_about)
        ]
        
        for text, desc, command in info_buttons:
            self.create_button(info_frame, text, desc, command)
    
    def create_section_frame(self, parent, title):
        """Create a section frame with title."""
        section_frame = tk.Frame(parent, bg='#2E86AB', relief='ridge', borderwidth=2)
        section_frame.pack(fill=tk.X, pady=10)
        
        title_label = tk.Label(
            section_frame,
            text=title,
            font=('Arial', 14, 'bold'),
            fg='white',
            bg='#2E86AB'
        )
        title_label.pack(pady=(10, 5))
        
        content_frame = tk.Frame(section_frame, bg='#2E86AB')
        content_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        return content_frame
    
    def create_button(self, parent, text, description, command):
        """Create a styled button with description."""
        button_frame = tk.Frame(parent, bg='#2E86AB')
        button_frame.pack(fill=tk.X, pady=2)
        
        button = tk.Button(
            button_frame,
            text=text,
            font=('Arial', 11, 'bold'),
            bg='#4A90C2',
            fg='white',
            command=command,
            relief='raised',
            borderwidth=2,
            width=20
        )
        button.pack(side=tk.LEFT, padx=(0, 15))
        
        desc_label = tk.Label(
            button_frame,
            text=description,
            font=('Arial', 10),
            fg='#E8F4FD',
            bg='#2E86AB'
        )
        desc_label.pack(side=tk.LEFT, anchor=tk.W)
    
    # GUI Launch Methods
    def launch_quick_simulation(self):
        """Launch the quick simulation launcher."""
        try:
            subprocess.run([sys.executable, str(project_root / "run_simulation.py")])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch quick simulation: {str(e)}")
    
    def launch_simulation_manager(self):
        """Launch the simulation manager."""
        try:
            subprocess.run([sys.executable, str(project_root / "scripts" / "simulation_manager.py")])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch simulation manager: {str(e)}")
    
    def launch_gui_launcher(self):
        """Launch the GUI selection menu."""
        try:
            from scripts.gui_launcher import main as gui_launcher_main
            self.root.withdraw()
            gui_launcher_main()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch GUI launcher: {str(e)}")
    
    def launch_simple_gui(self):
        """Launch the simple GUI directly."""
        try:
            from src.gui.simple_gui import main as simple_gui_main
            self.root.withdraw()
            simple_gui_main()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Simple GUI: {str(e)}")
    
    def launch_advanced_gui(self):
        """Launch the advanced GUI directly."""
        try:
            from src.gui.advanced_gui import main as advanced_gui_main
            self.root.withdraw()
            advanced_gui_main()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch Advanced GUI: {str(e)}")
    
    def launch_pybullet_gui(self):
        """Launch the PyBullet GUI directly."""
        try:
            from src.gui.pybullet_gui import main as pybullet_gui_main
            self.root.withdraw()
            pybullet_gui_main()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch PyBullet GUI: {str(e)}")
    
    # Tool Methods
    def launch_kinematics_test(self):
        """Launch kinematics testing tool."""
        try:
            subprocess.run([sys.executable, "-c", """
from src.core.kinematics import InverseKinematics
import numpy as np

# Test inverse kinematics
ik = InverseKinematics(0.2, 0.2, 12, 12)
test_poses = [
    [0, 0, 0, 0, 0, 0],
    [10, 10, 20, 5, 5, 10],
    [-15, 15, -10, -8, 8, -15]
]

print("Kinematics Test Results:")
print("=" * 40)
for i, pose in enumerate(test_poses):
    try:
        lengths = ik.calculate(pose)
        print(f"Test {i+1}: {pose}")
        print(f"  Leg lengths: {[f'{l:.2f}' for l in lengths]}")
        print()
    except Exception as e:
        print(f"Test {i+1} failed: {str(e)}")
        print()

input("Press Enter to close...")
"""], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch kinematics test: {str(e)}")
    
    def launch_visualization(self):
        """Launch visualization tools."""
        try:
            from src.simulation.matplotlib_viz import demo_visualization
            demo_visualization()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch visualization: {str(e)}")
    
    def open_config(self):
        """Open configuration editor."""
        try:
            config_path = project_root / "assets" / "config" / "platform_config.yaml"
            if config_path.exists():
                if os.name == 'nt':  # Windows
                    os.startfile(str(config_path))
                else:  # Linux/Mac
                    subprocess.run(['xdg-open', str(config_path)])
            else:
                messagebox.showwarning("Warning", f"Configuration file not found: {config_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open configuration: {str(e)}")
    
    def run_setup(self):
        """Run project setup script."""
        try:
            from scripts.setup_project import main as setup_main
            setup_main()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run setup: {str(e)}")
    
    # Simulation Demo Methods
    def run_elliptical_demo(self):
        """Run elliptical trajectory demonstration."""
        try:
            subprocess.run([sys.executable, str(project_root / "examples" / "trajectory_demo.py"), 
                           "--type", "ellipse", "--simulation"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run elliptical demo: {str(e)}")
    
    def run_spiral_demo(self):
        """Run spiral trajectory demonstration."""
        try:
            subprocess.run([sys.executable, str(project_root / "examples" / "trajectory_demo.py"), 
                           "--type", "spiral", "--simulation"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run spiral demo: {str(e)}")
    
    def run_sine_demo(self):
        """Run sinusoidal trajectory demonstration."""
        try:
            subprocess.run([sys.executable, str(project_root / "examples" / "trajectory_demo.py"), 
                           "--type", "sine", "--simulation"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run sine demo: {str(e)}")
    
    def run_mixed_demo(self):
        """Run mixed trajectory demonstration."""
        try:
            subprocess.run([sys.executable, str(project_root / "examples" / "trajectory_demo.py"), 
                           "--type", "mixed", "--simulation"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run mixed demo: {str(e)}")
    
    def run_interactive_demo(self):
        """Run interactive demo selection."""
        try:
            subprocess.run([sys.executable, str(project_root / "examples" / "trajectory_demo.py")])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run interactive demo: {str(e)}")
    
    # Legacy example methods preserved for compatibility
    def run_basic_example(self):
        """Run basic control example."""
        try:
            example_path = project_root / "examples" / "basic_control.py"
            subprocess.run([sys.executable, str(example_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run basic example: {str(e)}")
    
    def run_trajectory_demo(self):
        """Run trajectory demonstration."""
        try:
            example_path = project_root / "examples" / "trajectory_demo.py"
            subprocess.run([sys.executable, str(example_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run trajectory demo: {str(e)}")
    
    def run_hardware_example(self):
        """Run hardware integration example."""
        try:
            example_path = project_root / "examples" / "hardware_integration.py"
            subprocess.run([sys.executable, str(example_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run hardware example: {str(e)}")
    
    def open_documentation(self):
        """Open project documentation."""
        try:
            readme_path = project_root / "README.md"
            if readme_path.exists():
                if os.name == 'nt':  # Windows
                    os.startfile(str(readme_path))
                else:  # Linux/Mac
                    subprocess.run(['xdg-open', str(readme_path)])
            else:
                messagebox.showwarning("Warning", "README.md not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open documentation: {str(e)}")
    
    # Info Methods
    def show_project_structure(self):
        """Show project structure information."""
        try:
            structure_path = project_root / "ARCHITECTURE.md"
            if structure_path.exists():
                if os.name == 'nt':  # Windows
                    os.startfile(str(structure_path))
                else:  # Linux/Mac
                    subprocess.run(['xdg-open', str(structure_path)])
            else:
                messagebox.showinfo("Project Structure", """
Stewart Platform Project Structure:

src/
├── core/          # Core kinematics and platform logic
├── gui/           # GUI interfaces
├── hardware/      # Hardware abstraction
├── simulation/    # Simulation and visualization
└── utils/         # Utility functions

simulation/        # URDF, meshes, worlds
configurations/    # YAML configuration
examples/          # Example scripts
tests/             # Unit tests
scripts/           # Utility scripts
docs/              # Documentation
""")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show project structure: {str(e)}")
    
    def run_system_check(self):
        """Run system and dependency check."""
        try:
            subprocess.run([sys.executable, "-c", """
import sys
import platform

print("Stewart Platform - System Check")
print("=" * 40)
print(f"Python: {platform.python_version()}")
print(f"Platform: {platform.platform()}")
print()

# Check required packages
required_packages = [
    'numpy', 'matplotlib', 'pyyaml', 'tkinter'
]

optional_packages = [
    'pybullet', 'scipy', 'pandas'
]

print("Required Dependencies:")
for pkg in required_packages:
    try:
        __import__(pkg)
        print(f"✓ {pkg}")
    except ImportError:
        print(f"✗ {pkg} (missing)")

print()
print("Optional Dependencies:")
for pkg in optional_packages:
    try:
        module = __import__(pkg)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {pkg} ({version})")
    except ImportError:
        print(f"✗ {pkg} (not installed)")

input("\\nPress Enter to close...")
"""], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run system check: {str(e)}")
    
    def open_user_guide(self):
        """Open user guide."""
        try:
            guide_path = project_root / "docs" / "guides" / "GUIDE_UTILISATION.md"
            if guide_path.exists():
                if os.name == 'nt':  # Windows
                    os.startfile(str(guide_path))
                else:  # Linux/Mac
                    subprocess.run(['xdg-open', str(guide_path)])
            else:
                messagebox.showwarning("Warning", "User guide not found")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open user guide: {str(e)}")
    
    def show_about(self):
        """Show about information."""
        about_text = """
🤖 Stewart Platform Control System

A comprehensive 6-DOF parallel manipulator control system with:

• Multiple GUI interfaces (Simple, Advanced, PyBullet)
• Real-time kinematics calculations
• 3D simulation and visualization
• Hardware integration support
• Trajectory generation and analysis

Features:
✓ Modular architecture
✓ Comprehensive testing
✓ Modern Python practices
✓ Extensive documentation
✓ Cross-platform compatibility

Developed for research and educational purposes.
        """
        messagebox.showinfo("About Stewart Platform", about_text)


def main():
    """Main function to run the project launcher."""
    root = tk.Tk()
    
    # Configure for better appearance
    try:
        root.tk.call('tk', 'scaling', 1.0)
    except:
        pass
    
    launcher = StewartPlatformLauncher(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.quit()


if __name__ == "__main__":
    main()
