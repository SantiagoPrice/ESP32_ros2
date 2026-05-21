from setuptools import find_packages, setup
import glob

package_name = 'ESP32_ros2'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (f"share/{package_name}/conf", glob.glob(f"{package_name}/conf/*")),
        (f"share/{package_name}/launch", glob.glob(f"{package_name}/launch/*")),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='orin64',
    maintainer_email='santiago@ai.iit.tsukuba.ac.jp',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ESP32_sreceiver_node = ESP32_ros2.ESP32_sreceiver_node:main',
            'ESP32_manager_node = ESP32_ros2.ESP32_manager_node:main'
        ],
    },
)
