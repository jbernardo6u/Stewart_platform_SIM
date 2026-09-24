#!/usr/bin/env python3
"""
Version de main.py avec GUI sécurisée
Utilise des techniques pour éviter les segfaults
"""

from src.core.platform import StewartPlatform as sp
import numpy as np
import os

# Configuration
path = "simulation/urdf/Stewart.urdf"
joint_indices = [(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)]
actuator_indices = [9, 2, 31, 45, 38, 24]
design_variables = [0.2, 0.2, 12, 12]

# Variables d'environnement pour stabiliser PyBullet GUI
os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'

# Test simple avec GUI
trans = np.array([0, 0, 0])
rot1 = np.array([0, 0, 30])  # 30° yaw
rot2 = np.array([15, 0, 0])  # 15° roll
rot3 = np.array([0, 20, 0])  # 20° pitch

data1 = [
    [trans, rot1, 3],
    [trans, rot2, 3], 
    [trans, rot3, 3]
]

print("🤖 DÉMARRAGE SIMULATION AVEC GUI")
print("Tentative d'ouverture de l'interface graphique...")

# Création de la plateforme
clf = sp(path, joint_indices, actuator_indices, design_variables)

try:
    # Tentative avec GUI
    clf.start_simmulation(data1, simulation=False, flag=True, use_gui=True)
    print("✅ Simulation GUI réussie!")
    
except Exception as e:
    print(f"❌ Erreur GUI: {e}")
    print("🔄 Basculement en mode DIRECT...")
    clf.start_simmulation(data1, simulation=False, flag=True, use_gui=False)
    print("✅ Simulation DIRECT réussie!")
