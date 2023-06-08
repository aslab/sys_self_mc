import rclpy
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus
from sensor_msgs.msg import LaserScan
# http://docs.ros.org/en/api/diagnostic_msgs/html/msg/DiagnosticStatus.html

class DiagnosticPublisher(Node):
    def __init__(self):
        super().__init__('diagnostic_publisher')
        self.publisher_ = self.create_publisher(DiagnosticArray, 'diagnostic', 10)
        # self.timer_ = self.create_timer(1.0, self.publish_diagnostic)
        self.subscription_ = self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)

    def publish_diagnostic_lidar(self):
        msg = DiagnosticArray()
        status = DiagnosticStatus()
        status.level = DiagnosticStatus.ERROR
        status.name = 'lidar'
        status.message = 'ComponentStatus'
        # # Add key-value pairs for additional information
        # status.values.append(KeyValue(key='Key', value='Value'))

        msg.status.append(status)
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing LIDAR diagnostic')

    def lidar_callback(self, msg):
        self.scan_count_ = sum(msg.ranges) # sum values
        if self.scan_count_ < 1.0:
            self.publish_diagnostic_lidar()

def main(args=None):
    rclpy.init(args=args)

    publisher_node = DiagnosticPublisher()

    rclpy.spin(publisher_node)


    publisher_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
