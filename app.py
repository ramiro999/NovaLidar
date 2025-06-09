import plotly.express as px
import plotly.graph_objects as go
from typing import Union, Iterable
from gradio.themes.utils import colors, fonts, sizes
from gradio.themes.citrus import Citrus
import gradio as gr
from gradio_modal import Modal
from dataManagement.dataIMU import get_imu_data
from dataManagement.dataPointCloud import visualize_pointcloud_topic, get_pointcloud_topics, debug_bag_file
from dataManagement.dataGeo import get_gps_data
import pathlib
import pandas as pd
import numpy as np

theme = gr.themes.Citrus()
custom_css = """
<style>
    .gradio-tabs {
        display: flex;
        justify-content: center;
    }
    .geo-container {
        max-width: 100%;
        height: 600px;
    }
</style>
"""

# Bloque principal de la interfaz Gradio
with gr.Blocks(theme=theme, css=custom_css) as demo:
    # Estado global para compartir archivo entre tabs
    shared_file = gr.State()
    
    # Modal de bienvenida
    with Modal(visible=True) as modal:
        gr.HTML("""
        <div style="
            animation: slideUpFadeIn 0.6s ease-out;
            border-radius: 20px;
            text-align: left;
            font-family: 'Poppins', sans-serif;
        ">  
        
            <div style="text-align: center; display: flex; justify-content: center; align-items: center; gap: 10px;">
                <h1 style="margin: 0; font-size: 40px;">
                    Welcome to
                </h1>
            </div>
            <!-- Logo -->
            <div style="text-align: center; margin-top: 20px; justify-content: center; align-items: center; gap: 10px;">
                <img src="https://i.ibb.co/hFHdm5jq/Nova-Lidar-Logo-Citrus-Grish-Horizontal.png" alt="Near" style="width: 50%;">
            </div>
                
            <p style="font-size: 20px; margin-top: 15px;">
                This application allows you to analyze, visualize, and georeference LiDAR point clouds to enhance environmental perception for autonomous vehicles.
            </p>

            <ul style="font-size: 18px;">
                <li>🧱 Analyzes LiDAR point clouds to identify objects and surfaces in the environment.</li>
                <li>📊 Visualizes 3D data using interactive tools for improved spatial understanding.</li>
                <li>🌍 Georeferences point clouds to integrate them with maps and precise navigation systems.</li>
            </ul>

            
        </div>

        <style>
            @keyframes slideUpFadeIn {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
        </style>
        """)

    # Títulos y estilos personalizados con gr.HTML
    gr.HTML("""
        <style>
        .nova-title {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
        }
        @media (prefers-color-scheme: dark) {
            .nova-title {
            color: white;
            }
        }
        @media (prefers-color-scheme: light) {
            .nova-title {
            color: black;
            }
        }
        </style>
        <!-- Logo -->
        <div style="text-align: center; margin-top: 20px; justify-content: center; align-items: center; gap: 10px;">
            <img src="https://i.ibb.co/hFHdm5jq/Nova-Lidar-Logo-Citrus-Grish-Horizontal.png" alt="Near" style="width: 50%;">
        </div>
        """)

    # Primer tab: Point Cloud
    with gr.Tab("Point Cloud"):
        gr.Markdown("## Point Cloud", elem_id="point-cloud-title")
        gr.HTML("""
            <style>
            .nova-title {
                font-size: 2em;
                font-weight: bold;
                text-align: center;
            }
            @media (prefers-color-scheme: dark) {
                .nova-title {
                color: white;
                }
            }
            @media (prefers-color-scheme: light) {
                .nova-title {
                color: black;
                }
            }
            </style>
            <div>Representing point cloud data in plot</div>
            """)

        # Selector de dataset
        dataset_selection = gr.Radio(
            ["Own data", ".las", ".bag"], label="Select Dataset", value="Own data", elem_id="model-selector",
            visible=False
        )

        # Seleccionar archivo de nube de puntos
        file_input = gr.File(label="Upload Point Cloud File (.bag)", file_types=[".bag"])
        debug_button = gr.Button("Debug Bag File")
        update_topics_btn = gr.Button("Load Point Cloud Topics")
        debug_output = gr.Textbox(label="Debug Info", lines=10, interactive=False)
        selected_topic = gr.State()  # Estado oculto para almacenar el topic seleccionado

        visualize_button = gr.Button("Visualize Point Cloud")

        point_cloud_output = gr.Plot(label="Point Cloud Visualization")

        # Función para actualizar archivo compartido
        def update_shared_file(file):
            return file

        # Conexiones de eventos
        file_input.change(
            fn=update_shared_file,
            inputs=file_input,
            outputs=shared_file
        )
        
        debug_button.click(
            fn=debug_bag_file,
            inputs=file_input,
            outputs=debug_output
        )

        update_topics_btn.click(
            fn=get_pointcloud_topics, 
            inputs=file_input, 
            outputs=[selected_topic, debug_output]
        )

        visualize_button.click(
            fn=visualize_pointcloud_topic, 
            inputs=[file_input, selected_topic], 
            outputs=point_cloud_output
        )

    # Segundo tab: Data Analysis
    with gr.Tab("Data Analysis For IMU Sensor"):
        gr.Markdown("## Data Analysis For IMU Sensor", elem_id="data-analysis-title")
        gr.HTML("""
            <style>
            .nova-title {
                font-size: 2em;
                font-weight: bold;
                text-align: center;
            }
            @media (prefers-color-scheme: dark) {
                .nova-title {
                color: white;
                }
            }
            @media (prefers-color-scheme: light) {
                .nova-title {
                color: black;
                }
            }
            </style>
            <div>Data Analysis for IMU Sensor</div>
            """)
        
        imu_file_input = gr.File(label="Upload IMU Data File (.bag)", file_types=[".bag"], visible=False)
        imu_run_button = gr.Button("Analyze IMU Data", elem_id="imu-inference-button")

        # Salidas
        imu_table = gr.Dataframe(label="IMU Data", interactive=False)
        imu_plot = gr.Plot(label="IMU Sensor Analysis")

        # Función para mostrar los datos del IMU en tabla
        def show_imu_data(dataset_selection):
            tabla, imagen = get_imu_data()
            return tabla, imagen
            
        # Función para procesar y mostrar datos IMU
        def analyze_imu_data(bag_file):
            df, fig = get_imu_data(bag_file)
            return df, fig

        # Conexión del evento IMU
        imu_run_button.click(
            fn=analyze_imu_data,
            inputs=shared_file,  # Usar archivo compartido
            outputs=[imu_table, imu_plot]
        )

    # Tercer tab: Georeferencing (SIMPLIFICADO PARA COMPATIBILIDAD)
    with gr.Tab("Georeferencing"):
        gr.Markdown("## GPS Data Analysis & Georeferencing")
        gr.HTML("""
            <div>Analyze GPS data and create georeferenced polygons of the surveyed area</div>
            """)

        # Controles para GPS
        gr.Markdown("### GPS Configuration")
        
        # Selector de topic GPS personalizado
        gps_topic_input = gr.Textbox(
            label="GPS Topic Name (leave empty for auto-detection)", 
            placeholder="/gps/fix"
        )
        
        # Información del archivo actual
        file_info = gr.Textbox(
            label="Current File", 
            interactive=False,
            placeholder="No file selected"
        )
        
        # Botones de acción
        with gr.Row():
            gps_run_button = gr.Button("🗺️ Load GPS Data")
            clear_button = gr.Button("🗑️ Clear Data")
        
        # Estadísticas GPS
        gr.Markdown("### GPS Statistics")
        gps_stats = gr.JSON(label="GPS Data Summary")

        # Visualizaciones
        gr.Markdown("### GPS Data Table")
        geo_table = gr.Dataframe(
            label="GPS Coordinates", 
            interactive=False
        )
        
        # Mapa interactivo
        gr.Markdown("### Interactive Map")
        geo_viewer = gr.HTML(label="GPS Trajectory Map")

        # Función simplificada para analizar datos GPS
        def analyze_gps_data_enhanced(bag_file, topic_name=None):
            if bag_file is None:
                return (
                    pd.DataFrame(), 
                    "⚠️ No file provided. Please upload a .bag file first.",
                    {},
                    "No file selected"
                )
            
            try:
                # Obtener información del archivo
                file_name = bag_file.name if hasattr(bag_file, 'name') else str(bag_file)
                file_info_text = f"📁 {file_name.split('/')[-1]}"
                
                # Usar topic_name solo si no está vacío
                topic_to_use = topic_name if topic_name and topic_name.strip() else None
                
                # Procesar datos GPS
                df, map_path = get_gps_data(bag_file, topic_to_use)
                
                if df.empty:
                    return (
                        df, 
                        "❌ No GPS data found in the bag file. Try leaving the topic field empty for auto-detection.",
                        {},
                        file_info_text
                    )
                
                # Calcular estadísticas básicas
                stats = {
                    "Total Points": int(len(df)),
                    "Latitude Range": f"{df['Latitude'].min():.6f} to {df['Latitude'].max():.6f}",
                    "Longitude Range": f"{df['Longitude'].min():.6f} to {df['Longitude'].max():.6f}",
                    "Center Point": f"({df['Latitude'].mean():.6f}, {df['Longitude'].mean():.6f})"
                }
                
                # Agregar área aproximada si tenemos suficientes puntos
                if len(df) >= 3:
                    area = calculate_approximate_area(df)
                    stats["Approximate Area"] = f"{area:.2f} m²"
                
                # Leer contenido del mapa
                try:
                    with open(map_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                except Exception as e:
                    html_content = f"❌ Error loading map: {str(e)}"
                
                return df, html_content, stats, file_info_text
                
            except Exception as e:
                error_msg = f"❌ Error processing GPS data: {str(e)}"
                file_info_text = file_info_text if 'file_info_text' in locals() else "Error"
                return pd.DataFrame(), error_msg, {}, file_info_text

        # Función auxiliar para calcular área aproximada
        def calculate_approximate_area(df):
            if len(df) < 3:
                return 0
            
            # Aproximación simple usando bounding box
            lat_diff = df['Latitude'].max() - df['Latitude'].min()
            lon_diff = df['Longitude'].max() - df['Longitude'].min()
            
            # Conversión aproximada a metros (111km por grado)
            lat_meters = lat_diff * 111000
            lon_meters = lon_diff * 111000 * np.cos(np.radians(df['Latitude'].mean()))
            
            return lat_meters * lon_meters

        # Función para limpiar datos
        def clear_gps_data():
            return (
                pd.DataFrame(),
                "🔄 Data cleared. Upload a new file to begin analysis.",
                {},
                "No file selected"
            )

        # Función para actualizar info del archivo
        def update_file_info(file):
            if file is None:
                return "No file selected"
            file_name = file.name if hasattr(file, 'name') else str(file)
            return f"📁 {file_name.split('/')[-1]}"

        # Conexiones de eventos
        shared_file.change(
            fn=update_file_info,
            inputs=shared_file,
            outputs=file_info
        )
        
        gps_run_button.click(
            fn=analyze_gps_data_enhanced, 
            inputs=[shared_file, gps_topic_input], 
            outputs=[geo_table, geo_viewer, gps_stats, file_info]
        )
        
        clear_button.click(
            fn=clear_gps_data,
            outputs=[geo_table, geo_viewer, gps_stats, file_info]
        )

if __name__ == "__main__":
    demo.launch()