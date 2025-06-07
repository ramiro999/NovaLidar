from rosbags.rosbag1 import Reader
from rosbags.serde import deserialize_cdr
from sensor_msgs.msg import PointCloud2
import struct
import numpy as np

def decode_ros_pointcloud2(msg):
    # Formato del tipo de dato
    dtype_map = {
        1: ("b", 1), 2: ("B", 1), 3: ("h", 2), 4: ("H", 2),
        5: ("i", 4), 6: ("I", 4), 7: ("f", 4), 8: ("d", 8),
    }
    fields = [(f.name, f.offset, *dtype_map[f.datatype]) for f in msg.fields if f.name in ["x", "y", "z", "intensity"]]
    step = msg.point_step
    raw = msg.data
    n_points = len(raw) // step

    xyz, intensity = [], []
    for i in range(n_points):
        base = i * step
        point = {}
        for name, offset, fmt, _ in fields:
            point[name] = struct.unpack_from(fmt, raw, base + offset)[0]
        xyz.append([point["x"], point["y"], point["z"]])
        intensity.append(point.get("intensity", 0.0))
    return np.array(xyz), np.array(intensity)


