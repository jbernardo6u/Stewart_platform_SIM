#!/usr/bin/env python3
"""
Création d'une visualisation web simple de la plateforme Stewart
Génère un fichier HTML avec animation 3D
"""

import os
import sys
import numpy as np
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.core.platform import StewartPlatform as sp
from src.core.kinematics import InverseKinematics

def generate_trajectory_data():
    """Génère les données de trajectoire pour visualisation"""
    
    # Configuration
    design_variables = [0.2, 0.2, 12, 12]
    r_P, r_B, gama_P, gama_B = design_variables
    clf_ik = InverseKinematics(r_P, r_B, gama_P, gama_B)
    
    # Trajectoire simple
    trajectory_points = []
    
    # Série de mouvements
    movements = [
        ([0, 0, 0], [0, 0, 0]),           # Position home
        ([0, 0, 0.05], [0, 0, 0]),        # Translation Z
        ([0, 0, 0.05], [15, 0, 0]),       # + Roll
        ([0, 0, 0.05], [15, 15, 0]),      # + Pitch  
        ([0, 0, 0.05], [15, 15, 20]),     # + Yaw
        ([0, 0, 0], [0, 0, 0]),           # Retour home
    ]
    
    for i, (trans, rot) in enumerate(movements):
        try:
            leg_lengths = clf_ik.solve(np.array(trans), np.array(rot))
            
            trajectory_points.append({
                'step': i,
                'translation': trans,
                'rotation': rot, 
                'leg_lengths': leg_lengths.tolist(),
                'description': f"Step {i+1}: T={trans}, R={rot}"
            })
            
        except Exception as e:
            print(f"Erreur calcul step {i}: {e}")
    
    return trajectory_points

def create_html_visualization(trajectory_data):
    """Crée un fichier HTML avec visualisation 3D"""
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Stewart Platform Visualization</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body {{ margin: 0; font-family: Arial, sans-serif; background: #1a1a1a; color: white; }}
        #container {{ width: 100%; height: 100vh; }}
        #controls {{ position: absolute; top: 10px; left: 10px; z-index: 100; background: rgba(0,0,0,0.7); padding: 15px; border-radius: 5px; }}
        button {{ padding: 8px 15px; margin: 5px; background: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer; }}
        button:hover {{ background: #45a049; }}
        #info {{ position: absolute; bottom: 10px; left: 10px; z-index: 100; background: rgba(0,0,0,0.7); padding: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="controls">
        <h3>🤖 Stewart Platform Control</h3>
        <button onclick="animateTrajectory()">▶️ Start Animation</button>
        <button onclick="resetPlatform()">🏠 Reset</button>
        <button onclick="nextStep()">⏭️ Next Step</button>
        <button onclick="prevStep()">⏮️ Prev Step</button>
    </div>
    <div id="info">
        <div id="stepInfo">Step: 1/6</div>
        <div id="positionInfo">Position: [0, 0, 0]</div>
        <div id="rotationInfo">Rotation: [0, 0, 0]</div>
    </div>

    <script>
        // Données de trajectoire
        const trajectoryData = {json.dumps(trajectory_data, indent=2)};
        
        let scene, camera, renderer, platform, legs = [];
        let currentStep = 0;
        
        function init() {{
            // Scène
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x222222);
            
            // Caméra
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0.5, 0.5, 0.5);
            camera.lookAt(0, 0, 0);
            
            // Renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.getElementById('container').appendChild(renderer.domElement);
            
            // Éclairage
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(1, 1, 1);
            directionalLight.castShadow = true;
            scene.add(directionalLight);
            
            // Base de la plateforme
            const baseGeometry = new THREE.CylinderGeometry(0.2, 0.2, 0.02, 6);
            const baseMaterial = new THREE.MeshLambertMaterial({{ color: 0x333333 }});
            const base = new THREE.Mesh(baseGeometry, baseMaterial);
            base.position.y = -0.01;
            scene.add(base);
            
            // Plateforme mobile
            const platformGeometry = new THREE.CylinderGeometry(0.15, 0.15, 0.02, 6);
            const platformMaterial = new THREE.MeshLambertMaterial({{ color: 0x4CAF50 }});
            platform = new THREE.Mesh(platformGeometry, platformMaterial);
            platform.position.set(0, 0.25, 0);
            scene.add(platform);
            
            // Vérins (6 cylindres)
            const legGeometry = new THREE.CylinderGeometry(0.01, 0.01, 0.25, 8);
            const legMaterial = new THREE.MeshLambertMaterial({{ color: 0xff6b35 }});
            
            for (let i = 0; i < 6; i++) {{
                const angle = (i * Math.PI * 2) / 6;
                const leg = new THREE.Mesh(legGeometry, legMaterial);
                
                // Position initiale des vérins
                const x = 0.18 * Math.cos(angle);
                const z = 0.18 * Math.sin(angle);
                leg.position.set(x, 0.125, z);
                
                legs.push(leg);
                scene.add(leg);
            }}
            
            updateInfo();
            animate();
        }}
        
        function updatePlatform(stepIndex) {{
            if (stepIndex >= trajectoryData.length) return;
            
            const data = trajectoryData[stepIndex];
            const [tx, ty, tz] = data.translation;
            const [rx, ry, rz] = data.rotation;
            const legLengths = data.leg_lengths;
            
            // Mise à jour position plateforme
            platform.position.set(tx, 0.25 + tz, ty);
            platform.rotation.set(
                rx * Math.PI / 180,
                rz * Math.PI / 180, 
                ry * Math.PI / 180
            );
            
            // Mise à jour longueur des vérins
            for (let i = 0; i < 6; i++) {{
                const newLength = legLengths[i];
                legs[i].scale.y = newLength / 0.25;
                legs[i].position.y = newLength / 2;
            }}
            
            currentStep = stepIndex;
            updateInfo();
        }}
        
        function updateInfo() {{
            if (currentStep < trajectoryData.length) {{
                const data = trajectoryData[currentStep];
                document.getElementById('stepInfo').textContent = `Step: ${{currentStep + 1}}/${{trajectoryData.length}}`;
                document.getElementById('positionInfo').textContent = `Position: [${{data.translation.join(', ')}}]`;
                document.getElementById('rotationInfo').textContent = `Rotation: [${{data.rotation.join(', ')}}]°`;
            }}
        }}
        
        function animateTrajectory() {{
            let step = 0;
            const interval = setInterval(() => {{
                updatePlatform(step);
                step++;
                if (step >= trajectoryData.length) {{
                    clearInterval(interval);
                }}
            }}, 1000);
        }}
        
        function resetPlatform() {{
            updatePlatform(0);
        }}
        
        function nextStep() {{
            if (currentStep < trajectoryData.length - 1) {{
                updatePlatform(currentStep + 1);
            }}
        }}
        
        function prevStep() {{
            if (currentStep > 0) {{
                updatePlatform(currentStep - 1);
            }}
        }}
        
        function animate() {{
            requestAnimationFrame(animate);
            
            // Rotation automatique de la caméra
            const time = Date.now() * 0.0005;
            camera.position.x = Math.cos(time) * 0.8;
            camera.position.z = Math.sin(time) * 0.8;
            camera.lookAt(0, 0.25, 0);
            
            renderer.render(scene, camera);
        }}
        
        // Redimensionnement
        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
        
        // Initialisation
        init();
    </script>
</body>
</html>
"""
    
    return html_content

def main():
    print("🌐 CRÉATION VISUALISATION WEB 3D")
    print("=" * 35)
    
    try:
        # Génération des données
        print("📊 Calcul des données de trajectoire...")
        trajectory_data = generate_trajectory_data()
        print(f"✅ {len(trajectory_data)} points générés")
        
        # Création du fichier HTML
        print("🎨 Création du fichier HTML...")
        html_content = create_html_visualization(trajectory_data)
        
        with open('stewart_visualization.html', 'w') as f:
            f.write(html_content)
        
        print("✅ Fichier 'stewart_visualization.html' créé!")
        print()
        print("🚀 Pour visualiser:")
        print("1. Ouvrez stewart_visualization.html dans votre navigateur")
        print("2. Ou lancez: firefox stewart_visualization.html")
        print("3. Ou lancez: google-chrome stewart_visualization.html")
        print()
        print("🎮 Contrôles:")
        print("- ▶️ Start Animation: Lance l'animation automatique")
        print("- 🏠 Reset: Retour position initiale")
        print("- ⏭️⏮️ Next/Prev: Navigation manuelle")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
