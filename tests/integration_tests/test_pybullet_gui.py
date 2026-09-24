#!/usr/bin/env python3
"""
Test simple pour vérifier que PyBullet GUI fonctionne
"""

import pybullet as p
import pybullet_data
import time
import os

def test_pybullet_gui():
    """Test simple de PyBullet avec interface graphique"""
    
    print("🔍 Testing PyBullet GUI...")
    
    # Configuration environnement
    os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
    os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
    
    try:
        # Tentative de connexion GUI
        print("📡 Attempting to connect to PyBullet GUI...")
        physicsClient = p.connect(p.GUI, options="--width=1280 --height=720")
        print("✅ Connected to PyBullet GUI successfully!")
        
        # Configuration de l'environnement
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        
        # Charger un plan
        planeId = p.loadURDF("plane.urdf")
        
        # Charger le Stewart Platform
        cubeStartPos = [0, 0, 0]
        cubeStartOrientation = p.getQuaternionFromEuler([0, 0, 0])
        
        stewart_path = "simulation/urdf/Stewart.urdf"
        if os.path.exists(stewart_path):
            robotId = p.loadURDF(stewart_path, cubeStartPos, cubeStartOrientation)
            print("✅ Stewart Platform loaded successfully!")
        else:
            print("⚠️ Stewart.urdf not found, loading a cube instead...")
            robotId = p.loadURDF("cube.urdf", cubeStartPos, cubeStartOrientation)
        
        # Configuration caméra
        p.configureDebugVisualizer(p.COV_ENABLE_GUI, 1)
        p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 1)
        
        print("🎮 PyBullet GUI is ready!")
        print("📝 You should see a PyBullet window with the Stewart Platform.")
        print("💡 The simulation will run for 10 seconds...")
        
        # Simulation simple
        for i in range(2400):  # 10 seconds à 240 FPS
            p.stepSimulation()
            time.sleep(1./240.)
            
            if i % 240 == 0:  # Every second
                print(f"⏱️  Simulation running... {i//240 + 1}/10 seconds")
        
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ PyBullet GUI test failed: {str(e)}")
        print("💡 Falling back to DIRECT mode...")
        
        try:
            p.disconnect()
        except:
            pass
            
        # Fallback en mode DIRECT
        physicsClient = p.connect(p.DIRECT)
        print("✅ Connected to PyBullet DIRECT mode")
        
    finally:
        try:
            p.disconnect()
            print("🔌 Disconnected from PyBullet")
        except:
            pass

if __name__ == "__main__":
    test_pybullet_gui()
