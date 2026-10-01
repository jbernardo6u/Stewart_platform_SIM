"""
Génération du monde Gazebo du démonstrateur REM
===============================================

Tout est calculé depuis ``configurations/bench_rem.yaml`` (aucune cote en dur dans le
SDF) : base, plateforme, 12 éléments de vérins (corps et tige), caméra embarquée aux
intrinsèques du banc, marqueur ArUco texturé et son support.

Les corps mobiles sont **statiques** : leur pose est imposée à chaque pas par le nœud
``virtual_hardware`` (service ``/world/<monde>/set_pose_vector``) à partir de la FK des
codeurs simulés. Gazebo sert au rendu des capteurs, pas à la dynamique (voir EXP-009).

Sortie : ``<dossier>/rem_bench.sdf``, ``<dossier>/markers/aruco_<id>.{png,obj,mtl}``.
"""

import os
from typing import Dict

import numpy as np

from .geometry import BenchGeometry
from .scene import BenchScene, leg_visual_poses, matrix_to_sdf_rpy

# Aspect des vérins (visuel seulement, sans effet sur la cinématique)
LEG_BODY_LENGTH = 0.13
LEG_ROD_LENGTH = 0.16
LEG_BODY_RADIUS = 0.009
LEG_ROD_RADIUS = 0.004
MARKER_MARGIN_CELLS = 1          # zone blanche autour du marqueur, en cellules ArUco
MARKER_PIXELS_PER_CELL = 50
# Gazebo place l'origine des pixels au coin du pixel, OpenCV (calib_int.npz) au centre :
# image décalée de −0,5 px sans cette correction (mesuré, EXP-009).
GZ_PIXEL_OFFSET = 0.5


def _pose(p, R) -> str:
    rpy = matrix_to_sdf_rpy(R)
    return ' '.join(f'{v:.6f}' for v in (*p, *rpy))


def _material(rgb) -> str:
    c = ' '.join(f'{v:.3f}' for v in rgb)
    return f'<material><ambient>{c} 1</ambient><diffuse>{c} 1</diffuse><specular>0.2 0.2 0.2 1</specular></material>'


def _cylinder_model(name, p, R, radius, length, rgb) -> str:
    return f"""
    <model name="{name}"><static>true</static><pose>{_pose(p, R)}</pose>
      <link name="link"><visual name="visual">
        <geometry><cylinder><radius>{radius}</radius><length>{length}</length></cylinder></geometry>
        {_material(rgb)}</visual></link></model>"""


def marker_bits(marker_id: int, dictionary: str) -> np.ndarray:
    """Cellules du marqueur (6x6 avec la bordure), 1 = noir, ligne 0 en haut."""
    import cv2   # uniquement pour lire le dictionnaire ArUco
    aruco = cv2.aruco
    dico = aruco.getPredefinedDictionary(getattr(aruco, dictionary))
    draw = aruco.generateImageMarker if hasattr(aruco, 'generateImageMarker') else aruco.drawMarker
    return (draw(dico, marker_id, 6) < 128).astype(int)


def marker_assets(marker_id: int, dictionary: str, size_m: float, out_dir: str) -> Dict[str, str]:
    """
    Marqueur en **géométrie** : un carré blanc (marge comprise) et un quad noir par cellule.

    Un marqueur texturé est rendu trop petit d'environ 0,5 px par bord (filtrage de la
    texture en réduction) : biais de +2,4 % sur la distance estimée à 30 cm (EXP-009).
    Des quads rastérisés n'ont pas ce biais. Le PNG n'est produit que pour la documentation.
    Repère : plan y-z, normale sortante −x ; vu depuis −x, la droite est −y, le haut +z.
    """
    os.makedirs(out_dir, exist_ok=True)
    bits = marker_bits(marker_id, dictionary)
    cells = bits.shape[0]
    cell = size_m / cells
    stem = f'aruco_{marker_id}'
    import cv2
    img = np.kron(1 - bits, np.ones((MARKER_PIXELS_PER_CELL, MARKER_PIXELS_PER_CELL))).astype(np.uint8) * 255
    margin = MARKER_MARGIN_CELLS * MARKER_PIXELS_PER_CELL
    img = cv2.copyMakeBorder(img, margin, margin, margin, margin, cv2.BORDER_CONSTANT, value=255)
    png = os.path.join(out_dir, stem + '.png')
    cv2.imwrite(png, img)

    vertices, faces = [], {'white': [], 'black': []}

    def quad(y_left, y_right, z_bottom, z_top, x, material):
        base = len(vertices) + 1
        vertices.extend([(x, y_left, z_bottom), (x, y_right, z_bottom), (x, y_right, z_top), (x, y_left, z_top)])
        faces[material].append((base, base + 1, base + 2, base + 3))

    h = size_m / 2 + MARKER_MARGIN_CELLS * cell
    quad(h, -h, -h, h, 0.0, 'white')
    for row in range(cells):
        for col in range(cells):
            if bits[row, col]:
                y_left = size_m / 2 - col * cell
                z_top = size_m / 2 - row * cell
                quad(y_left, y_left - cell, z_top - cell, z_top, -0.0002, 'black')

    lines = [f'# Marqueur ArUco {dictionary} id {marker_id}, carré noir de {size_m * 1000:.1f} mm',
             f'mtllib {stem}.mtl', f'o {stem}']
    lines += [f'v {x:.6f} {y:.6f} {z:.6f}' for x, y, z in vertices]
    lines.append('vn -1 0 0')
    for material in ('white', 'black'):
        lines.append(f'usemtl {stem}_{material}')
        for a, b, c, d in faces[material]:
            lines += [f'f {a}//1 {b}//1 {c}//1', f'f {a}//1 {c}//1 {d}//1']
    mtl = (f'newmtl {stem}_white\nKa 1 1 1\nKd 1 1 1\nKs 0 0 0\nillum 1\n\n'
           f'newmtl {stem}_black\nKa 0 0 0\nKd 0.02 0.02 0.02\nKs 0 0 0\nillum 1\n')
    paths = {'png': png, 'obj': os.path.join(out_dir, stem + '.obj'), 'mtl': os.path.join(out_dir, stem + '.mtl')}
    with open(paths['obj'], 'w') as f:
        f.write('\n'.join(lines) + '\n')
    with open(paths['mtl'], 'w') as f:
        f.write(mtl)
    return paths


def generate_world(config: dict, out_dir: str) -> str:
    """Écrit le monde SDF et les marqueurs ; renvoie le chemin du monde."""
    geo, scene = BenchGeometry(config), BenchScene(config)
    cam, mk, gz = config['camera'], config['markers']['target'], config['gazebo']
    world = gz['world_name']

    home = geo.pose_from_encoders(np.zeros(6))      # pose physique à codeurs nuls
    R = home.rotation_matrix
    centre = geo.platform_position_world(home.translation)
    base_W, top_W = geo.legs_world(home.translation, R)

    rb = config['geometry']['radius_base']
    rp = config['geometry']['radius_platform']
    legs = ''
    for i, (pb, Rb, pr, Rr) in enumerate(leg_visual_poses(base_W, top_W, LEG_BODY_LENGTH, LEG_ROD_LENGTH)):
        legs += _cylinder_model(f'leg{i + 1}_body', pb, Rb, LEG_BODY_RADIUS, LEG_BODY_LENGTH, (0.55, 0.57, 0.6))
        legs += _cylinder_model(f'leg{i + 1}_rod', pr, Rr, LEG_ROD_RADIUS, LEG_ROD_LENGTH, (0.85, 0.85, 0.88))

    markers_dir = os.path.join(out_dir, 'markers')
    assets = marker_assets(int(mk['id']), config['markers']['dictionary'], float(mk['size_m']), markers_dir)
    marker_uri = os.path.relpath(assets['obj'], out_dir)
    board = 0.08
    R_G = scene.R_W_G
    # Plaque support derrière le marqueur (côté +x_G), puis montant jusqu'au sol
    board_p = scene.marker_position_W + R_G @ np.array([0.003, 0, 0])
    post_h = scene.marker_position_W[2] - board / 2

    camera_rel, R_P_C = scene.camera_position_P, scene.R_P_C
    hfov = scene.horizontal_fov()

    sdf = f"""<?xml version="1.0"?>
<!-- Généré par scripts/generate_bench_sim.py depuis configurations/bench_rem.yaml : ne pas éditer. -->
<sdf version="1.9">
  <world name="{world}">
    <physics name="kinematic" type="ode"><max_step_size>0.004</max_step_size><real_time_factor>1.0</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
    <gravity>0 0 -9.81</gravity>
    <scene><ambient>0.55 0.55 0.55 1</ambient><background>0.75 0.8 0.85 1</background><grid>false</grid></scene>
    <light type="directional" name="sun"><cast_shadows>true</cast_shadows><pose>0 0 3 0 0 0</pose>
      <diffuse>0.9 0.9 0.9 1</diffuse><specular>0.2 0.2 0.2 1</specular><direction>-0.4 0.2 -0.9</direction></light>

    <model name="ground"><static>true</static><link name="link"><visual name="visual">
      <geometry><plane><normal>0 0 1</normal><size>4 4</size></plane></geometry>
      {_material((0.42, 0.43, 0.45))}</visual></link><pose>0 0 -0.012 0 0 0</pose></model>

    <model name="base"><static>true</static><pose>0 0 -0.006 0 0 0</pose>
      <link name="link"><visual name="visual">
        <geometry><cylinder><radius>{rb + 0.02:.4f}</radius><length>0.012</length></cylinder></geometry>
        {_material((0.25, 0.27, 0.3))}</visual></link></model>

    <model name="platform"><static>true</static><pose>{_pose(centre, R)}</pose>
      <link name="link">
        <visual name="plate">
          <pose>0 0 0.005 0 0 0</pose>
          <geometry><cylinder><radius>{rp + 0.015:.4f}</radius><length>0.01</length></cylinder></geometry>
          {_material((0.2, 0.45, 0.75))}</visual>
        <visual name="camera_body">
          <pose>{_pose(camera_rel - R_P_C @ np.array([0.012, 0, 0]), R_P_C)}</pose>
          <geometry><box><size>0.024 0.035 0.025</size></box></geometry>
          {_material((0.1, 0.1, 0.1))}</visual>
        <visual name="imu"><pose>0 0 0.0125 0 0 0</pose>
          <geometry><box><size>0.02 0.016 0.004</size></box></geometry>
          {_material((0.1, 0.5, 0.2))}</visual>
        <sensor name="camera" type="camera">
          <pose>{_pose(camera_rel, R_P_C)}</pose>
          <always_on>1</always_on><update_rate>{cam['fps']}</update_rate><visualize>false</visualize>
          <topic>/{world}/camera/image</topic>
          <camera>
            <horizontal_fov>{hfov:.6f}</horizontal_fov>
            <image><width>{cam['width']}</width><height>{cam['height']}</height><format>R8G8B8</format></image>
            <clip><near>{cam['near_clip']}</near><far>{cam['far_clip']}</far></clip>
            <lens><intrinsics><fx>{cam['fx']}</fx><fy>{cam['fy']}</fy><cx>{cam['cx'] + GZ_PIXEL_OFFSET:.4f}</cx><cy>{cam['cy'] + GZ_PIXEL_OFFSET:.4f}</cy><s>0</s></intrinsics></lens>
          </camera>
        </sensor>
      </link></model>
{legs}

    <model name="target_marker"><static>true</static><pose>{_pose(scene.marker_position_W, R_G)}</pose>
      <link name="link"><visual name="marker">
        <geometry><mesh><uri>{marker_uri}</uri></mesh></geometry></visual></link></model>
    <model name="target_board"><static>true</static><pose>{_pose(board_p, R_G)}</pose>
      <link name="link">
        <visual name="board"><geometry><box><size>0.004 {board} {board}</size></box></geometry>
          {_material((0.92, 0.92, 0.9))}</visual>
        <visual name="post"><pose>0.02 0 {-(board / 2 + post_h / 2):.4f} 0 0 0</pose>
          <geometry><box><size>0.03 0.03 {post_h:.4f}</size></box></geometry>
          {_material((0.5, 0.35, 0.2))}</visual></link></model>
  </world>
</sdf>
"""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f'{world}.sdf')
    with open(path, 'w') as f:
        f.write(sdf)
    return path


def body_poses(config: dict, geo: BenchGeometry, translation, R) -> Dict[str, tuple]:
    """Poses monde ``{nom de modèle: (position, R)}`` des corps mobiles pour une pose."""
    base_W, top_W = geo.legs_world(translation, R)
    poses = {'platform': (geo.platform_position_world(translation), R)}
    for i, (pb, Rb, pr, Rr) in enumerate(leg_visual_poses(base_W, top_W, LEG_BODY_LENGTH, LEG_ROD_LENGTH)):
        poses[f'leg{i + 1}_body'] = (pb, Rb)
        poses[f'leg{i + 1}_rod'] = (pr, Rr)
    return poses
