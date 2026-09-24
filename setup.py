"""
Setup script pour Stewart Platform Control System
=================================================

Ce script permet d'installer le système de contrôle de plateforme Stewart
comme un package Python standard.

Usage:
    pip install -e .        # Installation en mode développement
    pip install .           # Installation standard
"""

from setuptools import setup, find_packages
import os


def read_requirements():
    """Lit le fichier requirements.txt"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    with open(requirements_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def read_readme():
    """Lit le fichier README.md"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Stewart Platform Control System"


setup(
    # Informations de base
    name="stewart-platform",
    version="1.0.0",
    description="Système de contrôle complet pour plateforme de Stewart",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    
    # Auteur et contact
    author="Stewart Platform Project",
    author_email="contact@stewart-platform.com",
    url="https://github.com/your-username/stewart-platform",
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    
    # Packages et structure
    packages=find_packages(),
    package_data={
        'stewart_platform': [
            'simulation/urdf/*',
            'simulation/meshes/*',
            'configurations/*',
        ],
    },
    include_package_data=True,
    
    # Dépendances
    python_requires=">=3.8",
    install_requires=read_requirements(),
    
    # Dépendances optionnelles
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.800',
        ],
        'docs': [
            'sphinx>=4.0',
            'sphinx-rtd-theme>=0.5',
            'sphinx-autodoc-typehints>=1.12',
        ],
        'hardware': [
            'pyserial>=3.5',
            'RPi.GPIO>=0.7.0;platform_machine=="armv7l"',  # Raspberry Pi uniquement
        ],
    },
    
    # Scripts en ligne de commande
    entry_points={
        'console_scripts': [
            'stewart-gui=scripts.launcher:main',
            'stewart-test=scripts.run_tests:main',
            'stewart-demo=examples.basic_control:main',
        ],
    },
    
    # Métadonnées supplémentaires
    keywords="stewart platform, robotics, simulation, pybullet, control system",
    project_urls={
        "Documentation": "https://stewart-platform.readthedocs.io/",
        "Source": "https://github.com/your-username/stewart-platform",
        "Tracker": "https://github.com/your-username/stewart-platform/issues",
    },
)
