#!/usr/bin/env python3
"""
System Check Script for Stewart Platform
========================================

Ce script vérifie que toutes les dépendances et composants nécessaires
sont correctement installés et configurés.

Usage:
    python3 scripts/system_check.py
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SystemChecker:
    """Vérificateur de système pour la plateforme de Stewart."""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        
    def print_header(self):
        """Afficher l'en-tête."""
        print("=" * 60)
        print("🔧 STEWART PLATFORM - SYSTEM CHECK")
        print("=" * 60)
        print()
    
    def print_section(self, title):
        """Afficher une section."""
        print(f"\n📋 {title}")
        print("-" * (len(title) + 4))
    
    def check_item(self, description, check_func):
        """Exécuter une vérification."""
        try:
            result = check_func()
            if result:
                print(f"✅ {description}")
                self.checks_passed += 1
                return True
            else:
                print(f"❌ {description}")
                self.checks_failed += 1
                return False
        except Exception as e:
            print(f"❌ {description} - Error: {str(e)}")
            self.checks_failed += 1
            return False
    
    def warning(self, message):
        """Ajouter un avertissement."""
        print(f"⚠️  {message}")
        self.warnings.append(message)
    
    def check_python_version(self):
        """Vérifier la version de Python."""
        version = sys.version_info
        return version.major >= 3 and version.minor >= 7
    
    def check_required_modules(self):
        """Vérifier les modules Python requis."""
        required_modules = [
            'numpy', 'tkinter', 'threading', 'json', 'pathlib',
            'math', 'time', 'subprocess', 'argparse'
        ]
        
        all_present = True
        for module in required_modules:
            try:
                importlib.import_module(module)
            except ImportError:
                print(f"  ❌ Missing: {module}")
                all_present = False
        
        if all_present:
            print(f"  ✅ All {len(required_modules)} required modules found")
        
        return all_present
    
    def check_optional_modules(self):
        """Vérifier les modules optionnels."""
        optional_modules = {
            'pybullet': 'PyBullet simulation',
            'matplotlib': 'Plotting and visualization',
            'yaml': 'Configuration files',
            'scipy': 'Advanced mathematics'
        }
        
        available = []
        missing = []
        
        for module, description in optional_modules.items():
            try:
                importlib.import_module(module)
                available.append(f"{module} ({description})")
            except ImportError:
                missing.append(f"{module} ({description})")
        
        if available:
            print(f"  ✅ Available: {', '.join([m.split('(')[0] for m in available])}")
        
        if missing:
            print(f"  ⚠️  Optional missing: {', '.join([m.split('(')[0] for m in missing])}")
            for m in missing:
                self.warning(f"Optional module missing: {m}")
        
        return len(missing) == 0
    
    def check_project_structure(self):
        """Vérifier la structure du projet."""
        required_dirs = [
            'src/core',
            'src/gui', 
            'src/simulation',
            'src/hardware',
            'src/utils',
            'simulation/urdf',
            'configurations',
            'tests',
            'examples',
            'scripts'
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            print(f"  ❌ Missing directories: {', '.join(missing_dirs)}")
            return False
        else:
            print(f"  ✅ All {len(required_dirs)} required directories found")
            return True
    
    def check_core_files(self):
        """Vérifier les fichiers core."""
        core_files = [
            'src/core/kinematics.py',
            'src/core/platform.py',
            'src/core/trajectory.py',
            'src/gui/simple_gui.py',
            'src/gui/advanced_gui.py',
            'src/gui/pybullet_gui.py'
        ]
        
        missing_files = []
        for file_path in core_files:
            full_path = project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"  ❌ Missing files: {', '.join(missing_files)}")
            return False
        else:
            print(f"  ✅ All {len(core_files)} core files found")
            return True
    
    def check_urdf_files(self):
        """Vérifier les fichiers URDF."""
        urdf_path = project_root / "simulation/urdf/Stewart.urdf"
        meshes_dir = project_root / "simulation/meshes"
        
        if not urdf_path.exists():
            print(f"  ❌ URDF file not found: {urdf_path}")
            return False
        
        if not meshes_dir.exists():
            print(f"  ❌ Meshes directory not found: {meshes_dir}")
            return False
        
        # Compter les fichiers STL
        stl_files = list(meshes_dir.glob("*.stl"))
        print(f"  ✅ URDF file found with {len(stl_files)} mesh files")
        
        return True
    
    def check_config_files(self):
        """Vérifier les fichiers de configuration."""
        config_path = project_root / "configurations/platform_config.yaml"
        
        if not config_path.exists():
            print(f"  ⚠️  Configuration file not found: {config_path}")
            self.warning("Configuration file missing - using defaults")
            return False
        else:
            print(f"  ✅ Configuration file found")
            return True
    
    def check_imports(self):
        """Vérifier que les modules du projet peuvent être importés."""
        modules_to_test = [
            'src.core.kinematics',
            'src.core.platform', 
            'src.core.trajectory'
        ]
        
        all_imported = True
        for module in modules_to_test:
            try:
                importlib.import_module(module)
                print(f"  ✅ {module}")
            except Exception as e:
                print(f"  ❌ {module} - {str(e)}")
                all_imported = False
        
        return all_imported
    
    def check_gui_availability(self):
        """Vérifier la disponibilité des GUIs."""
        guis = ['simple_gui', 'advanced_gui', 'pybullet_gui']
        available_guis = []
        
        for gui in guis:
            try:
                module = importlib.import_module(f'src.gui.{gui}')
                if hasattr(module, 'main'):
                    available_guis.append(gui)
            except Exception:
                pass
        
        if len(available_guis) == len(guis):
            print(f"  ✅ All {len(guis)} GUIs available")
            return True
        else:
            print(f"  ⚠️  {len(available_guis)}/{len(guis)} GUIs available")
            return False
    
    def test_kinematics(self):
        """Tester la cinématique inverse."""
        try:
            from src.core.kinematics import InverseKinematics
            
            # Test simple
            ik = InverseKinematics(0.2, 0.2, 12, 12)
            test_pose = [0, 0, 0, 0, 0, 0]
            lengths = ik.calculate(test_pose)
            
            if len(lengths) == 6 and all(isinstance(l, (int, float)) for l in lengths):
                print(f"  ✅ Kinematics calculation successful")
                return True
            else:
                print(f"  ❌ Kinematics returned invalid result")
                return False
        except Exception as e:
            print(f"  ❌ Kinematics test failed: {str(e)}")
            return False
    
    def print_summary(self):
        """Afficher le résumé."""
        print("\n" + "=" * 60)
        print("📊 SYSTEM CHECK SUMMARY")
        print("=" * 60)
        
        total_checks = self.checks_passed + self.checks_failed
        success_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0
        
        print(f"✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        print(f"\n🎯 RECOMMENDATION:")
        if self.checks_failed == 0:
            print("   🚀 System is ready! All simulations should work correctly.")
        elif self.checks_failed <= 2:
            print("   ⚡ System is mostly ready. Check failed items above.")
        else:
            print("   🔧 System needs attention. Please fix failed checks before using.")
        
        print(f"\n💡 NEXT STEPS:")
        print(f"   • Run 'python3 scripts/simulation_manager.py' for simulation access")
        print(f"   • Try 'python3 scripts/quick_simulation.py' for quick demos")
        print(f"   • Use 'python3 scripts/launcher.py' for full project access")


def main():
    """Fonction principale."""
    checker = SystemChecker()
    checker.print_header()
    
    # Vérifications système
    checker.print_section("Python Environment")
    checker.check_item("Python 3.7+", checker.check_python_version)
    checker.check_item("Required modules", checker.check_required_modules)
    checker.check_item("Optional modules", checker.check_optional_modules)
    
    # Vérifications structure
    checker.print_section("Project Structure")
    checker.check_item("Directory structure", checker.check_project_structure)
    checker.check_item("Core files", checker.check_core_files)
    checker.check_item("URDF and meshes", checker.check_urdf_files)
    checker.check_item("Configuration files", checker.check_config_files)
    
    # Vérifications fonctionnelles
    checker.print_section("Functionality")
    checker.check_item("Module imports", checker.check_imports)
    checker.check_item("GUI availability", checker.check_gui_availability)
    checker.check_item("Kinematics calculation", checker.test_kinematics)
    
    # Résumé
    checker.print_summary()


if __name__ == "__main__":
    main()
