"""
Identification de la géométrie de la plateforme depuis le URDF (EXP-001)
=======================================================================

Le URDF décrit chaque jambe comme une chaîne U-P-R-U :
cardan de base (2 révolutes) → vérin (prismatique) → rotation propre (révolute
selon l'axe de la jambe) → cardan supérieur (2 révolutes). Le centre de chaque
cardan est l'intersection de ses deux axes. Ces centres sont les « vrais »
points d'attache B_i et P_i du modèle cinématique.

Fonctions:
    identify_urdf_geometry: points d'attache, pose neutre et centre de plateforme
"""

from typing import Dict, List

import numpy as np
import pybullet as p


def _joint_axis_world(body: int, joint: int, client: int):
    info = p.getJointInfo(body, joint, physicsClientId=client)
    state = p.getLinkState(body, joint, computeForwardKinematics=1, physicsClientId=client)
    rot = np.array(p.getMatrixFromQuaternion(state[5])).reshape(3, 3)
    axis = rot @ np.array(info[13])
    return np.array(state[4]), axis / np.linalg.norm(axis)


def _axes_intersection(o1, d1, o2, d2):
    """Milieu du plus court segment entre deux droites, et longueur de ce segment."""
    t = np.linalg.solve(np.array([d1, -d2, np.cross(d1, d2)]).T, o2 - o1)
    p1, p2 = o1 + t[0] * d1, o2 + t[1] * d2
    return (p1 + p2) / 2, float(np.linalg.norm(p1 - p2))


def _leg_joints(body: int, slider: int, client: int) -> Dict[str, int]:
    """Retrouve les articulations d'une jambe à partir de son vérin (parcours de l'arbre)."""
    joints = [p.getJointInfo(body, j, physicsClientId=client) for j in range(p.getNumJoints(body, physicsClientId=client))]
    parent_of = {j[0]: j[16] for j in joints}          # joint (= lien enfant) -> lien parent
    children_of: Dict[int, List[int]] = {}
    for j in joints:
        children_of.setdefault(j[16], []).append(j[0])

    def revolute_child(link):
        revs = [c for c in children_of.get(link, []) if joints[c][2] == p.JOINT_REVOLUTE]
        if len(revs) != 1:
            raise ValueError(f"chaîne de jambe inattendue sous le lien {link}")
        return revs[0]

    base2 = parent_of[slider]      # révolute dont l'enfant est le cylindre
    base1 = parent_of[base2]       # révolute dont l'enfant est le premier lien du cardan
    for j in (base1, base2):
        if joints[j][2] != p.JOINT_REVOLUTE:
            raise ValueError(f"cardan de base introuvable au-dessus du vérin {slider}")
    spin = revolute_child(slider)
    top1 = revolute_child(spin)
    top2 = revolute_child(top1)
    return dict(base1=base1, base2=base2, spin=spin, top1=top1, top2=top2)


def identify_urdf_geometry(urdf_path: str, actuator_indices: List[int], platform_link: int) -> Dict:
    """
    Identifie la géométrie cinématique réelle décrite par le URDF, en configuration zéro.

    Args:
        urdf_path: Chemin du URDF
        actuator_indices: Vérins des jambes 1 à 6 (ordre de sortie de l'IK)
        platform_link: Lien de la plateforme mobile (TOP1)

    Returns:
        dict avec :
            base_points (3x6), platform_points (3x6) : entrées de InverseKinematics.from_attachment_points
            home_position (3,) : centre plateforme dans le repère base, à la pose neutre
            base_centre_world, platform_centre_world (3,) : centres en coordonnées monde
            platform_centre_in_link (3,) : centre plateforme dans le repère du lien plateforme
            max_axis_gap (float) : plus grand écart entre axes d'un même cardan (m) ; 0 si cardans idéaux
            stroke (list[(min, max)]) : course des vérins (m)
    """
    client = p.connect(p.DIRECT)
    try:
        body = p.loadURDF(urdf_path, useFixedBase=1, physicsClientId=client)
        base_pts, top_pts, gaps, stroke = [], [], [], []
        for slider in actuator_indices:
            legs = _leg_joints(body, slider, client)
            b, gb = _axes_intersection(*_joint_axis_world(body, legs['base1'], client),
                                       *_joint_axis_world(body, legs['base2'], client))
            t, gt = _axes_intersection(*_joint_axis_world(body, legs['top1'], client),
                                       *_joint_axis_world(body, legs['top2'], client))
            base_pts.append(b); top_pts.append(t); gaps += [gb, gt]
            info = p.getJointInfo(body, slider, physicsClientId=client)
            stroke.append((info[8], info[9]))
        B, P = np.array(base_pts), np.array(top_pts)
        c_base, c_plat = B.mean(axis=0), P.mean(axis=0)

        state = p.getLinkState(body, platform_link, computeForwardKinematics=1, physicsClientId=client)
        rot = np.array(p.getMatrixFromQuaternion(state[5])).reshape(3, 3)
        centre_in_link = rot.T @ (c_plat - np.array(state[4]))
    finally:
        p.disconnect(client)

    return dict(base_points=(B - c_base).T, platform_points=(P - c_plat).T,
                home_position=c_plat - c_base, base_centre_world=c_base,
                platform_centre_world=c_plat, platform_centre_in_link=centre_in_link,
                max_axis_gap=max(gaps), stroke=stroke)
