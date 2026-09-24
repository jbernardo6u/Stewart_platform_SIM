# Configuration matérielle pour plateforme Stewart physique
# JGA25-371 DC Gearmotor with Encoder (126 RPM at 12 V)

## COMPOSANTS NÉCESSAIRES

### 1. MICROCONTRÔLEUR
# Option A: Raspberry Pi 4
#   - 40 pins GPIO
#   - Python natif
#   - Puissance de calcul suffisante

# Option B: Arduino Mega 2560
#   - 54 pins digitales
#   - 16 pins PWM
#   - Communication série avec PC

### 2. DRIVERS MOTEUR (6x)
# L298N Dual H-Bridge ou équivalent
# Spécifications:
#   - Tension: 5V-35V (compatible 12V)
#   - Courant: 2A par canal
#   - Contrôle PWM + Direction

### 3. ALIMENTATION
# Alimentation 12V/10A minimum
# Régulateur 5V pour logique

### 4. CAPTEURS
# Encodeurs intégrés aux moteurs JGA25-371
# Résolution: ~7 pulses/rev (à vérifier)

### 5. MÉCANISME LINÉAIRE
# Option A: Vis à billes (précision)
# Option B: Vis trapézoïdale (économique)
# Pas recommandé: 2mm/tour

### 6. STRUCTURE MÉCANIQUE
# Impression 3D:
#   - Base hexagonale (fichier .stl disponible)
#   - Plateforme mobile hexagonale
#   - 6x supports moteur
#   - 6x joints universels
#   - 6x tiges de liaison

## CONNEXIONS ÉLECTRIQUES

### Raspberry Pi GPIO (exemple)
MOTOR_PINS = {
    'Motor1_PWM': 18,    'Motor1_DIR1': 19,   'Motor1_DIR2': 20,
    'Motor2_PWM': 21,    'Motor2_DIR1': 22,   'Motor2_DIR2': 23,
    'Motor3_PWM': 24,    'Motor3_DIR1': 25,   'Motor3_DIR2': 8,
    'Motor4_PWM': 7,     'Motor4_DIR1': 1,    'Motor4_DIR2': 12,
    'Motor5_PWM': 16,    'Motor5_DIR1': 20,   'Motor5_DIR2': 21,
    'Motor6_PWM': 6,     'Motor6_DIR1': 13,   'Motor6_DIR2': 19,
}

ENCODER_PINS = {
    'Encoder1_A': 2,   'Encoder1_B': 3,
    'Encoder2_A': 4,   'Encoder2_B': 17,
    'Encoder3_A': 27,  'Encoder3_B': 22,
    'Encoder4_A': 10,  'Encoder4_B': 9,
    'Encoder5_A': 11,  'Encoder5_B': 5,
    'Encoder6_A': 6,   'Encoder6_B': 13,
}

## CARACTÉRISTIQUES MÉCANIQUES
MECHANICAL_SPECS = {
    'motor_torque': 2.5,        # Nm @ 12V
    'gear_ratio': 371,          # 1:371
    'max_rpm_output': 126/371,  # RPM en sortie réducteur
    'thread_pitch': 2.0,        # mm/tour (vis)
    'max_linear_speed': 0.68,   # mm/s théorique
    'max_stroke': 100,          # mm course max
    'platform_radius': 0.2,    # mètres
    'base_radius': 0.2,         # mètres
    'home_height': 0.257547,    # mètres (position repos)
}

## SÉCURITÉ
SAFETY_LIMITS = {
    'max_translation_x': 0.05,  # ±50mm
    'max_translation_y': 0.05,  # ±50mm  
    'max_translation_z': 0.10,  # 0-100mm
    'max_rotation_roll': 30,    # ±30°
    'max_rotation_pitch': 30,   # ±30°
    'max_rotation_yaw': 45,     # ±45°
    'max_motor_current': 2.0,   # A
    'emergency_stop_pin': 26,   # GPIO pin
}

## CALIBRATION
CALIBRATION_PARAMS = {
    'encoder_pulses_per_rev': 7,      # À mesurer
    'backlash_compensation': 0.1,     # mm
    'pid_kp': 1.0,                    # Proportionnel
    'pid_ki': 0.1,                    # Intégral  
    'pid_kd': 0.05,                   # Dérivé
    'max_acceleration': 10,           # mm/s²
}
