import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import bagpy
from bagpy import bagreader
import numpy as np
from scipy.spatial.transform import Rotation

def get_imu_data(bag_file=None):
    """
    Procesa el archivo .bag y devuelve:
    - DataFrame con los datos del IMU
    - Figura con 4 gráficas (aceleración, velocidad angular, orientación y magnitud)
    """
    if bag_file is None:
        # Modo demo si no se proporciona archivo
        return create_demo_data()
    
    try:
        # Procesar el archivo .bag
        bag_path = bag_file.name if hasattr(bag_file, 'name') else bag_file
        b = bagreader(bag_path)
        
        # Buscar el topic del IMU automáticamente
        imu_topic = find_imu_topic(b.topic_table)
        if not imu_topic:
            return None, create_empty_plot("No se encontró ningún topic de IMU en el archivo .bag")
        
        # Extraer datos del IMU
        imu_csv = b.message_by_topic(imu_topic)
        imu_df = pd.read_csv(imu_csv)
        
        # Procesar datos y crear visualizaciones
        return process_imu_dataframe(imu_df)
        
    except Exception as e:
        return None, create_empty_plot(f"Error procesando datos IMU: {str(e)}")

def find_imu_topic(topic_table):
    """
    Busca automáticamente el topic del IMU en la tabla de topics
    """
    for _, row in topic_table.iterrows():
        if 'sensor_msgs/Imu' in row['Types'] or 'Imu' in row['Types']:
            return row['Topics']
    return None

def process_imu_dataframe(imu_df):
    """
    Procesa el DataFrame del IMU y crea las visualizaciones
    """
    # Limpiar y preparar datos
    if 'Time' not in imu_df.columns and 'header.stamp.secs' in imu_df.columns:
        imu_df['Time'] = imu_df['header.stamp.secs'] + imu_df['header.stamp.nsecs'] * 1e-9
        imu_df['Time'] -= imu_df['Time'].min()
    
    # Renombrar columnas si es necesario
    column_mapping = {
        'linear_acceleration.x': 'acc_x',
        'linear_acceleration.y': 'acc_y', 
        'linear_acceleration.z': 'acc_z',
        'angular_velocity.x': 'gyro_x',
        'angular_velocity.y': 'gyro_y',
        'angular_velocity.z': 'gyro_z',
        'orientation.x': 'quat_x',
        'orientation.y': 'quat_y',
        'orientation.z': 'quat_z',
        'orientation.w': 'quat_w'
    }
    
    imu_df = imu_df.rename(columns={k:v for k,v in column_mapping.items() if k in imu_df.columns})
    
    # Calcular orientación en ángulos de Euler si hay datos de cuaterniones
    if all(col in imu_df.columns for col in ['quat_x', 'quat_y', 'quat_z', 'quat_w']):
        quats = imu_df[['quat_x', 'quat_y', 'quat_z', 'quat_w']].values
        rots = Rotation.from_quat(quats)
        euler = rots.as_euler('xyz', degrees=True)
        imu_df['roll'] = euler[:, 0]
        imu_df['pitch'] = euler[:, 1]
        imu_df['yaw'] = euler[:, 2]
    
    # Calcular magnitudes
    imu_df['acc_mag'] = np.sqrt(imu_df['acc_x']**2 + imu_df['acc_y']**2 + imu_df['acc_z']**2)
    imu_df['gyro_mag'] = np.sqrt(imu_df['gyro_x']**2 + imu_df['gyro_y']**2 + imu_df['gyro_z']**2)
    
    # Crear figura con subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Aceleración Lineal (m/s²)",
            "Velocidad Angular (rad/s)",
            "Orientación (grados)",
            "Magnitud Aceleración y Velocidad Angular"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # Gráfica de aceleración
    fig.add_trace(
        go.Scatter(x=imu_df['Time'], y=imu_df['acc_x'], name='Acc X', line=dict(color='red')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=imu_df['Time'], y=imu_df['acc_y'], name='Acc Y', line=dict(color='green')),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=imu_df['Time'], y=imu_df['acc_z'], name='Acc Z', line=dict(color='blue')),
        row=1, col=1
    )
    
    # Gráfica de velocidad angular
    fig.add_trace(
        go.Scatter(x=imu_df['Time'], y=imu_df['gyro_x'], name='Gyro X', line=dict(color='red')),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=imu_df['Time'], y=imu_df['gyro_y'], name='Gyro Y', line=dict(color='green')),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=imu_df['Time'], y=imu_df['gyro_z'], name='Gyro Z', line=dict(color='blue')),
        row=1, col=2
    )
    
    # Gráfica de orientación (si está disponible)
    if all(col in imu_df.columns for col in ['roll', 'pitch', 'yaw']):
        fig.add_trace(
            go.Scatter(x=imu_df['Time'], y=imu_df['roll'], name='Roll', line=dict(color='red')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=imu_df['Time'], y=imu_df['pitch'], name='Pitch', line=dict(color='green')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=imu_df['Time'], y=imu_df['yaw'], name='Yaw', line=dict(color='blue')),
            row=2, col=1
        )
    else:
        fig.add_annotation(
            text="Datos de orientación no disponibles",
            xref="x3", yref="y3",
            x=0.5, y=0.5, showarrow=False,
            row=2, col=1
        )
    
    # Gráfica de magnitudes
    fig.add_trace(
        go.Scatter(x=imu_df['Time'], y=imu_df['acc_mag'], name='Aceleración', line=dict(color='purple')),
        row=2, col=2
    )
    fig.add_trace(
        go.Scatter(x=imu_df['Time'], y=imu_df['gyro_mag'], name='Velocidad Angular', line=dict(color='orange')),
        row=2, col=2
    )
    
    # Actualizar diseño
    fig.update_layout(
        height=800,
        width=1000,
        title_text="Análisis de Datos IMU",
        showlegend=True,
        hovermode="x unified"
    )
    
    # Actualizar ejes
    fig.update_yaxes(title_text="m/s²", row=1, col=1)
    fig.update_yaxes(title_text="rad/s", row=1, col=2)
    fig.update_yaxes(title_text="grados", row=2, col=1)
    fig.update_yaxes(title_text="magnitud", row=2, col=2)
    fig.update_xaxes(title_text="Tiempo (s)", row=2, col=1)
    fig.update_xaxes(title_text="Tiempo (s)", row=2, col=2)
    
    return imu_df, fig

def create_empty_plot(message):
    """Crea un gráfico vacío con un mensaje de error"""
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

def create_demo_data():
    """Genera datos de demostración cuando no hay archivo .bag"""
    time = np.linspace(0, 10, 100)
    
    # Datos de ejemplo
    demo_df = pd.DataFrame({
        'Time': time,
        'acc_x': np.sin(time),
        'acc_y': np.cos(time),
        'acc_z': np.sin(time)*0.5,
        'gyro_x': np.cos(time*2),
        'gyro_y': np.sin(time*1.5),
        'gyro_z': np.cos(time*0.5),
        'quat_x': np.sin(time*0.1)*0.1,
        'quat_y': np.cos(time*0.1)*0.1,
        'quat_z': np.sin(time*0.05)*0.1,
        'quat_w': np.sqrt(1 - (np.sin(time*0.1)*0.1)**2 - (np.cos(time*0.1)*0.1)**2 - (np.sin(time*0.05)*0.1)**2)
    })
    
    return process_imu_dataframe(demo_df)