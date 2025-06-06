from foxglove_data_platform.client import Client
from datetime import datetime 
import pandas as pd
import matplotlib.pyplot as plt
import folium
import webbrowser
import duckdb
import numpy as np
import pprint
import struct
import open3d as o3d

# Create a client instance
client = Client(token="fox_sk_1dbfnSNxWmtT4cV82YCMA3lbQE3hcE3E")

# List all devices
all_devices_coverage = client.get_coverage(start=datetime(2018, 1, 1), end=datetime(2019,1,1))
all_devices_coverage = sorted(all_devices_coverage, key=lambda c: c['start'])
pd.DataFrame(all_devices_coverage).head()

# Get coverage for a specific device
device_id = "dev_cJEWbnootvtj8e4p"
coverage = [r for r in all_devices_coverage if r["device_id"] == device_id]

# List all topics for a specific device
topics = client.get_topics(device_id=device_id, start=coverage[1]["start"], end=coverage[1]["end"])
print(pd.DataFrame(topics))

# Get data for a specific topic GPS /gps 
gps_messages =[
    (message.latitude, message.longitude)
    for topic, record, message in client.get_messages(
        device_id=device_id,
        start=coverage[1]["start"],
        end=coverage[1]["end"],
        topics=["/gps"],
    )
]

#print(pd.DataFrame(gps_messages, columns=["lat", "lon"]).head(10))
#pd.DataFrame(gps_messages, columns=["lat", "lon"]).plot(kind='scatter', x='lat', y='lon')
#plt.show()

# Create a map in folium
figure = folium.Figure(width=640, height=480)
map = folium.Map(location=gps_messages[0], zoom_start=200, width="100%")
folium.PolyLine(
    locations=gps_messages,
    weight=10,
    color="purple",
).add_to(map)
map.add_to(figure)
map.save("map.html")
webbrowser.open("map.html")

# Plotting IMU acceleration
imu_messages = [
    {
        "time": pd.Timestamp(record.log_time, unit="ns").isoformat(),
        "accel_x": message["linear_accel"]["x"],
        "accel_y": message["linear_accel"]["y"],
    }
    for topic, record, message in client.get_messages(
        device_id=device_id,
        start=coverage[0]["start"],
        end=coverage[-1]["end"],
        topics=["/imu"],
    )
]

pd.DataFrame(imu_messages).plot(x="time", figsize=(10, 6), rot=45)
plt.show()

# Classifying perceived object markers
"""
marker_messages = client.get_messages(
    device_id=device_id,
    start=coverage[1]["start"],
    end=coverage[1]["end"],
    topics=["/marker/annotations"],
)

flattened_markers = []
for topic, record, message in marker_messages:
    for entity in message.entities:
        for kv in entity.metadata:
            if kv.key == "category":
                flattened_markers.append((entity.id, kv.value))

annotations = pd.DataFrame(flattened_markers, columns=["annotation_id", "class_name"])

pysqldf = lambda q: sqldf(q, globals())
query = "SELECT class_name, COUNT(*) as count FROM annotations GROUP BY class_name ORDER BY count DESC"
res = duckdb.query(query).df()
res
print(res)

res.plot.bar(x="class_name", y="count", legend=False)
plt.xlabel("Class Name")
plt.ylabel("Count")
plt.title("Annotations Count by Class Name")
plt.show()
"""

lidar_messages = [
    message
    for topic, record, message in client.get_messages(
        device_id=device_id,
        start=coverage[0]["start"],
        end=coverage[0]["end"],
        topics=["/LIDAR_TOP"],
    )
]

message = lidar_messages[0]

# Recorre todos los atributos posibles (solo campos protobuf)
for field in message.DESCRIPTOR.fields:
    print(f"{field.name} ({field.type})")

field = lidar_messages[0].fields[0]

print("Attributes in field object:")
for attr in dir(field):
    if not attr.startswith("_"):
        print(f"{attr}: {getattr(field, attr)}") 

# Inspecciona el primer mensaje
print("Tipo de mensaje:", type(lidar_messages[0]))
pprint.pprint(vars(lidar_messages[0]))

def decode_pointcloud(message):
    dtype_map = {
        1: ("b", 1),  # INT8
        2: ("B", 1),  # UINT8
        3: ("h", 2),  # INT16
        4: ("H", 2),  # UINT16
        5: ("i", 4),  # INT32
        6: ("I", 4),  # UINT32
        7: ("f", 4),  # FLOAT32
        8: ("d", 8),  # FLOAT64
    }

    # Solo extraemos los campos x, y, z
    fields = [(f.name, f.offset, *dtype_map[f.type]) for f in message.fields if f.name in ["x", "y", "z"]]

    point_step = message.point_stride
    raw = message.data
    num_points = len(raw) // point_step

    # Extraer x, y, z de cada punto
    points = []
    for i in range(num_points):
        base = i * point_step
        point = []
        for _, offset, fmt, _ in fields:
            val = struct.unpack_from(fmt, raw, base + offset)[0]
            point.append(val)
        points.append(point)

    return np.array(points)
    
points = decode_pointcloud(lidar_messages[0])
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points)
o3d.visualization.draw_geometries([pcd])

