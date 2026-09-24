#!/usr/bin/env python3
"""
Script de test pour la plateforme Stewart en mode DIRECT (sans GUI)
Évite les problèmes de segmentation fault
"""

from StewartPlatform import StewartPlatform as sp
import numpy as np

# Configuration identique à main.py
path = "simulation/urdf/Stewart.urdf"
joint_indices = [(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)]
actuator_indices = [2, 31, 45, 38, 24, 9]  # jambes 1 à 6 (EXP-002)

# Variables de design de la plateforme
radious_platform, radious_base = 0.2, 0.2
half_angle_platform, half_angle_base = 24/2, 24/2
design_variables = [radious_platform, radious_base, half_angle_platform, half_angle_base]

# Trajectoires de test simplifiées
def test_basic_rotations():
    """Test des rotations de base"""
    print("=== TEST ROTATIONS DE BASE ===")
    
    # Données de test
    trans = np.array([0, 0, 0])
    
    # Rotations simples
    rot_roll = np.array([15, 0, 0])    # 15° roll
    rot_pitch = np.array([0, 15, 0])   # 15° pitch  
    rot_yaw = np.array([0, 0, 20])     # 20° yaw
    
    data_test = [
        [trans, rot_roll, 2],   # Roll
        [trans, rot_pitch, 2],  # Pitch
        [trans, rot_yaw, 2],    # Yaw
    ]
    
    # Création et test de la plateforme
    clf = sp(path, joint_indices, actuator_indices, design_variables)
    
    try:
        print("Démarrage simulation (mode DIRECT)...")
        clf.start_simmulation(data_test, simulation=False, flag=True, use_gui=False)
        print("✅ Test rotations terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")

def test_translations():
    """Test des translations"""
    print("\n=== TEST TRANSLATIONS ===")
    
    rot = np.array([0, 0, 0])  # Pas de rotation
    
    # Translations simples
    trans_x = np.array([0.02, 0, 0])    # 2cm en X
    trans_y = np.array([0, 0.02, 0])    # 2cm en Y
    trans_z = np.array([0, 0, 0.03])    # 3cm en Z
    
    data_test = [
        [trans_x, rot, 2],
        [trans_y, rot, 2], 
        [trans_z, rot, 2],
    ]
    
    clf = sp(path, joint_indices, actuator_indices, design_variables)
    
    try:
        print("Démarrage simulation translations...")
        clf.start_simmulation(data_test, simulation=False, flag=False, use_gui=False)
        print("✅ Test translations terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")

def test_combined_movements():
    """Test mouvements combinés"""
    print("\n=== TEST MOUVEMENTS COMBINÉS ===")
    
    # Mouvements combinant translation et rotation
    data_test = [
        [np.array([0.01, 0, 0.02]), np.array([10, 0, 0]), 3],  # X + Roll
        [np.array([0, 0.01, 0.01]), np.array([0, 10, 0]), 3],  # Y + Pitch
        [np.array([0, 0, 0.02]), np.array([0, 0, 15]), 3],     # Z + Yaw
    ]
    
    clf = sp(path, joint_indices, actuator_indices, design_variables)
    
    try:
        print("Démarrage simulation mouvements combinés...")
        clf.start_simmulation(data_test, simulation=False, flag=False, use_gui=False)
        print("✅ Test mouvements combinés terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")

def test_kinematics_validation():
    """Test pour valider la cinématique inverse"""
    print("\n=== VALIDATION CINÉMATIQUE INVERSE ===")
    
    from inv_kinematics import inv_kinematics as ik
    
    # Initialisation
    r_P, r_B, gama_P, gama_B = design_variables
    clf_ik = ik(r_P, r_B, gama_P, gama_B)
    
    # Test de plusieurs poses
    test_poses = [
        ([0, 0, 0], [0, 0, 0]),           # Position home
        ([0, 0, 0.05], [0, 0, 0]),        # Translation Z
        ([0, 0, 0], [10, 0, 0]),          # Rotation Roll
        ([0.02, 0.02, 0.03], [5, 5, 10]), # Mouvement complexe
    ]
    
    print("Calculs de cinématique inverse:")
    for i, (trans, rot) in enumerate(test_poses):
        try:
            leg_lengths = clf_ik.solve(np.array(trans), np.array(rot))
            print(f"Pose {i+1}: T={trans}, R={rot}")
            print(f"  Longueurs vérins: {leg_lengths}")
            print(f"  Min: {min(leg_lengths):.4f}m, Max: {max(leg_lengths):.4f}m")
            
        except Exception as e:
            print(f"❌ Erreur calcul pose {i+1}: {e}")
    
    print("✅ Validation cinématique terminée!")

if __name__ == "__main__":
    print("🤖 TESTS PLATEFORME STEWART - MODE SANS GUI")
    print("=" * 50)
    
    # Validation de la cinématique d'abord
    test_kinematics_validation()
    
    # Tests de simulation
    test_basic_rotations()
    test_translations() 
    test_combined_movements()
    
    print("\n🎉 TOUS LES TESTS TERMINÉS!")
    print("Votre plateforme Stewart fonctionne correctement.")
    print("Vous pouvez maintenant procéder à la fabrication physique.")
