"""
Jumeau Gazebo du démonstrateur REM
==================================

    ros2 launch rem_bench_sim bench_sim.launch.py mode:=acquisition gui:=false

``mode`` :
- ``acquisition`` : caméra, IMU, fusion ; aucun vérin commandé (comme acquisition_launch.py) ;
- ``manual`` : + ``manual_stewart_node`` (consignes ``/manual_position`` en cm, ``/manual_orientation`` en °) ;
- ``auto`` : + ``stewart_node`` (commande automatique du banc, inchangée).

Au lancement, dans ``runtime_dir`` (par défaut ``~/.rem_bench_sim``) :
- ``stewart_params_sim.yaml`` : configuration du banc adaptée (voir src/rem_bench/sim_config.py),
  transmise aux nœuds du banc par ``STEWART_CONFIG`` ;
- ``motor_runtime_state.json`` « home confirmé » (``STEWART_RUNTIME_DIR``) : l'état du banc
  réel (~/.stewart_control) n'est jamais touché ;
- ``world/rem_bench.sdf`` : monde Gazebo généré depuis bench_rem.yaml.

Les deux espaces de travail doivent être sourcés (stewart_control et rem_bench_sim).
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, RegisterEventHandler,
                            SetEnvironmentVariable)
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _setup(context):
    from rem_bench_sim import ensure_stewart_platform_on_path
    root = ensure_stewart_platform_on_path()
    from src.rem_bench import load_bench_config
    from src.rem_bench.sdf import generate_world
    from src.rem_bench.sim_config import make_sim_params, write_clean_runtime_state

    mode = LaunchConfiguration('mode').perform(context)
    gui = LaunchConfiguration('gui').perform(context).lower() in ('1', 'true', 'yes')
    runtime_dir = os.path.expanduser(LaunchConfiguration('runtime_dir').perform(context))
    bench_cfg_path = LaunchConfiguration('bench_config').perform(context) or None
    bench_cfg = load_bench_config(bench_cfg_path)
    world_name = bench_cfg['gazebo']['world_name']

    params_src = LaunchConfiguration('bench_params').perform(context) or os.path.join(
        get_package_share_directory('stewart_control'), 'config', 'stewart_params.yaml')
    with open(params_src, encoding='utf-8') as f:
        bench_params = yaml.safe_load(f)
    serial_link = os.path.join(runtime_dir, 'ttyVIRT')
    os.makedirs(runtime_dir, exist_ok=True)
    sim_params_path = os.path.join(runtime_dir, 'stewart_params_sim.yaml')
    with open(sim_params_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(make_sim_params(bench_params, bench_cfg, serial_link), f, sort_keys=False)
    write_clean_runtime_state(runtime_dir)
    world_path = generate_world(bench_cfg, os.path.join(runtime_dir, 'world'))

    env = [
        SetEnvironmentVariable('STEWART_CONFIG', sim_params_path),
        SetEnvironmentVariable('STEWART_RUNTIME_DIR', runtime_dir),
        SetEnvironmentVariable('STEWART_PLATFORM_ROOT', root),
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.path.dirname(world_path)),
    ]
    gz_args = ['gz', 'sim', '-r', world_path] if gui else ['gz', 'sim', '-r', '-s', '--headless-rendering', world_path]
    actions = env + [
        ExecuteProcess(cmd=gz_args, output='screen', name='gazebo'),
        Node(package='ros_gz_bridge', executable='parameter_bridge', name='camera_bridge', output='screen',
             arguments=[f'/{world_name}/camera/image@sensor_msgs/msg/Image[gz.msgs.Image']),
        Node(package='rem_bench_sim', executable='virtual_hardware', name='virtual_hardware', output='screen',
             parameters=[{'bench_config': bench_cfg_path or '', 'serial_link': serial_link}]),
        Node(package='rem_bench_sim', executable='sim_imu', name='imu_node', output='screen'),
        Node(package='rem_bench_sim', executable='sim_aruco', name='aruco_node', output='screen',
             parameters=[{'image_topic': f'/{world_name}/camera/image'}]),
        Node(package='stewart_control', executable='fusion_node', name='fusion_node', output='screen'),
    ]
    motion = {
        'manual': Node(package='stewart_control', executable='manual_stewart_node', output='screen'),
        'auto': Node(package='stewart_control', executable='stewart_node', name='stewart_node', output='screen'),
    }
    if mode in motion:
        # Le nœud ouvre le port série dès son démarrage : attendre que l'Arduino virtuel
        # ait créé le pseudo-terminal (comme on attend que l'Arduino soit branché).
        wait = ExecuteProcess(cmd=['bash', '-c', f'for i in $(seq 100); do [ -e "{serial_link}" ] && exit 0; '
                                                 'sleep 0.1; done; echo "port virtuel absent"; exit 1'],
                              name='wait_serial', output='screen')
        actions += [wait, RegisterEventHandler(OnProcessExit(target_action=wait, on_exit=[motion[mode]]))]
    elif mode != 'acquisition':
        raise ValueError(f"mode inconnu : {mode} (acquisition, manual, auto)")
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='acquisition', description='acquisition, manual ou auto'),
        DeclareLaunchArgument('gui', default_value='false', description='interface graphique Gazebo'),
        DeclareLaunchArgument('runtime_dir', default_value='~/.rem_bench_sim'),
        DeclareLaunchArgument('bench_config', default_value='', description='bench_rem.yaml (défaut : dépôt)'),
        DeclareLaunchArgument('bench_params', default_value='',
                              description='stewart_params.yaml du banc (défaut : share de stewart_control)'),
        OpaqueFunction(function=_setup),
    ])
