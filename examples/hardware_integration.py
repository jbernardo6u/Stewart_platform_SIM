#!/usr/bin/env python3
"""
Exemple d'Intégration Hardware pour Plateforme de Stewart
=========================================================

Ce script montre comment intégrer la plateforme de Stewart avec du matériel réel,
incluant la communication avec les moteurs et les capteurs.

Usage:
    python3 hardware_integration.py [--test] [--calibrate]
"""

import sys
import os
import argparse
import time
import numpy as np

# Ajouter le répertoire parent au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.kinematics import InverseKinematics
from src.core.trajectory import generate_test_sequence
from src.hardware.physical_platform import PhysicalStewartPlatform
from src.hardware.motor_controller import MotorController


def test_hardware_connection():
    """
    Test la connexion avec le matériel.
    
    Returns:
        True si la connexion est réussie, False sinon
    """
    print("🔌 Test de connexion hardware...")
    
    try:
        # Tenter de créer une instance de la plateforme physique
        platform = PhysicalStewartPlatform()
        
        if platform.connect():
            print("✅ Connexion hardware réussie")
            
            # Test de communication basique
            print("📡 Test de communication...")
            if platform.test_communication():
                print("✅ Communication hardware OK")
                platform.disconnect()
                return True
            else:
                print("❌ Échec de communication")
                platform.disconnect()
                return False
        else:
            print("❌ Échec de connexion hardware")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False


def calibrate_platform():
    """
    Effectue la calibration de la plateforme.
    """
    print("🎯 Calibration de la plateforme...")
    
    try:
        platform = PhysicalStewartPlatform()
        
        if not platform.connect():
            print("❌ Impossible de se connecter pour la calibration")
            return
        
        print("🏠 Retour à la position de référence...")
        platform.go_home()
        time.sleep(2)
        
        print("📏 Calibration des positions extrêmes...")
        
        # Séquence de calibration
        calibration_positions = [
            [0, 0, 0],          # Position centrale
            [0.01, 0, 0],       # X max
            [-0.01, 0, 0],      # X min
            [0, 0.01, 0],       # Y max
            [0, -0.01, 0],      # Y min
            [0, 0, 0.005],      # Z max
            [0, 0, -0.005],     # Z min
            [0, 0, 0],          # Retour centre
        ]
        
        calibration_rotations = [
            [0, 0, 0],          # Neutre
            [10, 0, 0],         # Roll max
            [-10, 0, 0],        # Roll min
            [0, 10, 0],         # Pitch max
            [0, -10, 0],        # Pitch min
            [0, 0, 15],         # Yaw max
            [0, 0, -15],        # Yaw min
            [0, 0, 0],          # Retour neutre
        ]
        
        for i, (pos, rot) in enumerate(zip(calibration_positions, calibration_rotations)):
            print(f"   Position {i+1}/8: {pos}, {rot}")
            platform.move_to_position(pos, rot)
            time.sleep(1)  # Pause entre les mouvements
            
            # Lire la position réelle si des capteurs sont disponibles
            try:
                actual_pos = platform.get_current_position()
                print(f"     Position réelle: {actual_pos}")
            except:
                pass
        
        print("✅ Calibration terminée")
        platform.disconnect()
        
    except Exception as e:
        print(f"❌ Erreur de calibration: {e}")


def run_hardware_demo():
    """
    Exécute une démonstration avec le matériel réel.
    """
    print("🎮 Démonstration hardware...")
    
    try:
        # Initialiser la cinématique
        design_variables = [0.2, 0.2, 12, 12]
        r_P, r_B, gamma_P, gamma_B = design_variables
        kinematics = InverseKinematics(r_B, r_P, gamma_B, gamma_P)
        
        # Initialiser la plateforme physique
        platform = PhysicalStewartPlatform()
        
        if not platform.connect():
            print("❌ Connexion impossible")
            return
        
        print("✅ Plateforme connectée")
        
        # Générer une séquence de test
        translations, rotations = generate_test_sequence()
        
        print(f"🎯 Exécution de {len(translations)} mouvements...")
        
        for i, (trans, rot) in enumerate(zip(translations, rotations)):
            print(f"\n📍 Mouvement {i+1}/{len(translations)}")
            print(f"   Translation: [{trans[0]:6.3f}, {trans[1]:6.3f}, {trans[2]:6.3f}]")
            print(f"   Rotation:    [{rot[0]:5.1f}, {rot[1]:5.1f}, {rot[2]:5.1f}]")
            
            # Calculer les longueurs de vérins
            leg_lengths = kinematics.solve(trans, rot)
            print(f"   Vérins:      {leg_lengths}")
            
            # Déplacer la plateforme
            platform.move_to_position(trans, rot)
            
            # Attendre la fin du mouvement
            time.sleep(2)
            
            # Vérifier la position atteinte
            try:
                current_pos = platform.get_current_position()
                print(f"   Position atteinte: {current_pos}")
            except:
                print("   (Position réelle non disponible)")
        
        print("\n🏠 Retour à la position initiale...")
        platform.go_home()
        
        print("✅ Démonstration terminée")
        platform.disconnect()
        
    except Exception as e:
        print(f"❌ Erreur de démonstration: {e}")


def monitor_platform():
    """
    Surveille la plateforme en temps réel.
    """
    print("📊 Surveillance de la plateforme...")
    print("Appuyez sur Ctrl+C pour arrêter")
    
    try:
        platform = PhysicalStewartPlatform()
        
        if not platform.connect():
            print("❌ Connexion impossible")
            return
        
        print("✅ Surveillance démarrée")
        
        while True:
            try:
                # Lire les données de la plateforme
                position = platform.get_current_position()
                leg_lengths = platform.get_leg_lengths()
                motor_status = platform.get_motor_status()
                
                # Afficher les informations
                print(f"\r🔄 Pos: {position} | Vérins: {leg_lengths} | Moteurs: {motor_status}", end="")
                
                time.sleep(0.1)  # Mise à jour 10Hz
                
            except KeyboardInterrupt:
                print("\n⏹️ Surveillance arrêtée")
                break
            except Exception as e:
                print(f"\n⚠️ Erreur de lecture: {e}")
                time.sleep(1)
        
        platform.disconnect()
        
    except Exception as e:
        print(f"❌ Erreur de surveillance: {e}")


def main():
    """Fonction principale avec arguments de ligne de commande."""
    parser = argparse.ArgumentParser(description="Intégration hardware Stewart Platform")
    parser.add_argument('--test', action='store_true', help='Tester la connexion hardware')
    parser.add_argument('--calibrate', action='store_true', help='Calibrer la plateforme')
    parser.add_argument('--demo', action='store_true', help='Exécuter une démonstration')
    parser.add_argument('--monitor', action='store_true', help='Surveiller la plateforme')
    
    args = parser.parse_args()
    
    print("🤖 INTÉGRATION HARDWARE STEWART PLATFORM")
    print("=" * 60)
    print()
    
    # Vérifier qu'au moins une action est demandée
    if not any([args.test, args.calibrate, args.demo, args.monitor]):
        print("ℹ️ Aucune action spécifiée. Exécution du test de connexion...")
        args.test = True
    
    # Exécuter les actions demandées
    if args.test:
        if test_hardware_connection():
            print("🎉 Hardware prêt pour utilisation!")
        else:
            print("❌ Problème hardware détecté")
            return
    
    if args.calibrate:
        calibrate_platform()
    
    if args.demo:
        run_hardware_demo()
    
    if args.monitor:
        monitor_platform()
    
    print("\n🎉 Intégration hardware terminée!")


if __name__ == "__main__":
    main()
