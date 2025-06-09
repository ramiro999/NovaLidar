import os
import pandas as pd
import numpy as np
import bagpy
from bagpy import bagreader
import tempfile
from typing import Optional, Tuple, List
import folium
from folium import plugins
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gps_data(bag_file=None, topic_name=None):
    """
    Extrae y procesa datos GPS de un archivo .bag
    
    Args:
        bag_file: Archivo .bag con datos GPS
        topic_name: Nombre del topic GPS (opcional)
        
    Returns:
        Tuple[pd.DataFrame, str]: DataFrame con datos GPS y ruta del mapa HTML
    """
    if bag_file is None:
        return pd.DataFrame(), "No file provided."

    try:
        bag_path = bag_file.name if hasattr(bag_file, 'name') else bag_file
        logger.info(f"Processing bag file: {bag_path}")
        
        b = bagreader(bag_path)

        # Buscar topic GPS
        if topic_name:
            topic_table = b.topic_table
            if topic_name not in topic_table['Topics'].values:
                logger.warning(f"Topic {topic_name} not found in bag file")
                return pd.DataFrame(), f"Topic '{topic_name}' not found in bag file."
            gps_topic = topic_name
        else:
            gps_topic = find_gps_topic(b.topic_table)
            if not gps_topic:
                logger.warning("No GPS topic found in bag file")
                return pd.DataFrame(), "No GPS topic found in bag file."

        logger.info(f"Using GPS topic: {gps_topic}")
        
        # Extraer mensajes GPS
        gps_csv = b.message_by_topic(gps_topic)
        gps_df = pd.read_csv(gps_csv)
        
        return process_gps_dataframe(gps_df)

    except Exception as e:
        logger.error(f"Error processing GPS data: {str(e)}")
        return pd.DataFrame(), f"Error: {str(e)}"

def find_gps_topic(topic_table) -> Optional[str]:
    """
    Encuentra automáticamente el topic GPS en la tabla de topics
    
    Args:
        topic_table: Tabla de topics del archivo bag
        
    Returns:
        Optional[str]: Nombre del topic GPS encontrado
    """
    gps_patterns = [
        'sensor_msgs/NavSatFix',
        'NavSatFix',
        'gps',
        'gnss',
        'fix'
    ]
    
    for _, row in topic_table.iterrows():
        topic_name = row['Topics'].lower()
        topic_type = str(row['Types']).lower()
        
        # Buscar patrones en el tipo de mensaje
        for pattern in gps_patterns:
            if pattern.lower() in topic_type or pattern.lower() in topic_name:
                logger.info(f"Found GPS topic: {row['Topics']} (Type: {row['Types']})")
                return row['Topics']
    
    return None

def process_gps_dataframe(gps_df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Procesa el DataFrame de datos GPS y crea visualización en mapa
    
    Args:
        gps_df: DataFrame con datos GPS en bruto
        
    Returns:
        Tuple[pd.DataFrame, str]: DataFrame procesado y ruta del mapa HTML
    """
    try:
        # Normalizar nombres de columnas
        column_mapping = {
            'latitude': 'Latitude',
            'longitude': 'Longitude', 
            'altitude': 'Altitude',
            'lat': 'Latitude',
            'lon': 'Longitude',
            'lng': 'Longitude',
            'alt': 'Altitude'
        }
        
        gps_df.rename(columns=column_mapping, inplace=True)
        
        # Verificar que tenemos las columnas necesarias
        required_cols = ['Latitude', 'Longitude']
        missing_cols = [col for col in required_cols if col not in gps_df.columns]
        
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return pd.DataFrame(), f"Missing required GPS columns: {missing_cols}"
        
        # Filtrar coordenadas válidas
        initial_count = len(gps_df)
        gps_df = gps_df[
            (gps_df['Latitude'].between(-90, 90)) & 
            (gps_df['Longitude'].between(-180, 180)) &
            (gps_df['Latitude'] != 0) &  # Eliminar coordenadas (0,0)
            (gps_df['Longitude'] != 0)
        ]
        
        # Eliminar duplicados
        gps_df = gps_df.drop_duplicates(subset=['Latitude', 'Longitude'])
        
        filtered_count = len(gps_df)
        logger.info(f"Filtered GPS data: {initial_count} -> {filtered_count} points")

        if gps_df.empty:
            return pd.DataFrame(), "No valid GPS coordinates found."

        # Crear mapa interactivo
        map_path = create_enhanced_map(gps_df)
        
        # Agregar columnas útiles
        gps_df = add_derived_columns(gps_df)
        
        return gps_df, map_path

    except Exception as e:
        logger.error(f"Error processing GPS dataframe: {str(e)}")
        return pd.DataFrame(), f"Error processing GPS data: {str(e)}"

def add_derived_columns(gps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columnas derivadas útiles al DataFrame GPS
    
    Args:
        gps_df: DataFrame con datos GPS básicos
        
    Returns:
        pd.DataFrame: DataFrame con columnas adicionales
    """
    df = gps_df.copy()
    
    # Agregar índice de punto
    df['Point_ID'] = range(1, len(df) + 1)
    
    # Calcular distancias entre puntos consecutivos
    if len(df) > 1:
        distances = []
        for i in range(len(df)):
            if i == 0:
                distances.append(0.0)
            else:
                dist = calculate_haversine_distance(
                    df.iloc[i-1]['Latitude'], df.iloc[i-1]['Longitude'],
                    df.iloc[i]['Latitude'], df.iloc[i]['Longitude']
                )
                distances.append(dist)
        df['Distance_m'] = distances
        df['Cumulative_Distance_m'] = df['Distance_m'].cumsum()
    
    # Reordenar columnas
    column_order = ['Point_ID', 'Latitude', 'Longitude']
    if 'Altitude' in df.columns:
        column_order.append('Altitude')
    if 'Distance_m' in df.columns:
        column_order.extend(['Distance_m', 'Cumulative_Distance_m'])
    
    # Agregar columnas restantes
    remaining_cols = [col for col in df.columns if col not in column_order]
    column_order.extend(remaining_cols)
    
    return df[column_order]

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia entre dos puntos GPS usando la fórmula de Haversine
    
    Args:
        lat1, lon1: Coordenadas del primer punto
        lat2, lon2: Coordenadas del segundo punto
        
    Returns:
        float: Distancia en metros
    """
    R = 6371000  # Radio de la Tierra en metros
    
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    delta_lat = np.radians(lat2 - lat1)
    delta_lon = np.radians(lon2 - lon1)
    
    a = (np.sin(delta_lat/2)**2 + 
         np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return R * c

def create_enhanced_map(gps_df: pd.DataFrame) -> str:
    """
    Crea un mapa interactivo mejorado con la trayectoria GPS
    
    Args:
        gps_df: DataFrame con datos GPS procesados
        
    Returns:
        str: Ruta del archivo HTML del mapa
    """
    try:
        # Calcular centro del mapa
        center_lat = gps_df['Latitude'].mean()
        center_lon = gps_df['Longitude'].mean()
        
        # Crear mapa base
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=17,
            tiles='OpenStreetMap'
        )
        
        # Agregar capas de mapa adicionales
        folium.TileLayer('Stamen Terrain').add_to(m)
        folium.TileLayer('CartoDB positron').add_to(m)
        
        # Preparar coordenadas para el polígono
        coords = list(zip(gps_df['Latitude'], gps_df['Longitude']))
        
        # Crear polígono del área recorrida
        folium.Polygon(
            locations=coords,
            color='purple',
            fill=True,
            fill_color='purple',
            fill_opacity=0.3,
            weight=3,
            popup=f'Área recorrida<br>Puntos: {len(coords)}<br>Área aprox: {calculate_polygon_area(coords):.1f} m²'
        ).add_to(m)
        
        # Agregar línea de trayectoria
        folium.PolyLine(
            locations=coords,
            color='red',
            weight=2,
            opacity=0.8,
            popup='Trayectoria GPS'
        ).add_to(m)
        
        # Agregar marcadores de inicio y fin
        if len(coords) > 0:
            # Punto de inicio
            folium.Marker(
                coords[0],
                popup='Inicio de trayectoria',
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)
            
            # Punto final
            if len(coords) > 1:
                folium.Marker(
                    coords[-1],
                    popup='Final de trayectoria', 
                    icon=folium.Icon(color='red', icon='stop')
                ).add_to(m)
        
        # Agregar mapa de calor de densidad de puntos
        heat_data = [[row['Latitude'], row['Longitude']] for _, row in gps_df.iterrows()]
        plugins.HeatMap(heat_data, radius=15, blur=10, max_zoom=1).add_to(m)
        
        # Agregar control de capas
        folium.LayerControl().add_to(m)
        
        # Agregar plugin de medición
        plugins.MeasureControl().add_to(m)
        
        # Guardar mapa
        map_path = os.path.join(tempfile.gettempdir(), "enhanced_gps_map.html")
        m.save(map_path)
        
        logger.info(f"Map saved to: {map_path}")
        return map_path
        
    except Exception as e:
        logger.error(f"Error creating map: {str(e)}")
        # Crear mapa básico como fallback
        return create_basic_map(gps_df)

def create_basic_map(gps_df: pd.DataFrame) -> str:
    """
    Crear mapa básico como fallback
    """
    center_lat = gps_df['Latitude'].mean()
    center_lon = gps_df['Longitude'].mean()
    coords = list(zip(gps_df['Latitude'], gps_df['Longitude']))
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=17)
    folium.Polygon(
        locations=coords,
        color='purple',
        fill=True,
        fill_color='purple',
        fill_opacity=0.4,
        weight=2,
        popup='Área recorrida'
    ).add_to(m)
    
    map_path = os.path.join(tempfile.gettempdir(), "basic_gps_map.html")
    m.save(map_path)
    return map_path

def calculate_polygon_area(coords: List[Tuple[float, float]]) -> float:
    """
    Calcula el área aproximada de un polígono usando coordenadas GPS
    
    Args:
        coords: Lista de tuplas (lat, lon)
        
    Returns:
        float: Área en metros cuadrados
    """
    if len(coords) < 3:
        return 0.0
    
    # Usar fórmula del área del polígono en coordenadas esféricas (aproximación)
    area = 0.0
    n = len(coords)
    
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][1] * coords[j][0]
        area -= coords[j][1] * coords[i][0]
    
    area = abs(area) / 2.0
    
    # Convertir de grados cuadrados a metros cuadrados (aproximación)
    # 1 grado ≈ 111 km en el ecuador
    area_m2 = area * (111000 ** 2)
    
    return area_m2