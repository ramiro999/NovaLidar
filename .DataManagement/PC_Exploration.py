from foxglove_data_platform.client import Client
from datetime import datetime
import numpy as np
import struct
import open3d as o3d
import gradio as gr
import plotly.graph_objects as go

# ======================
# 1. Cargar datos LIDAR
# ======================
client = Client(token="fox_sk_1dbfnSNxWmtT4cV82YCMA3lbQE3hcE3E")
device_id = "dev_cJEWbnootvtj8e4p"
coverage = [r for r in client.get_coverage(start=datetime(2018, 1, 1), end=datetime(2019, 1, 1)) if r["device_id"] == device_id]
lidar_messages = [
    message for topic, record, message in client.get_messages(
        device_id=device_id,
        start=coverage[0]["start"],
        end=coverage[0]["end"],
        topics=["/LIDAR_TOP"]
    )
]
message = lidar_messages[0]

# ======================
# 2. Decodificar mensaje
# ======================
def decode_pointcloud(msg):
    dtype_map = {
        1: ("b", 1), 2: ("B", 1), 3: ("h", 2), 4: ("H", 2),
        5: ("i", 4), 6: ("I", 4), 7: ("f", 4), 8: ("d", 8),
    }
    fields = [(f.name, f.offset, *dtype_map[f.type]) for f in msg.fields if f.name in ["x", "y", "z", "intensity"]]
    step = msg.point_stride
    raw = msg.data
    num = len(raw) // step

    xyz, intensity = [], []
    for i in range(num):
        base = i * step
        point = {}
        for name, offset, fmt, _ in fields:
            point[name] = struct.unpack_from(fmt, raw, base + offset)[0]
        xyz.append([point["x"], point["y"], point["z"]])
        intensity.append(point.get("intensity", 0.0))
    return np.array(xyz), np.array(intensity)

# Cargar y procesar una vez
points, intensities = decode_pointcloud(message)
global_z_min = points[:, 2].min()
global_z_max = points[:, 2].max()

# ============================
# 3. Convertir a Plotly Figure
# ============================
def pointcloud_to_plotly(points, color_values):
    fig = go.Figure(data=[go.Scatter3d(
        x=points[:, 0],
        y=points[:, 1],
        z=points[:, 2],
        mode='markers',
        marker=dict(
            size=1.5,
            color=color_values,
            colorscale='Plasma',
            opacity=0.8
        )
    )])
    fig.update_layout(
        scene=dict(
            xaxis_title='X', yaxis_title='Y', zaxis_title='Z',
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0)
    )
    return fig

# ======================
# 4. Interfaz de Gradio
# ======================
def visualize(color_mode, z_min, z_max):
    # Filtrar por altura
    mask = (points[:, 2] >= z_min) & (points[:, 2] <= z_max)
    filtered = points[mask]
    filtered_int = intensities[mask]

    if color_mode == "Altura (Z)":
        color = filtered[:, 2]
    elif color_mode == "Intensidad":
        color = filtered_int
    else:
        color = np.ones(len(filtered))  # color plano

    return pointcloud_to_plotly(filtered, color)

# Llama a interfaz
gr.Interface(
    fn=visualize,
    inputs=[
        gr.Radio(["Altura (Z)", "Intensidad"], label="Color por"),
        gr.Slider(global_z_min, global_z_max, value=global_z_min, step=0.1, label="Altura mínima Z"),
        gr.Slider(global_z_min, global_z_max, value=global_z_max, step=0.1, label="Altura máxima Z"),
    ],
    outputs=gr.Plot(label="Nube de puntos LIDAR"),
    title="Visualizador LIDAR desde Foxglove",
    description="Colorea la nube por altura o intensidad. Usa los sliders para filtrar el eje Z."
).launch(share=True)
