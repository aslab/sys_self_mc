#!/usr/bin/env python3

import rclpy

from rclpy.node import Node
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

        self.declare_parameter('ontologies', rclpy.Parameter.Type.STRING_ARRAY) 
        self.declare_parameter('application', rclpy.Parameter.Type.STRING)    

        ontol = self.get_parameter('ontologies').value
        applic = self.get_parameter('application').value


        path = os.path.join(get_package_share_directory('sys_self_mc'), 'ontologies')
        # ontologies = ["app_attach.owl","rm_domain.owl", "sys_self.owl"]
        SysSelf.__init__(self, path, ontol)
        self.load_OWL_file()
        self.get_logger().info("Initialization OK")
        self.subscription_ = self.create_subscription(DiagnosticArray, 'diagnostic', self.diagnostics_callback, 1)
        self.application_path = os.path.join(get_package_share_directory(applic))
  
    def diagnostics_callback(self, msg):
        ERROR = int(2).to_bytes(1, 'big') # convert bytes to diagnostic level status
        WARN = int(1).to_bytes(1, 'big')

        for diagnostic_status in msg.status:
            if diagnostic_status.level == ERROR:
                self.get_logger().info("New ERROR status received")
                if diagnostic_status.message == "ComponentStatus":
                    status = "UNAVAILABLE"
                    source = diagnostic_status.name + "_status"
                    type = "has" + diagnostic_status.message +"Value"
                    if self.check_status(source) != status: # check if change already applied
                        result = self.receive_update(status, source, type)
                        if result:
                            self.get_logger().info("Component {} status updated to value {}".format(diagnostic_status.name, status))
                            adaption = self.find_adaption(diagnostic_status.name)
                            self.request_configuration(adaption)
            elif diagnostic_status.level == WARN:
                self.get_logger().info("New WARN status received, checking metrics")
                object_affected = self.check_metric(diagnostic_status.name, diagnostic_status.message)
                if object_affected is not None:
                    adaption = self.find_adaption(object_affected.name)
                    self.request_configuration(adaption)

    def request_configuration(self, adaption):
        # if adapt of type component -> NODE
        # if adapt of type goal -> ACTION
        for adapt in adaption: 
            file = os.path.join(self.application_path, 'config', (adapt.name + '.yaml')) # reconfigurations available specified in yaml file
            if os.path.isfile(file):
                    self.get_logger().info("New Configuration requested: {} of type ROS2 NODE".format(adaption))
                    self.reconfiguration_execution(adapt,file)
                    
            # else:
            #     self.get_logger().info("New Configuration requested: {} of type ROS2 ACTION".format(adaption))
                #TODO GET ADAPT FOR GOAL

            # ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{
            # pose: {
            #     header: {stamp: { sec: 0, nanosec: 0 },
            #     frame_id: 'map'
            #     },
            #     pose: {
            #         position: { x: 0.0, y: 0.0, z: 0.0 },
            #         orientation: { x: 0.0, y: 0.0, z: 0.0, w: 0.0 }
            #     }
            #     }
            #     }"

                
    def reconfiguration_execution(self, adapt, file):
        with open(file) as f:

            data = yaml.load(f, Loader=SafeLoader)
            node = adapt.name + "_node"

            if data[node] is not None:
                remap_list = data[node]['ros__parameters']['remappings']
                remap = " --remap " + remap_list[0] + ":=" + remap_list[1] + " --remap " + remap_list[2] + ":=" + remap_list[3]
                
                command = ["ros2 run " + adapt.name + " " + node + " --ros-args" + remap + " --params-file " + file]
            else:
                command = ["ros2 run " + adapt.name + " " + node + ".py"]


        try:
            subprocess.Popen(command, shell = True)
            self.get_logger().info("------------Reconfiguration successful------------")
        except OSError as e:
            self.get_logger().info(f"Error executing command: {e}")

def main():

    # Start rosnode
    rclpy.init()

    ros_reasoner = SysSelfROS()

    
    # Spin until the process in terminated
    rclpy.spin(ros_reasoner)
    rclpy.shutdown()


if __name__ == '__main__':
    main()