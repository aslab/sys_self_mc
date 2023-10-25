# SysSelf
The SysSelf metamodel is designed to enable the robot to adapt to robustly deliver the expected value, even in the face of unexpected contingencies. It incorporates classes relevant to the SE domain extracted from [INCOSE](https://www.incose.org/), ISO/IEC/IEEE 15288:2023 Standard on Systems and software engineering, and [SEBoK](https://sebokwiki.org/wiki/Guide_to_the_Systems_Engineering_Body_of_Knowledge_(SEBoK)), including terms such as Value, Component, and Capability, as well as diagnostic concepts such as Component and Goal Status or Measure of Performance. Perhaps the most characteristic aspect is that it is expressed in terms of Category Theory (CT) to establish inferences at higher levels of abstraction, which can reveal new insights and facilitate decision-making. The meta-model is written in OWL for implementation.

## Metacontroller
The meta-controller consists of a Python class that uses the [Owlready2](https://owlready2.readthedocs.io/en/v0.42/) API to interact with the ontology and specific methods to apply the reasoning based on CT described above. The reasoning is directed towards extracting the required adaptation action, and inform the stakeholders about the changes in the expected values. This is application- and implementation-agnostic.

In the context of ROS, we have created a node wrapper that inherits from the meta-controller class. This node is responsible for publishing or executing necessary adaptations based on diagnostic messages. Additionally, there is an observer node that continuously monitors the application's components, goals, capabilities, values, and performance. It publishes a diagnostic message whenever any of these elements fails or exhibits performance below the expected standards.

## Use-Cases

We evaluate the applicability of the metacontroller in distinct situations that can occur during the mission of a miner robot, in particular, a simulated version of the ROBOMINER prototype, a highly configurable modular system capable of self-assembly and reconfiguration during operation. The scenario below handles a critical component that is experiencing a failure. Other scenarios such as an unsolvable error, mission unreachable or capability not meeting its expected performance have been evaluated and may be shared upon demand. 

### Reconfiguration for failure in critical sensor
In this scenario, there is an robotic module exploring the mine. During the mission execution, the observer detects that the main localization sensor, a LiDAR, is not publishing any topic. This problem can be associated with a malfunctioning sensor or just a disconnection. When the metacontroller receives that a component is no longer available, it stars looking for another component with similar characteristics. In this case, it found that the depth information of the camera can provide the same data if it is transformed from point cloud to laser scan so it commanded executes this adaption.

## ROS2 Foxy example:
* Create workspace and clone this repo RM2 and fault injection repos:
```
source /opt/ros/foxy/setup.bash
mkdir -p ~/rm2_ws/src
cd ~/rm2_ws/src
git clone git@github.com:robominers-eu/rm2_simulation.git
git@github.com:aslab/sys_self_mc.git
git@github.com:robominers-eu/fault_injection.git
cd ..
rosdep update
rosdep install -y -r -q --from-paths src --ignore-src --rosdistro foxy 
colcon build --symlink-install
source install/setup.bash
```

## Launch the simulation
* Execute the simulation:
```
 ros2 launch rm2_simulation rm2_sim.launch.py  
```

## Launch the observer and the metacontroller
* Observer node:
```
 ros2 run sys_self_mc  observer_node
```
* Metacontroller node using the adequate model for this application, i.e., params file:
```
 ros2 run sys_self_mc  sys_self_node --ros-args --params-file src/sys_self_mc/config/loc.yaml
```

## Inject failure on the lidar sensor
* Sensor readings to zero:
```
 ros2 run fault_injection  lidar_fault
```
## Result
The robot shall resume to the navigation task, the changes in ROS2 nodes and topics can be verifyed with rqt_graph
```
rqt_graph
```
