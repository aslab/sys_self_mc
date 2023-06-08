#!/usr/bin/env python3

import rclpy

from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionServer, CancelResponse
from diagnostic_msgs.msg import DiagnosticArray
from diagnostic_msgs.msg import KeyValue
from ament_index_python.packages import get_package_share_directory
import subprocess, os, signal, sys
from sys_self_mc.onto_mc import SysSelf
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus
import yaml
from yaml.loader import SafeLoader

class SysSelfROS(Node, SysSelf):
    def __init__(self):
        super().__init__("sys_self_node")
        path = os.path.join(get_package_share_directory('sys_self_mc'), 'ontologies')
        names = ["app_loc.owl","rm_domain.owl", "sys_self.owl"]
        SysSelf.__init__(self, path, names)
        self.load_OWL_file()
        self.get_logger().info("Initialization OK")
        self.subscription_ = self.create_subscription(DiagnosticArray, 'diagnostic', self.diagnostics_callback, 1)
        self.application_path = os.path.join(get_package_share_directory('rm2_simulation'))
  
    def diagnostics_callback(self, msg):
        ERROR = int(2).to_bytes(1, 'big') # convert bytes to diagnostic level status

        # if self.onto is not None:
        for diagnostic_status in msg.status:
            if diagnostic_status.message == "ComponentStatus":
                self.get_logger().info("New component status received")
                if diagnostic_status.level == ERROR:
                    status = "UNAVAILABLE"
                    source = diagnostic_status.name + "_status"
                    type = "has" + diagnostic_status.message +"Value"
                    if self.check_status(source) != status: # check if change already applied
                        result = self.receive_update(status, source, type)
                        if result:
                            self.get_logger().info("Component {} status updated to value {}".format(diagnostic_status.name, status))
                            adaption = self.get_adaption_mechanism(diagnostic_status.name)

                            self.request_configuration(adaption)

    def request_configuration(self, adaption):

        for adapt in adaption:
            file = os.path.join(self.application_path, 'config', (adapt.name + '.yaml')) # reconfigurations available specified in yaml file
            if os.path.isfile(file):
                    self.get_logger().info("New Configuration requested: {} of type ROS2 NODE".format(adaption))
                    self.reconfiguration_execution(adapt,file)
                
    def reconfiguration_execution(self, adapt, file):
        with open(file) as f:
            data = yaml.load(f, Loader=SafeLoader)
            node = adapt.name + "_node"
            remap_list = data[node]['ros__parameters']['remappings']
            remap = " --remap " + remap_list[0] + ":=" + remap_list[1] + " --remap " + remap_list[2] + ":=" + remap_list[3]
            
            command = ["ros2 run " + adapt.name + " " + node + " --ros-args" + remap + " --params-file " + file]
            print(command)
        try:
            subprocess.Popen(command, shell = True)
            self.get_logger().info("------------Reconfiguration successful------------")
        except OSError as e:
            self.get_logger().info(f"Error executing command: {e}")
            #     while process.poll() is None:  # Check if the process is still running
            #         pass  # Process is still running, continue the loop
            # except KeyboardInterrupt:
            #     os.killpg(os.getpgid(process.pid), signal.SIGTERM)


def main():

    # Start rosnode
    rclpy.init()

    ros_reasoner = SysSelfROS()

    
    # Spin until the process in terminated
    rclpy.spin(ros_reasoner)
    rclpy.shutdown()


if __name__ == '__main__':
    main()