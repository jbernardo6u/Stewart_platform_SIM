#!/usr/bin/env python3
"""
Simulation avec enregistrement vidéo MP4
Alternative à la visualisation en temps réel
"""

from src.core.platform import StewartPlatform as sp, DEFAULT_JOINT_INDICES, DEFAULT_ACTUATOR_INDICES
import numpy as np

# Configuration
path = "simulation/urdf/Stewart.urdf"
joint_indices = DEFAULT_JOINT_INDICES
actuator_indices = DEFAULT_ACTUATOR_INDICES
design_variables = [0.2, 0.2, 12, 12]

# Trajectoire de démonstration
def create_demo_trajectory():
    """Crée une trajectoire de démonstration spectaculaire"""
    trajectory = []
    
    # 1. Montée progressive
    for z in np.linspace(0, 0.08, 5):
        trajectory.append([np.array([0, 0, z]), np.array([0, 0, 0]), 1])
    
    # 2. Rotations combinées
    for angle in np.linspace(0, 360, 12):
        roll = 15 * np.sin(np.radians(angle))
        pitch = 15 * np.cos(np.radians(angle))
        yaw = angle / 12  # Rotation lente
        trajectory.append([np.array([0, 0, 0.05]), np.array([roll, pitch, yaw]), 1])
    
    # 3. Mouvement de translation circulaire
    for angle in np.linspace(0, 2*np.pi, 16):
        x = 0.03 * np.cos(angle)
        y = 0.03 * np.sin(angle)
        trajectory.append([np.array([x, y, 0.04]), np.array([0, 0, 0]), 0.8])
    
    # 4. Retour à la position d'origine
    trajectory.append([np.array([0, 0, 0]), np.array([0, 0, 0]), 2])
    
    return trajectory

print("🎬 CRÉATION DE VIDÉO DE SIMULATION")
print("=" * 40)

# Création des trajectoires
demo_trajectory = create_demo_trajectory()
print(f"Trajectoire créée: {len(demo_trajectory)} points")

# Simulation avec enregistrement
clf = sp(path, joint_indices, actuator_indices, design_variables)

try:
    print("🎥 Démarrage enregistrement vidéo...")
    clf.start_simmulation(demo_trajectory, simulation=True, flag=False, use_gui=False)
    print("✅ Vidéo 'simulation.mp4' créée avec succès!")
    print("📁 Vous pouvez maintenant ouvrir le fichier simulation.mp4")
    
except Exception as e:
    print(f"❌ Erreur durant l'enregistrement: {e}")

print("\n🎯 Pour visualiser:")
print("1. Ouvrez simulation.mp4 avec un lecteur vidéo")
print("2. Ou utilisez: vlc simulation.mp4")
print("3. Ou utilisez: ffplay simulation.mp4")
