#!/usr/bin/env python3
"""
Script de test pour la plateforme Stewart physique
Avec moteurs JGA25-371 DC Gearmotor
"""

from physical_stewart import PhysicalStewartPlatform
import numpy as np
import time

# Configuration de vos moteurs JGA25-371
MOTOR_CONFIG = {
    'motor_pins': [18, 19, 20, 21, 22, 23],      # Pins GPIO moteurs (exemple RPi)
    'encoder_pins': [24, 25, 26, 27, 28, 29],    # Pins encodeurs
    'specs': {
        'rpm_max': 126,
        'voltage': 12,
        'has_encoder': True,
        'gear_ratio': 371,
        'torque_nominal': 2.5
    }
}

# Paramètres géométriques de votre plateforme (identiques à la simulation)
radious_platform, radious_base = 0.2, 0.2
half_angle_platform, half_angle_base = 24/2, 24/2
design_variables = [radious_platform, radious_base, half_angle_platform, half_angle_base]

def test_basic_movements():
    """Test des mouvements de base"""
    print("=== TEST MOUVEMENTS DE BASE ===")
    
    # Création de la plateforme
    platform = PhysicalStewartPlatform(design_variables, MOTOR_CONFIG)
    
    try:
        # Initialisation
        platform.initialize_platform()
        time.sleep(2)
        
        # Test 1: Translation Z (montée/descente)
        print("\n1. Test translation Z...")
        platform.move_to_pose(np.array([0, 0, 0.05]), np.array([0, 0, 0]), duration=3)
        time.sleep(1)
        platform.return_home()
        time.sleep(2)
        
        # Test 2: Rotation Roll
        print("\n2. Test rotation Roll...")
        platform.move_to_pose(np.array([0, 0, 0]), np.array([10, 0, 0]), duration=3)
        time.sleep(1)
        platform.return_home()
        time.sleep(2)
        
        # Test 3: Rotation Pitch
        print("\n3. Test rotation Pitch...")
        platform.move_to_pose(np.array([0, 0, 0]), np.array([0, 10, 0]), duration=3)
        time.sleep(1)
        platform.return_home()
        time.sleep(2)
        
        # Test 4: Rotation Yaw
        print("\n4. Test rotation Yaw...")
        platform.move_to_pose(np.array([0, 0, 0]), np.array([0, 0, 15]), duration=3)
        time.sleep(1)
        platform.return_home()
        
        print("\nTEST TERMINÉ AVEC SUCCÈS!")
        
    except KeyboardInterrupt:
        print("\nArrêt par l'utilisateur")
        platform.emergency_stop()
    except Exception as e:
        print(f"\nErreur durant le test: {e}")
        platform.emergency_stop()

def test_trajectory():
    """Test d'une trajectoire complexe"""
    print("=== TEST TRAJECTOIRE ===")
    
    platform = PhysicalStewartPlatform(design_variables, MOTOR_CONFIG)
    
    try:
        platform.initialize_platform()
        
        # Trajectoire simple: carré en translation XY
        trajectory = [
            [np.array([0.02, 0, 0]), np.array([0, 0, 0]), 2],    # X+
            [np.array([0.02, 0.02, 0]), np.array([0, 0, 0]), 2], # X+Y+
            [np.array([0, 0.02, 0]), np.array([0, 0, 0]), 2],    # Y+
            [np.array([0, 0, 0]), np.array([0, 0, 0]), 2],       # Origine
        ]
        
        platform.execute_trajectory(trajectory)
        platform.return_home()
        
        print("TRAJECTOIRE TERMINÉE!")
        
    except KeyboardInterrupt:
        print("\nArrêt par l'utilisateur")
        platform.emergency_stop()
    except Exception as e:
        print(f"\nErreur durant la trajectoire: {e}")
        platform.emergency_stop()

def calibration_test():
    """Test de calibration des moteurs"""
    print("=== CALIBRATION DES MOTEURS ===")
    
    platform = PhysicalStewartPlatform(design_variables, MOTOR_CONFIG)
    
    try:
        platform.initialize_platform()
        
        # Test chaque moteur individuellement
        for i in range(6):
            print(f"\nTest moteur {i+1}/6")
            
            # Mouvement petit déplacement
            test_positions = [0] * 6
            test_positions[i] = 10  # 10 tours moteur
            
            platform.motor_controller.move_to_position(test_positions)
            time.sleep(2)
            
            # Retour position
            platform.motor_controller.move_to_position([0, 0, 0, 0, 0, 0])
            time.sleep(2)
        
        print("CALIBRATION TERMINÉE!")
        
    except Exception as e:
        print(f"Erreur calibration: {e}")
        platform.emergency_stop()

if __name__ == "__main__":
    print("TESTS PLATEFORME STEWART PHYSIQUE")
    print("Moteurs JGA25-371 DC Gearmotor")
    print("=================================")
    
    while True:
        print("\nChoisissez un test:")
        print("1. Mouvements de base")
        print("2. Trajectoire")
        print("3. Calibration moteurs")
        print("4. Arrêt d'urgence")
        print("0. Quitter")
        
        choice = input("\nVotre choix: ")
        
        if choice == "1":
            test_basic_movements()
        elif choice == "2":
            test_trajectory()
        elif choice == "3":
            calibration_test()
        elif choice == "4":
            print("ARRÊT D'URGENCE ACTIVÉ")
            # Ici vous pourriez ajouter un arrêt d'urgence global
        elif choice == "0":
            print("Au revoir!")
            break
        else:
            print("Choix invalide!")
