#!/usr/bin/env python3
"""
Démonstration de Trajectoires pour Plateforme de Stewart
========================================================

Ce script montre comment générer et exécuter différents types de trajectoires
avec la plateforme de Stewart.

Usage:
    python3 trajectory_demo.py [--type ellipse|spiral|sine|mixed] [--simulation]
"""

import sys
import os
import argparse
import numpy as np

# Ajouter le répertoire parent au PYTHONPATH pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.kinematics import InverseKinematics
from src.core.trajectory import (
    generate_elliptical_trajectory,
    generate_spiral_trajectory,
    generate_sinusoidal_trajectory,
    generate_demo_trajectory
)


def demonstrate_trajectory(trajectory_type: str = 'ellipse', use_simulation: bool = False):
    """
    Démontre une trajectoire spécifiée.
    
    Args:
        trajectory_type: Type de trajectoire à démontrer
        use_simulation: True pour utiliser PyBullet, False pour calculs seulement
    """
    print(f"🎯 Démonstration de trajectoire: {trajectory_type}")
    print("=" * 60)
    
    # Initialiser la cinématique inverse
    design_variables = [0.2, 0.2, 12, 12]  # [r_P, r_B, gamma_P, gamma_B]
    r_P, r_B, gamma_P, gamma_B = design_variables
    kinematics = InverseKinematics(r_B, r_P, gamma_B, gamma_P)
    
    print("✅ Cinématique inverse initialisée")
    print(f"   • Rayon base: {r_B}m")
    print(f"   • Rayon plateforme: {r_P}m")
    print(f"   • Angle base: {gamma_B}°")
    print(f"   • Angle plateforme: {gamma_P}°")
    print()
    
    # Générer la trajectoire selon le type
    if trajectory_type == 'ellipse':
        print("🔄 Génération trajectoire elliptique...")
        translations = generate_elliptical_trajectory(
            center=[0, 0, 0],
            radii=[0.01, 0.005],
            rotation_angle=0,
            n_points=20
        )
        rotations = np.zeros((len(translations), 3))  # Pas de rotation
        
    elif trajectory_type == 'spiral':
        print("🌀 Génération trajectoire spirale...")
        x, y, z = generate_spiral_trajectory(num_points=30, radius=0.005, height=0.002)
        translations = np.column_stack([x, y, z])
        
        # Rotation progressive autour de Z
        angles = np.linspace(0, 360, len(translations))
        rotations = np.column_stack([
            np.zeros(len(translations)),  # Roll
            np.zeros(len(translations)),  # Pitch
            angles                        # Yaw
        ])
        
    elif trajectory_type == 'sine':
        print("〰️ Génération trajectoire sinusoïdale...")
        translations = generate_sinusoidal_trajectory(
            amplitude=[0.01, 0.01, 0.005],
            frequency=[0.5, 0.3, 0.2],
            phase=[0, np.pi/2, np.pi/4],
            duration=5.0,
            sample_rate=10.0
        )
        
        # Rotation sinusoïdale
        n_points = len(translations)
        t = np.linspace(0, 5.0, n_points)
        rotations = np.column_stack([
            15 * np.sin(2*np.pi*0.2*t),    # Roll
            10 * np.sin(2*np.pi*0.3*t),    # Pitch
            20 * np.sin(2*np.pi*0.1*t)     # Yaw
        ])
        
    elif trajectory_type == 'mixed':
        print("🎭 Génération trajectoire mixte...")
        translations, rotations = generate_demo_trajectory('mixed', n_points=25)
        
    else:
        print(f"❌ Type de trajectoire inconnu: {trajectory_type}")
        return
    
    print(f"✅ Trajectoire générée: {len(translations)} points")
    print()
    
    # Calculer les longueurs de vérins pour chaque point
    print("🔧 Calcul des longueurs de vérins...")
    leg_lengths_history = []
    
    for i, (trans, rot) in enumerate(zip(translations, rotations)):
        try:
            leg_lengths = kinematics.solve(trans, rot)
            leg_lengths_history.append(leg_lengths)
            
            if i % 5 == 0:  # Afficher tous les 5 points
                print(f"   Point {i+1:2d}: Pos=[{trans[0]:6.3f}, {trans[1]:6.3f}, {trans[2]:6.3f}], "
                      f"Rot=[{rot[0]:5.1f}, {rot[1]:5.1f}, {rot[2]:5.1f}]")
                
        except Exception as e:
            print(f"❌ Erreur au point {i+1}: {e}")
            continue
    
    leg_lengths_array = np.array(leg_lengths_history)
    print(f"✅ Calculs terminés pour {len(leg_lengths_array)} points")
    print()
    
    # Statistiques de la trajectoire
    print("📊 STATISTIQUES DE LA TRAJECTOIRE")
    print("-" * 40)
    
    # Limites de translation
    trans_min = np.min(translations, axis=0)
    trans_max = np.max(translations, axis=0)
    print(f"Translation X: [{trans_min[0]:6.3f}, {trans_max[0]:6.3f}] m")
    print(f"Translation Y: [{trans_min[1]:6.3f}, {trans_max[1]:6.3f}] m")
    print(f"Translation Z: [{trans_min[2]:6.3f}, {trans_max[2]:6.3f}] m")
    print()
    
    # Limites de rotation
    rot_min = np.min(rotations, axis=0)
    rot_max = np.max(rotations, axis=0)
    print(f"Rotation Roll:  [{rot_min[0]:5.1f}, {rot_max[0]:5.1f}] °")
    print(f"Rotation Pitch: [{rot_min[1]:5.1f}, {rot_max[1]:5.1f}] °")
    print(f"Rotation Yaw:   [{rot_min[2]:5.1f}, {rot_max[2]:5.1f}] °")
    print()
    
    # Limites des vérins
    if len(leg_lengths_array) > 0:
        leg_min = np.min(leg_lengths_array, axis=0)
        leg_max = np.max(leg_lengths_array, axis=0)
        print("Longueurs de vérins:")
        for i in range(6):
            print(f"   Vérin {i+1}: [{leg_min[i]:.6f}, {leg_max[i]:.6f}] m")
        print()
    
    # Lancer la simulation si demandée
    if use_simulation:
        print("🚀 Lancement de la simulation PyBullet...")
        try:
            from src.core.platform import StewartPlatform
            
            # Configuration de la plateforme
            urdf_path = "simulation/urdf/Stewart.urdf"
            joint_indices = [(6, 16), (35, 17), (49, 18), (42, 19), (28, 20)]
            actuator_indices = [9, 2, 31, 45, 38, 24]
            
            # Créer et initialiser la plateforme
            platform = StewartPlatform(urdf_path, joint_indices, actuator_indices, design_variables)
            
            if platform.setup_environment(use_gui=True):
                if platform.initialize_platform():
                    print("✅ Plateforme initialisée, exécution de la trajectoire...")
                    
                    # Exécuter la trajectoire
                    for i, (trans, rot) in enumerate(zip(translations, rotations)):
                        print(f"📍 Point {i+1}/{len(translations)}")
                        platform.move_to_pose(trans, rot, duration=0.5)
                    
                    print("✅ Trajectoire terminée")
                    input("Appuyez sur Entrée pour fermer...")
                else:
                    print("❌ Échec de l'initialisation de la plateforme")
            else:
                print("❌ Échec de la configuration de l'environnement")
                
        except ImportError:
            print("❌ PyBullet non disponible pour la simulation")
        except Exception as e:
            print(f"❌ Erreur de simulation: {e}")
    
    print("🎉 Démonstration terminée!")


def main():
    """Fonction principale avec arguments de ligne de commande et mode interactif."""
    parser = argparse.ArgumentParser(
        description="Démonstration de trajectoires pour la plateforme de Stewart",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python3 trajectory_demo.py                    # Mode interactif
  python3 trajectory_demo.py --type ellipse     # Démonstration elliptique
  python3 trajectory_demo.py --type spiral --simulation  # Spirale avec visualisation
  python3 trajectory_demo.py --list             # Lister les démonstrations
        """
    )
    
    parser.add_argument('--type', choices=['ellipse', 'spiral', 'sine', 'mixed'],
                       help='Type de trajectoire à démontrer')
    parser.add_argument('--simulation', action='store_true',
                       help='Utiliser la simulation PyBullet')
    parser.add_argument('--list', action='store_true',
                       help='Lister les démonstrations disponibles')
    
    args = parser.parse_args()
    
    if args.list:
        show_available_demos()
    elif args.type:
        demonstrate_trajectory(args.type, args.simulation)
    else:
        interactive_mode()


def show_available_demos():
    """Afficher les démonstrations disponibles."""
    print("🎮 DÉMONSTRATIONS DISPONIBLES")
    print("=" * 50)
    
    demos = {
        'ellipse': {
            'name': '🔄 Trajectoire Elliptique',
            'description': 'Mouvement elliptique fluide dans le plan XY',
            'level': 'Débutant',
            'duration': '~30 secondes'
        },
        'spiral': {
            'name': '🌀 Spirale 3D',
            'description': 'Spirale ascendante avec rotation progressive',
            'level': 'Intermédiaire', 
            'duration': '~45 secondes'
        },
        'sine': {
            'name': '〰️ Ondes Sinusoïdales',
            'description': 'Motifs sinusoïdaux multi-axes',
            'level': 'Avancé',
            'duration': '~60 secondes'
        },
        'mixed': {
            'name': '🎭 Trajectoire Mixte',
            'description': 'Combinaison de plusieurs types de mouvements',
            'level': 'Expert',
            'duration': '~90 secondes'
        }
    }
    
    for demo_type, info in demos.items():
        print(f"\n{info['name']}")
        print(f"  Type: {demo_type}")
        print(f"  Niveau: {info['level']}")
        print(f"  Durée: {info['duration']}")
        print(f"  Description: {info['description']}")
    
    print(f"\n💡 UTILISATION:")
    print(f"  python3 trajectory_demo.py --type [ellipse|spiral|sine|mixed]")
    print(f"  python3 trajectory_demo.py --type ellipse --simulation")
    print(f"  python3 trajectory_demo.py  (mode interactif)")


def interactive_mode():
    """Mode interactif pour choisir la démonstration."""
    print("🎮 MODE INTERACTIF - DÉMONSTRATION DE TRAJECTOIRES")
    print("=" * 60)
    
    show_available_demos()
    
    print(f"\n" + "=" * 60)
    
    while True:
        try:
            choice = input("\n🎯 Choisissez une démonstration [ellipse/spiral/sine/mixed] ou 'quit': ").strip().lower()
            
            if choice == 'quit' or choice == 'q':
                print("👋 Au revoir!")
                break
            elif choice in ['ellipse', 'spiral', 'sine', 'mixed']:
                use_sim = input("📊 Utiliser la simulation PyBullet? [y/n]: ").strip().lower() in ['y', 'yes', 'oui']
                
                print(f"\n🚀 Lancement de la démonstration '{choice}'...")
                print("-" * 40)
                
                demonstrate_trajectory(choice, use_sim)
                
                continue_choice = input("\n🔄 Essayer une autre démonstration? [y/n]: ").strip().lower()
                if continue_choice not in ['y', 'yes', 'oui']:
                    print("👋 Au revoir!")
                    break
            else:
                print("❌ Choix invalide. Utilisez: ellipse, spiral, sine, mixed, ou quit")
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    main()
