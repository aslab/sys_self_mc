import rclpy

from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.action import ActionServer, CancelResponse
from diagnostic_msgs.msg import DiagnosticArray
from diagnostic_msgs.msg import KeyValue

from sys_self_mc.onto_mc import SysSelf

class ROSSysSelf(Node, SysSelf):
    def __init__(self, node_name):
        super().__init__(node_name)
        SysSelf.__init__(self)

        # Initialize your ROS 2 node here

    def run(self):
        # Use the custom method from MyCustomClass
        self.custom_method()

        # Implement your ROS 2 node's functionality here

