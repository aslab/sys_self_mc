#!/usr/bin/env python3

import rclpy

from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionServer, CancelResponse
from diagnostic_msgs.msg import DiagnosticArray
from diagnostic_msgs.msg import KeyValue
from ament_index_python.packages import get_package_share_directory
import os
from sys_self_mc.onto_mc import SysSelf

class SysSelfROS(Node, SysSelf):
    def __init__(self):
        super().__init__("sys_self_node")

        path = os.path.join(get_package_share_directory('sys_self_mc'), 'ontologies')
        SysSelf.__init__(self, path, "rm_domain.owl")
        self.load_OWL_file()
        self.get_logger().info("Initialization OK")
        self.run()

    def run(self):
        a = self.onto.search(iri = "*Nav*")
        print(list(a))

def main():

    # Start rosnode
    rclpy.init()

    ros_reasoner = SysSelfROS()
    
    # Spin until the process in terminated
    rclpy.spin(ros_reasoner)
    rclpy.shutdown()


if __name__ == '__main__':
    main()