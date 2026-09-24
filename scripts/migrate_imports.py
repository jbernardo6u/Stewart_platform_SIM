#!/usr/bin/env python3
"""
Migration script to update import statements and file references
to use the new modular structure.
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path):
    """Update import statements in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update import statements
        replacements = [
            # Core imports
            (r'from src.core.platform import StewartPlatform as sp', 'from src.core.platform import StewartPlatform as sp'),
            (r'from src.core.platform import StewartPlatform', 'from src.core.platform import StewartPlatform'),
            (r'from src.core.kinematics import InverseKinematics', 'from src.core.kinematics import InverseKinematics'),
            (r'from src.core.kinematics import InverseKinematics', 'from src.core.kinematics import InverseKinematics'),
            
            # Trajectory imports
            (r'from src.core.trajectory import draw_3d_spiral', 'from src.core.trajectory import draw_3d_spiral'),
            (r'from src.core.trajectory import generate_elliptical_points', 'from src.core.trajectory import generate_elliptical_points'),
            
            # Hardware imports
            (r'from src.hardware.motor_controller import MotorController', 'from src.hardware.motor_controller import MotorController'),
            (r'from src.hardware.physical_platform import PhysicalStewartPlatform', 'from src.hardware.physical_platform import PhysicalStewartPlatform'),
            
            # Path updates
            (r'"Stewart/Stewart\.urdf"', '"assets/models/Stewart.urdf"'),
            (r"'Stewart/Stewart\.urdf'", "'assets/models/Stewart.urdf'"),
            
            # Class instantiation updates
            (r'= ik\(', '= InverseKinematics('),
            (r'clf_ik = ik\(', 'clf_ik = InverseKinematics('),
            (r'self\.clf = ik\(', 'self.clf = InverseKinematics('),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated: {file_path}")
            return True
        else:
            print(f"- No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ Error updating {file_path}: {str(e)}")
        return False

def main():
    """Main migration function."""
    print("🔄 Starting import migration...")
    print("=" * 50)
    
    # Find all Python files that might need updating
    project_root = Path(__file__).parent
    
    # Patterns to search for files
    patterns = [
        "*.py",
        "**/*.py"
    ]
    
    # Exclude certain directories
    exclude_dirs = {
        '__pycache__', '.git', 'build', 'dist', 'node_modules',
        'venv', 'env', '.venv'
    }
    
    files_to_update = []
    
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            # Skip if in excluded directory
            if any(part in exclude_dirs for part in file_path.parts):
                continue
            
            # Skip if already in new structure (src/)
            if 'src/' in str(file_path) and (
                '/gui/' in str(file_path) or 
                '/core/' in str(file_path) or 
                '/hardware/' in str(file_path) or
                '/simulation/' in str(file_path)
            ):
                continue
                
            files_to_update.append(file_path)
    
    # Update files
    updated_count = 0
    for file_path in files_to_update:
        if update_imports_in_file(file_path):
            updated_count += 1
    
    print("=" * 50)
    print(f"✅ Migration complete!")
    print(f"📝 Files processed: {len(files_to_update)}")
    print(f"🔧 Files updated: {updated_count}")
    
    # Show remaining old files that should be moved or removed
    print("\\n📋 Legacy files that might need attention:")
    legacy_files = [
        'main.py', 'main_simple.py', 'main_with_gui.py',
        'StewartPlatform.py', 'inv_kinematics.py',
        'draw_3d_spiral.py', 'generate_elliptical_points.py',
        'motor_controller.py', 'physical_stewart.py', 'hardware_config.py',
        'stewart_gui.py', 'stewart_gui_simple.py', 'stewart_gui_advanced.py',
        'stewart_gui_robust.py', 'stewart_gui_with_pybullet.py', 
        'stewart_gui_with_separate_pybullet.py'
    ]
    
    for legacy_file in legacy_files:
        file_path = project_root / legacy_file
        if file_path.exists():
            print(f"  📄 {legacy_file}")
    
    print("\\n💡 Consider moving legacy files to a 'legacy/' directory")
    print("   or removing them if no longer needed.")

if __name__ == "__main__":
    main()
