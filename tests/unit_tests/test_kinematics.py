"""
Tests unitaires pour la cinématique inverse
==========================================

Ce module contient les tests pour valider le bon fonctionnement
de la classe InverseKinematics.
"""

import unittest
import numpy as np
import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.kinematics import InverseKinematics


class TestInverseKinematics(unittest.TestCase):
    """Tests pour la classe InverseKinematics."""
    
    def setUp(self):
        """Configuration avant chaque test."""
        self.radius_base = 0.2
        self.radius_platform = 0.2
        self.gamma_base = 12
        self.gamma_platform = 12
        
        self.kinematics = InverseKinematics(
            self.radius_base,
            self.radius_platform,
            self.gamma_base,
            self.gamma_platform
        )
    
    def test_initialization(self):
        """Test l'initialisation de la classe."""
        self.assertEqual(self.kinematics.rb, self.radius_base)
        self.assertEqual(self.kinematics.rp, self.radius_platform)
        self.assertAlmostEqual(self.kinematics.gamma_B, np.deg2rad(self.gamma_base))
        self.assertAlmostEqual(self.kinematics.gamma_P, np.deg2rad(self.gamma_platform))
        
        # Vérifier la position de référence
        expected_home = np.array([0, 0, 0.257547])
        np.testing.assert_array_almost_equal(self.kinematics.home_pos, expected_home)
    
    def test_rotation_matrices(self):
        """Test les matrices de rotation."""
        # Test rotation X de 90°
        R_x = InverseKinematics.rotation_matrix_x(90)
        expected_x = np.array([
            [1, 0, 0],
            [0, 0, -1],
            [0, 1, 0]
        ])
        np.testing.assert_array_almost_equal(R_x, expected_x)
        
        # Test rotation Y de 90°
        R_y = InverseKinematics.rotation_matrix_y(90)
        expected_y = np.array([
            [0, 0, 1],
            [0, 1, 0],
            [-1, 0, 0]
        ])
        np.testing.assert_array_almost_equal(R_y, expected_y)
        
        # Test rotation Z de 90°
        R_z = InverseKinematics.rotation_matrix_z(90)
        expected_z = np.array([
            [0, -1, 0],
            [1, 0, 0],
            [0, 0, 1]
        ])
        np.testing.assert_array_almost_equal(R_z, expected_z)
    
    def test_attachment_points(self):
        """Test le calcul des points d'attache."""
        P, B = self.kinematics.calculate_attachment_points()
        
        # Vérifier les dimensions
        self.assertEqual(P.shape, (3, 6))
        self.assertEqual(B.shape, (3, 6))
        
        # Vérifier que tous les points sont sur les cercles appropriés
        for i in range(6):
            # Distance à l'origine pour la plateforme
            dist_P = np.sqrt(P[0, i]**2 + P[1, i]**2)
            self.assertAlmostEqual(dist_P, self.radius_platform, places=6)
            
            # Distance à l'origine pour la base
            dist_B = np.sqrt(B[0, i]**2 + B[1, i]**2)
            self.assertAlmostEqual(dist_B, self.radius_base, places=6)
            
            # Coordonnée Z doit être 0
            self.assertAlmostEqual(P[2, i], 0, places=6)
            self.assertAlmostEqual(B[2, i], 0, places=6)
    
    def test_solve_neutral_position(self):
        """Test la résolution pour la position neutre."""
        translation = [0, 0, 0]
        rotation = [0, 0, 0]
        
        leg_lengths = self.kinematics.solve(translation, rotation)
        
        # Vérifier le nombre de vérins
        self.assertEqual(len(leg_lengths), 6)
        
        # Pour une position neutre, toutes les longueurs devraient être identiques
        expected_length = np.linalg.norm(self.kinematics.home_pos)
        for length in leg_lengths:
            self.assertAlmostEqual(length, expected_length, places=4)
    
    def test_solve_translation_x(self):
        """Test la résolution pour une translation en X."""
        translation = [0.01, 0, 0]  # 1cm en X
        rotation = [0, 0, 0]
        
        leg_lengths = self.kinematics.solve(translation, rotation)
        
        # Vérifier que les longueurs ont changé
        self.assertEqual(len(leg_lengths), 6)
        
        # Les longueurs ne devraient pas toutes être identiques
        self.assertFalse(np.allclose(leg_lengths, leg_lengths[0]))
    
    def test_solve_rotation_z(self):
        """Test la résolution pour une rotation autour de Z."""
        translation = [0, 0, 0]
        rotation = [0, 0, 15]  # 15° en yaw
        
        leg_lengths = self.kinematics.solve(translation, rotation)
        
        # Vérifier que les longueurs ont changé
        self.assertEqual(len(leg_lengths), 6)
        
        # Pour une rotation pure autour de Z, la variation devrait être symétrique
        self.assertTrue(len(set(np.round(leg_lengths, 6))) > 1)
    
    def test_solve_combined_motion(self):
        """Test la résolution pour un mouvement combiné."""
        translation = [0.005, 0.005, 0.002]
        rotation = [5, 5, 10]
        
        leg_lengths = self.kinematics.solve(translation, rotation)
        
        # Vérifier les résultats
        self.assertEqual(len(leg_lengths), 6)
        
        # Toutes les longueurs doivent être positives
        self.assertTrue(np.all(leg_lengths > 0))
        
        # Les longueurs doivent être dans une plage raisonnable
        self.assertTrue(np.all(leg_lengths > 0.1))  # Plus de 10cm
        self.assertTrue(np.all(leg_lengths < 0.4))  # Moins de 40cm
    
    def test_leg_positions(self):
        """Test l'obtention des positions des vérins."""
        translation = [0, 0, 0]
        rotation = [0, 0, 0]
        
        # Résoudre d'abord
        self.kinematics.solve(translation, rotation)
        
        # Obtenir les positions
        positions = self.kinematics.get_leg_positions()
        
        self.assertIsNotNone(positions)
        self.assertEqual(positions.shape, (3, 6))
    
    def test_input_validation(self):
        """Test la validation des entrées."""
        # Test avec des listes
        leg_lengths_list = self.kinematics.solve([0, 0, 0], [0, 0, 0])
        
        # Test avec des arrays numpy
        leg_lengths_array = self.kinematics.solve(
            np.array([0, 0, 0]), 
            np.array([0, 0, 0])
        )
        
        # Les résultats doivent être identiques
        np.testing.assert_array_almost_equal(leg_lengths_list, leg_lengths_array)
    
    def test_large_movements(self):
        """Test avec des mouvements plus importants."""
        # Translation importante
        translation = [0.02, 0.02, 0.01]  # 2cm, 2cm, 1cm
        rotation = [20, 20, 30]  # 20°, 20°, 30°
        
        try:
            leg_lengths = self.kinematics.solve(translation, rotation)
            
            # Vérifier que la solution existe
            self.assertEqual(len(leg_lengths), 6)
            self.assertTrue(np.all(leg_lengths > 0))
            
        except Exception as e:
            self.fail(f"La résolution a échoué pour des mouvements importants: {e}")


class TestCompatibility(unittest.TestCase):
    """Tests de compatibilité avec l'ancien code."""
    
    def test_old_class_name(self):
        """Test que l'ancien nom de classe fonctionne toujours."""
        from src.core.kinematics import inv_kinematics
        
        # L'alias doit pointer vers la nouvelle classe
        self.assertEqual(inv_kinematics, InverseKinematics)
        
        # Test d'utilisation
        ik = inv_kinematics(0.2, 0.2, 12, 12)
        leg_lengths = ik.solve([0, 0, 0], [0, 0, 0])
        
        self.assertEqual(len(leg_lengths), 6)


if __name__ == '__main__':
    # Configuration pour l'exécution des tests
    unittest.main(verbosity=2)
