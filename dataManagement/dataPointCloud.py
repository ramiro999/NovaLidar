import bagpy
from bagpy import bagreader
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import List
import tempfile
import os
import struct

def get_pointcloud_topics(bag_file):
    """
    Extrae el primer topic de PointCloud2 encontrado y devuelve información de debug
    """
    if bag_file is None:
        return None, "No hay archivo seleccionado"
    
    try:
        bag_path = bag_file.name if hasattr(bag_file, 'name') else bag_file
        b = bagreader(bag_path)
        topic_table = b.topic_table
        
        debug_info = "=== INFORMACIÓN DEL ARCHIVO BAG ===\n"
        debug_info += f"Archivo: {bag_path}\n"
        debug_info += f"Total de topics: {len(topic_table)}\n\n"
        
        # Buscar el primer topic de PointCloud2
        selected_topic = None
        for _, row in topic_table.iterrows():
            topic_name = row['Topics']
            msg_type = row['Types']
            
            debug_info += f"Topic: {topic_name}\nTipo: {msg_type}\n\n"
            
            if 'PointCloud2' in msg_type or 'sensor_msgs/PointCloud2' in msg_type:
                if selected_topic is None:  # Tomar el primer topic de PointCloud2 encontrado
                    selected_topic = topic_name
                    debug_info += f"=== TOPIC SELECCIONADO PARA VISUALIZACIÓN ===\n{topic_name}\n"
        
        if selected_topic is None:
            return None, debug_info + "\n=== NO SE ENCONTRARON TOPICS DE POINTCLOUD2 ==="
        
        return selected_topic, debug_info
        
    except Exception as e:
        return None, f"Error al leer el archivo .bag: {str(e)}\nTipo de error: {type(e).__name__}"
        
    except Exception as e:
        print(f"Error al leer el archivo .bag: {str(e)}")
        return []

def visualize_pointcloud_topic(bag_file, selected_topic: str):
    """
    Visualiza el topic de PointCloud2 seleccionado automáticamente
    """
    if bag_file is None:
        return create_empty_plot("No se ha seleccionado archivo")
    
    if selected_topic is None:
        return create_empty_plot("No se encontraron topics de PointCloud2 en el archivo")
    
    try:
        bag_path = bag_file.name if hasattr(bag_file, 'name') else bag_file
        points_x, points_y, points_z = extract_pointcloud_with_rosbag(bag_path, selected_topic)
        
        if not points_x or len(points_x) == 0:
            return create_empty_plot(f"No se pudieron extraer puntos del topic {selected_topic}")
        
        # Submuestrear si hay demasiados puntos
        if len(points_x) > 1000000:
            indices = np.random.choice(len(points_x), 1000000, replace=False)
            points_x = [points_x[i] for i in indices]
            points_y = [points_y[i] for i in indices]
            points_z = [points_z[i] for i in indices]
        
        # Crear visualización 3D
        fig = go.Figure(data=[go.Scatter3d(
            x=points_x,
            y=points_y,
            z=points_z,
            mode='markers',
            marker=dict(
                size=1.5,
                color=points_z,
                colorscale='Viridis',
                opacity=0.6,
                colorbar=dict(title="Altura (Z)")
            ),
            name='Point Cloud'
        )])
        
        fig.update_layout(
            title=f'Nube de Puntos - {selected_topic}<br>Total puntos: {len(points_x)}',
            scene=dict(
                xaxis_title='X (metros)',
                yaxis_title='Y (metros)',
                zaxis_title='Z (metros)',
                aspectmode='data',
                camera=dict(eye=dict(x=1.2, y=1.2, z=1.2))
            ),
            width=900,
            height=700,
            showlegend=True
        )
        
        return fig
        
    except Exception as e:
        return create_empty_plot(f"Error al visualizar: {str(e)}")

def create_empty_plot(message: str):
    """Crea un gráfico vacío con un mensaje"""
    fig = go.Figure()
    fig.add_annotation(
        text=message, 
        xref="paper", yref="paper", 
        x=0.5, y=0.5, 
        showarrow=False,
        font=dict(size=16)
    )
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400
    )
    return fig


def debug_bag_file(bag_file):
    """
    Función para mostrar todos los topics del archivo .bag
    """
    if bag_file is None:
        return "No hay archivo seleccionado"
    
    try:
        # Usar directamente la ruta del archivo de Gradio
        bag_path = bag_file.name if hasattr(bag_file, 'name') else bag_file
        
        # Leer el archivo .bag con bagpy
        b = bagreader(bag_path)
        
        # Obtener la tabla de topics
        topic_table = b.topic_table
        
        # Crear el texto de salida
        result = f"=== INFORMACIÓN DEL ARCHIVO BAG ===\n"
        result += f"Archivo: {bag_path}\n"
        result += f"Total de topics: {len(topic_table)}\n\n"
        
        result += "=== LISTA DE TOPICS ===\n"
        for index, row in topic_table.iterrows():
            result += f"{index + 1}. Topic: {row['Topics']}\n"
            result += f"   Tipo: {row['Types']}\n"
            result += f"   Mensajes: {row['Message Count']}\n"
            result += f"   Frecuencia: {row['Frequency']}\n"
            result += "-" * 50 + "\n"
        
        # Identificar topics de PointCloud2
        pointcloud_topics = []
        for _, row in topic_table.iterrows():
            if 'PointCloud2' in row['Types']:
                pointcloud_topics.append(row['Topics'])
        
        if pointcloud_topics:
            result += f"\n=== TOPICS DE POINTCLOUD2 ENCONTRADOS ===\n"
            for i, topic in enumerate(pointcloud_topics):
                result += f"{i + 1}. {topic}\n"
        else:
            result += f"\n=== NO SE ENCONTRARON TOPICS DE POINTCLOUD2 ===\n"
        
        return result
        
    except Exception as e:
        return f"Error al leer el archivo .bag: {str(e)}\nTipo de error: {type(e).__name__}"

def extract_pointcloud_with_rosbag(bag_path: str, topic: str):
    """Extrae puntos de PointCloud2 usando rosbag de Python"""
    try:
        import rosbag
        
        points_x, points_y, points_z = [], [], []
        message_count = 0
        max_messages = 1  # Solo procesamos el primer mensaje para mayor velocidad
        
        # Manejar el archivo temporal de Gradio
        if hasattr(bag_path, 'name'):
            actual_path = bag_path.name
        else:
            actual_path = bag_path
            
        with rosbag.Bag(actual_path, 'r') as bag:
            for topic_name, msg, timestamp in bag.read_messages(topics=[topic]):
                if message_count >= max_messages:
                    break
                    
                if msg._type == 'sensor_msgs/PointCloud2':
                    x, y, z = extract_points_from_pointcloud2_msg(msg)
                    points_x.extend(x)
                    points_y.extend(y)
                    points_z.extend(z)
                    message_count += 1
        
        return points_x, points_y, points_z
        
    except ImportError:
        print("rosbag no disponible, usando método alternativo")
        return [], [], []
    except Exception as e:
        print(f"Error con rosbag: {str(e)}")
        return [], [], []

def extract_pointcloud_with_bagpy(bag_path: str, topic: str):
    """
    Método alternativo usando bagpy (puede ser limitado para PointCloud2)
    """
    try:
        print("Intentando extraer con bagpy...")
        b = bagreader(bag_path)
        
        # Intentar obtener datos del topic específico
        # Nota: bagpy puede no extraer bien los datos binarios de PointCloud2
        # pero intentamos de todas formas
        
        # Generar datos de ejemplo para demostración
        # En un caso real, necesitarías implementar la decodificación manual
        n_points = 5000
        points_x = np.random.normal(0, 10, n_points).tolist()
        points_y = np.random.normal(0, 10, n_points).tolist() 
        points_z = np.random.normal(0, 5, n_points).tolist()
        
        print(f"Generados {n_points} puntos de ejemplo")
        return points_x, points_y, points_z
        
    except Exception as e:
        print(f"Error con bagpy: {str(e)}")
        return [], [], []

def extract_points_from_pointcloud2_msg(msg):
    """
    Extrae puntos x, y, z de un mensaje PointCloud2 de ROS1
    """
    try:
        # Información del mensaje PointCloud2
        width = msg.width
        height = msg.height  
        point_step = msg.point_step
        data = msg.data
        
        print(f"PointCloud2 info: width={width}, height={height}, point_step={point_step}")
        
        # Buscar los campos x, y, z en los field descriptors
        x_offset = y_offset = z_offset = None
        for field in msg.fields:
            if field.name == 'x':
                x_offset = field.offset
            elif field.name == 'y':
                y_offset = field.offset
            elif field.name == 'z':
                z_offset = field.offset
        
        if x_offset is None or y_offset is None or z_offset is None:
            print("Campos x, y, z no encontrados en el mensaje")
            return [], [], []
        
        print(f"Offsets encontrados: x={x_offset}, y={y_offset}, z={z_offset}")
        
        # Extraer puntos
        points_x, points_y, points_z = [], [], []
        
        # Manejar diferentes tipos de datos
        if isinstance(data, str):
            data = data.encode('latin-1')
        elif hasattr(data, 'tobytes'):
            data = data.tobytes()
        
        total_points = len(data) // point_step
        print(f"Procesando {total_points} puntos...")
        
        # Procesar cada punto
        for i in range(0, len(data), point_step):
            if i + 12 <= len(data):  # Asegurar suficientes bytes para x,y,z (4 bytes cada uno)
                try:
                    # Leer valores float32 en little-endian
                    x = struct.unpack_from('<f', data, i + x_offset)[0]
                    y = struct.unpack_from('<f', data, i + y_offset)[0]
                    z = struct.unpack_from('<f', data, i + z_offset)[0]
                    
                    # Filtrar puntos inválidos
                    if not (np.isnan(x) or np.isnan(y) or np.isnan(z) or 
                           np.isinf(x) or np.isinf(y) or np.isinf(z)):
                        points_x.append(x)
                        points_y.append(y)
                        points_z.append(z)
                        
                except struct.error as e:
                    continue
        
        print(f"Puntos válidos extraídos: {len(points_x)}")
        return points_x, points_y, points_z
        
    except Exception as e:
        print(f"Error extrayendo puntos: {str(e)}")
        return [], [], []
    """
    Obtiene todos los topics del archivo bag
    """
    if bag_file is None:
        return []
    
    try:
        bag_path = bag_file.name if hasattr(bag_file, 'name') else bag_file
        b = bagreader(bag_path)
        topic_table = b.topic_table
        return topic_table['Topics'].tolist()
        
    except Exception as e:
        print(f"Error al obtener topics: {str(e)}")
        return []