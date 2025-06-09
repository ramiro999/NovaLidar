import os
import pandas as pd
import numpy as np
import bagpy
from bagpy import bagreader
import tempfile
from typing import Optional, Tuple
import folium
import logging

# Configurar logging básico
logging.basicConfig(level=logging.WARNING)  # Reducir logging para velocidad
logger = logging.getLogger(__name__)

def get_gps_data(bag_file=None, topic_name=None):
    """
    Extrae y procesa datos GPS de un archivo .bag - VERSIÓN OPTIMIZADA
    """
    if bag_file is None:
        return pd.DataFrame(), "No file provided."

    try:
        bag_path = bag_file.name if hasattr(bag_file, 'name') else bag_file
        b = bagreader(bag_path)

        # Buscar topic GPS
        if topic_name:
            topic_table = b.topic_table
            if topic_name not in topic_table['Topics'].values:
                return pd.DataFrame(), f"Topic '{topic_name}' not found."
            gps_topic = topic_name
        else:
            gps_topic = find_gps_topic_fast(b.topic_table)
            if not gps_topic:
                return pd.DataFrame(), "No GPS topic found."
        
        # Extraer mensajes GPS
        gps_csv = b.message_by_topic(gps_topic)
        gps_df = pd.read_csv(gps_csv)
        
        return process_gps_dataframe_fast(gps_df)

    except Exception as e:
        return pd.DataFrame(), f"Error: {str(e)}"

def find_gps_topic_fast(topic_table) -> Optional[str]:
    """
    Búsqueda rápida de topic GPS
    """
    # Patrones más específicos y ordenados por probabilidad
    priority_patterns = ['NavSatFix', 'gps/fix', 'gnss']
    
    for pattern in priority_patterns:
        for _, row in topic_table.iterrows():
            if pattern in str(row['Types']) or pattern in str(row['Topics']):
                return row['Topics']
    
    # Búsqueda secundaria más general
    for _, row in topic_table.iterrows():
        topic_lower = str(row['Topics']).lower()
        type_lower = str(row['Types']).lower()
        if any(keyword in topic_lower or keyword in type_lower 
               for keyword in ['gps', 'fix', 'nav']):
            return row['Topics']
    
    return None

def process_gps_dataframe_fast(gps_df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    """
    Procesamiento rápido del DataFrame GPS
    """
    try:
        # Normalizar nombres de columnas - solo las más comunes
        if 'latitude' in gps_df.columns:
            gps_df.rename(columns={'latitude': 'Latitude'}, inplace=True)
        if 'longitude' in gps_df.columns:
            gps_df.rename(columns={'longitude': 'Longitude'}, inplace=True)
        if 'altitude' in gps_df.columns:
            gps_df.rename(columns={'altitude': 'Altitude'}, inplace=True)
        
        # Verificar columnas requeridas
        if 'Latitude' not in gps_df.columns or 'Longitude' not in gps_df.columns:
            return pd.DataFrame(), "Missing GPS coordinates columns."
        
        # Filtrado rápido - solo validaciones esenciales
        mask = (
            (gps_df['Latitude'].between(-90, 90)) & 
            (gps_df['Longitude'].between(-180, 180)) &
            (gps_df['Latitude'] != 0) &
            (gps_df['Longitude'] != 0)
        )
        gps_df = gps_df[mask]

        if gps_df.empty:
            return pd.DataFrame(), "No valid GPS coordinates."

        # Submuestreo si hay demasiados puntos (para velocidad)
        if len(gps_df) > 1000:
            # Tomar cada n-ésimo punto para mantener la forma general
            step = len(gps_df) // 500  # Máximo 500 puntos
            gps_df = gps_df.iloc[::step].copy()
        
        # Eliminar duplicados consecutivos rápidamente
        gps_df = gps_df.drop_duplicates(subset=['Latitude', 'Longitude'], keep='first')
        
        # Crear mapa simple y rápido
        map_path = create_fast_map(gps_df)
        
        # Agregar solo información básica
        gps_df = add_basic_info(gps_df)
        
        return gps_df, map_path

    except Exception as e:
        return pd.DataFrame(), f"Error processing GPS data: {str(e)}"

def add_basic_info(gps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Agregar solo información básica para velocidad
    """
    df = gps_df.copy()
    df['Point_ID'] = range(1, len(df) + 1)
    
    # Solo reordenar columnas básicas
    basic_cols = ['Point_ID', 'Latitude', 'Longitude']
    if 'Altitude' in df.columns:
        basic_cols.append('Altitude')
    
    # Mantener otras columnas al final
    other_cols = [col for col in df.columns if col not in basic_cols]
    final_cols = basic_cols + other_cols
    
    return df[final_cols]

def create_fast_map(gps_df: pd.DataFrame) -> str:
    """
    Crear mapa básico y rápido
    """
    try:
        # Calcular centro
        center_lat = gps_df['Latitude'].mean()
        center_lon = gps_df['Longitude'].mean()
        
        # Crear mapa simple
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=16,
            tiles='OpenStreetMap'
        )
        
        # Coordenadas para polígono - usar menos puntos si es necesario
        coords = list(zip(gps_df['Latitude'], gps_df['Longitude']))
        
        # Si hay muchos puntos, simplificar el polígono
        if len(coords) > 100:
            # Tomar cada n-ésimo punto para el polígono
            step = max(1, len(coords) // 50)
            coords = coords[::step]
        
        # Polígono simple
        folium.Polygon(
            locations=coords,
            color='purple',
            fill=True,
            fill_color='purple',
            fill_opacity=0.3,
            weight=2,
            popup=f'Área recorrida - {len(gps_df)} puntos GPS'
        ).add_to(m)
        
        # Línea de trayectoria
        folium.PolyLine(
            locations=coords,
            color='red',
            weight=2,
            opacity=0.8
        ).add_to(m)
        
        # Solo marcadores de inicio y fin si hay suficientes puntos
        if len(coords) > 1:
            folium.Marker(
                coords[0],
                popup='Inicio',
                icon=folium.Icon(color='green', icon='play')
            ).add_to(m)
            
            folium.Marker(
                coords[-1],
                popup='Final',
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(m)
        
        # Guardar mapa
        map_path = os.path.join(tempfile.gettempdir(), "fast_gps_map.html")
        m.save(map_path)
        
        return map_path
        
    except Exception as e:
        logger.error(f"Error creating map: {str(e)}")
        return create_minimal_map(gps_df)

def create_minimal_map(gps_df: pd.DataFrame) -> str:
    """
    Mapa mínimo como último recurso
    """
    try:
        center_lat = gps_df['Latitude'].mean()
        center_lon = gps_df['Longitude'].mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
        
        # Solo algunos puntos para el polígono
        coords = list(zip(gps_df['Latitude'], gps_df['Longitude']))
        if len(coords) > 20:
            coords = coords[::len(coords)//10]  # Máximo 10 puntos
        
        folium.Polygon(
            locations=coords,
            color='blue',
            fill=True,
            fill_opacity=0.2,
            popup='Área GPS'
        ).add_to(m)
        
        map_path = os.path.join(tempfile.gettempdir(), "minimal_gps_map.html")
        m.save(map_path)
        return map_path
        
    except:
        # Crear archivo HTML vacío como último recurso
        map_path = os.path.join(tempfile.gettempdir(), "empty_map.html")
        with open(map_path, 'w') as f:
            f.write("<html><body><h3>Error creating map</h3></body></html>")
        return map_path

def calculate_approximate_area_fast(gps_df: pd.DataFrame) -> float:
    """
    Cálculo rápido de área aproximada
    """
    if len(gps_df) < 3:
        return 0.0
    
    try:
        lat_range = gps_df['Latitude'].max() - gps_df['Latitude'].min()
        lon_range = gps_df['Longitude'].max() - gps_df['Longitude'].min()
        
        # Conversión simple a metros
        lat_meters = lat_range * 111000
        lon_meters = lon_range * 111000 * np.cos(np.radians(gps_df['Latitude'].mean()))
        
        return abs(lat_meters * lon_meters)
    except:
        return 0.0