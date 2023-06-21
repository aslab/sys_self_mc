import os
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument
                            
def generate_launch_description():

    config = os.path.join(
      get_package_share_directory('sys_self_mc'),
      'config',
      'loc.yaml'
      )

    return LaunchDescription([
        Node(
            package='sys_self_mc',
            executable='sys_self_node',
            name='sys_self_node',
            output='screen',
            parameters=[config],)
          ],)
          


    
