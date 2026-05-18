from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, ExecuteProcess
from launch.substitutions import (
    LaunchConfiguration, EnvironmentVariable,
    PathJoinSubstitution, Command, FindExecutable
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():


    world_arg = DeclareLaunchArgument('world', default_value='empty.sdf',
        description='World file name (relative to worlds/ directory)')
    world_path = PathJoinSubstitution([
        FindPackageShare('semubot_gazebo'), 'worlds', LaunchConfiguration('world')
    ])

    x_pos_arg = DeclareLaunchArgument('x', default_value='0', description='Spawn X position')
    y_pos_arg = DeclareLaunchArgument('y', default_value='0', description='Spawn Y position')
    z_pos_arg = DeclareLaunchArgument('z', default_value='0', description='Spawn Z position')

    xacro_file = PathJoinSubstitution([
        FindPackageShare('semubot_description'), 'urdf', 'semubot.urdf.xacro'
    ])

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]), ' ', xacro_file, ' sim:=true'
    ])

    robot_description = ParameterValue(robot_description_content, value_type=str)

    gazebo_model_path = SetEnvironmentVariable(
        name='GZ_SIM_MODEL_PATH',
        value=[
            EnvironmentVariable('GZ_SIM_MODEL_PATH', default_value=''),
            ':', PathJoinSubstitution([FindPackageShare('semubot_description'), 'meshes']),
            ':', FindPackageShare('semubot_gazebo'),
        ]
    )

    gazebo_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[
            EnvironmentVariable('GZ_SIM_RESOURCE_PATH', default_value=''),
            ':', PathJoinSubstitution([FindPackageShare('semubot_description'), '..']),
            ':', FindPackageShare('semubot_gazebo'),
            ':', PathJoinSubstitution([FindPackageShare('realsense2_description'), '..']),
        ]
    )

    gazebo_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-v', '4', '-r', world_path],
        output='screen'
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
    )

    spawn_urdf_node = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_urdf',
        output='screen',
        arguments=[
            '-name', 'semubot',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-string', robot_description_content,
        ]
    )

    odom_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='odom_bridge',
        output='screen',
        arguments=['/model/semubot/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry'],
        remappings=[('/model/semubot/odometry', '/odom')]
    )

    joint_state_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='joint_state_bridge',
        output='screen',
        arguments=[
            '/world/default/model/semubot/joint_state@sensor_msgs/msg/JointState@gz.msgs.Model'
        ],
        remappings=[('/world/default/model/semubot/joint_state', '/joint_states')]
    )

    cmd_vel_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='cmd_vel_bridge',
        output='screen',
        arguments=['/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist']
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        output='screen',
        arguments=['/world/default/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock'],
        remappings=[('/world/default/clock', '/clock')]
    )

    tf_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='tf_bridge',
        output='screen',
        arguments=['/model/semubot/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'],
        remappings=[('/model/semubot/tf', '/tf')]
    )

    camera_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='camera_bridge',
        output='screen',
        arguments=[
            '/camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth_image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
        ],
        remappings=[
            ('/camera/image', '/camera/color/image_raw'),
            ('/camera/depth_image', '/camera/aligned_depth_to_color/image_raw'),
            ('/camera/points', '/camera/depth/color/points'),
            ('/camera/camera_info', '/camera/color/camera_info'),
        ]
    )

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_node',
        output='screen',
        parameters=[
            os.path.join(get_package_share_directory('semubot_gazebo'), 'config', 'ekf.yaml'),
            {'use_sim_time': True},
        ],
    )

    return LaunchDescription([
        world_arg,
        x_pos_arg,
        y_pos_arg,
        z_pos_arg,
        gazebo_model_path,
        gazebo_resource_path,
        gazebo_sim,
        robot_state_publisher_node,
        spawn_urdf_node,
        tf_bridge,
        odom_bridge,
        joint_state_bridge,
        cmd_vel_bridge,
        clock_bridge,
        camera_bridge,
        ekf_node,
    ])
