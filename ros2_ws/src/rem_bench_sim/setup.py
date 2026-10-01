import os
from glob import glob

from setuptools import setup

package_name = 'rem_bench_sim'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jbernardo6u',
    maintainer_email='josebernardofisico@gmail.com',
    description='Jumeau Gazebo du démonstrateur REM',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'virtual_hardware = rem_bench_sim.virtual_hardware:main',
            'sim_imu = rem_bench_sim.sim_imu:main',
            'sim_aruco = rem_bench_sim.sim_aruco:main',
            'exp009_campaign = rem_bench_sim.exp009_campaign:main',
        ],
    },
)
