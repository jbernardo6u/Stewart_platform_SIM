"""
Chargement de la configuration
==============================

Source unique des paramètres géométriques, de simulation et d'interface :
``configurations/platform_config.yaml``.
"""

import os
from typing import Any, Dict, Optional

import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'configurations', 'platform_config.yaml')


def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Lit le fichier YAML de configuration (par défaut celui du dépôt)."""
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        return yaml.safe_load(f)


def project_path(relative: str) -> str:
    """Chemin absolu d'un fichier du dépôt (ex. l'URDF indiqué dans la configuration)."""
    return relative if os.path.isabs(relative) else os.path.join(PROJECT_ROOT, relative)
