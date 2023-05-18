import os
from glob import glob
from setuptools import setup

package_name = 'sys_self_mc'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, "ontologies"), glob('ontologies/*.owl')),
        (os.path.join('share', package_name), glob('launch/*.launch.py'))
    ],
    install_requires=['setuptools',
                        'owlready2>=0.24'],
    zip_safe=True,
    maintainer='Esther Aguado Gonzalez',
    maintainer_email='e.aguado@upm.es',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ros_mc = sys_self_mc.ros_mc:main',
        ],
    },
)
