#!/usr/bin/env python3
"""
ROS2 Node — UDP Binary Receiver
Listens on a UDP socket and publishes incoming binary data to a ROS2 topic.

Topic published : /udp/raw   (std_msgs/msg/UInt8MultiArray)
Topic published : /udp/info  (std_msgs/msg/String)  ← sender address + byte count

Usage
-----
  ros2 run <your_package> udp_receiver_node
  ros2 run <your_package> udp_receiver_node --ros-args -p udp_port:=9000 -p udp_host:=0.0.0.0
"""
import os
import serial
import threading

import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import UInt8MultiArray, MultiArrayDimension, String
from ament_index_python.packages import get_package_share_directory
import yaml

pkg_path = get_package_share_directory('ESP32_ros2')
IPs_PATH = os.path.join(pkg_path,'conf/conf.yaml')



class SerialReceiverNode(Node):
    """ROS2 node that receives binary UDP datagrams and publishes them."""

    def __init__(self):
        super().__init__("ESP32_sreceiver_node")

        with open(IPs_PATH, "r") as f:
            conf_handlr= yaml.safe_load(f)
            baudr = conf_handlr["baudr"]
            timeout = conf_handlr["timeout"]
            parity = conf_handlr["parity"]
            bsize = conf_handlr["bsize"]
            stopbits = conf_handlr["stopbits"]
            port = conf_handlr["port"]
        
        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter("baudr", baudr)
        self.declare_parameter("timeout", timeout)
        self.declare_parameter("parity", parity)
        self.declare_parameter("bsize", bsize)
        self.declare_parameter("stopbits", stopbits)
        self.declare_parameter("raw_topic", "/ESP32/raw")
        self.declare_parameter("info_topic", "/ESP32/info")
        self.declare_parameter("port", port)

        baudr    = self.get_parameter("baudr").value
        bsize    = self.get_parameter("bsize").value
        parity_key   = self.get_parameter("parity").value
        if parity_key == "SPACE":
            parity=serial.PARITY_SPACE
        elif parity_key == "MARK":
            parity=serial.PARITY_MARK
        elif parity_key == "EVEN":
            parity=serial.PARITY_EVEN
        elif parity_key == "ODD":
            parity=serial.PARITY_ODD
        else:            
            parity=serial.PARITY_NONE
        stopbits =self.get_parameter("stopbits").value

        timeout = self.get_parameter("timeout").value
        raw_topic = self.get_parameter("raw_topic").value
        info_topic = self.get_parameter("info_topic").value

        # ── Publishers ────────────────────────────────────────────────────────
        self._raw_pub  = self.create_publisher(UInt8MultiArray, raw_topic,  10)
        self._info_pub = self.create_publisher(String,          info_topic, 10)

        # ── Serial Handler ────────────────────────────────────────────────────────
        
        self._ser = serial.Serial()
        self._ser.baudrate = baudr
        self._ser.bytesize = bsize
        self._ser.parity   = parity
        self._ser.baudrate = baudr
        self._ser.stopbits = stopbits
        self._ser.timeout = timeout
        self._ser.port = port
        self._ser.open()

        self.get_logger().info(
            f"SERIAL receiver listening  "
            f"→  publishing to '{raw_topic}' and '{info_topic}'"
        )

        # ── Background receive thread ─────────────────────────────────────────
        self._running = True
        self._thread  = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    # ── Core receive loop ─────────────────────────────────────────────────────

    def _recv_loop(self) -> None:
        """Blocking receive loop running in a daemon thread."""
        while self._running and rclpy.ok():
            data=None
            try:
                data = self._ser.read_until()
            except OSError:
                break

            if len(data):
                # print(data.rstrip(b"\r\n"))
                self._publish(data.rstrip(b"\r\n"))

    def _publish(self, data: bytes) -> None:
        """Build and publish ROS2 messages from a received datagram."""
        # -- UInt8MultiArray (raw bytes) --------------------------------------
        raw_msg                        = UInt8MultiArray()
        raw_msg.layout.data_offset     = 0
        dim                            = MultiArrayDimension()
        dim.label                      = "bytes"
        dim.size                       = len(data)
        dim.stride                     = len(data)
        raw_msg.layout.dim             = [dim]
        raw_msg.data                   = list(data)
        self._raw_pub.publish(raw_msg)

        # -- String info message ---------------------------------------------
        info_msg      = String()
        info_msg.data = (
            f"bytes={len(data)}  "
            f"hex={data.hex()}"
        )
        self._info_pub.publish(info_msg)

        self.get_logger().debug(info_msg.data)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def destroy_node(self) -> None:
        self.get_logger().info("Shutting down Serial receiver…")
        self._running = False
        self._thread.join(timeout=2.0)
        self._ser.close()
        super().destroy_node()


# ── Entry point ───────────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = SerialReceiverNode()

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()