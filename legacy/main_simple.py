#!/usr/bin/env python3
"""
Version simplifiée de main.py en mode DIRECT
"""

from src.core.platform import StewartPlatform as sp
import numpy as np

# Configuration
path = "simulation/urdf/Stewart.urdf"
joint_indices = [(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)]
actuator_indices = [9, 2, 31, 45, 38, 24]
design_variables = [0.2, 0.2, 12, 12]  # radii et angles

# Test simple
trans = np.array([0, 0, 0])
rot1 = np.array([0, 0, 15])  # 15° yaw
data1 = [[trans, rot1, 2]]

# Création et test
clf = sp(path, joint_indices, actuator_indices, design_variables)

print("Démarrage test simple...")
try:
    clf.start_simmulation(data1, simulation=False, flag=True, use_gui=False)
    print("✅ Test réussi!")
except Exception as e:
    print(f"❌ Erreur: {e}")
