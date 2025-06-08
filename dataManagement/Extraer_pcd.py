import rosbag
import sensor_msgs.point_cloud2 as pc2
import open3d as o3d
import numpy as np

# Ruta del archivo bag
bag = rosbag.Bag("hall_02.bag")

# Nombre del topic con las nubes de puntos
topic = "/velodyne_points"

for i, (topic, msg, t) in enumerate(bag.read_messages(topics=[topic])):
    pc = pc2.read_points(msg, skip_nans=True, field_names=["x", "y", "z"])
    points = np.array(list(pc))

    if len(points) == 0:
        continue

    # Guarda
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    filename = f"frame_{i:03d}.pcd"
    o3d.io.write_point_cloud(filename, pcd)
    print(f"{filename} guardado.")
    
    if i >= 4:  # Solo los primeros 5 mensajes
        break
