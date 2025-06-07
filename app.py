import plotly.express as px
import plotly.graph_objects as go
from typing import Union, Iterable
from gradio.themes.utils import colors, fonts, sizes
from gradio.themes.citrus import Citrus
import gradio as gr
from gradio_modal import Modal
from dataManagement.dataIMU import get_imu_data


theme = gr.themes.Citrus()
custom_css = """
<style>
    .gradio-tabs {
        display: flex;
        justify-content: center;
    }
</style>
"""

# Bloque principal de la interfaz Gradio
with gr.Blocks(theme=theme, css=custom_css) as demo:
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
                <img src="https://i.ibb.co/WWSHnpDy/Nova-Lidar-Logo-Citrus-Gris.png" alt="Near" style="width: 50%;">
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
            <img src="https://i.ibb.co/WWSHnpDy/Nova-Lidar-Logo-Citrus-Gris.png" alt="Near" style="width: 50%;">
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
        # Procesar datos .las y .bag
        dataset_selection = gr.Radio(
            ["Own data", ".las", ".bag"], label="Select Dataset", value="Own data", elem_id="model-selector"
        )

        # Seleccionar archivo de nube de puntos
        file_input = gr.File(label="Upload Point Cloud File", file_types=[".las", ".bag",])

        run_button = gr.Button("Run Inference", elem_id="inference-button")
        point_cloud_output = gr.Plot(label="Point Cloud Visualization", visible=True, scale=1)

        run_button.click(inputs=[dataset_selection, file_input], outputs=point_cloud_output)
        
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
        
        # Panel grafico para mostrar datos del sensor IMU
        run_button = gr.Button("Run Detection", elem_id="inference-button")
        detect_output_image = gr.Plot(label="iMU SENSOR", visible=True, scale=1)
        #cards_placeholder = gr.HTML(label="mcap dataset lidar Info", visible=True)
        run_button.click(inputs=[dataset_selection], outputs=[detect_output_image])

        ########
        # Tabla y gráfico para mostrar datos del IMU
        run_button = gr.Button("Run Detection", elem_id="inference-button")
        imu_table = gr.Dataframe(label="IMU Data", interactive=False)
        imu_image = gr.Image(label="IMU Sensor Plot")
        
        # Función para mostrar los datos del IMU en tabla
        def show_imu_data(dataset_selection):
            tabla, imagen = get_imu_data()
            return tabla, imagen
        ########
    # Tercer tab: Georeferencing
    with gr.Tab("Georeferencing"):
        gr.Markdown("## Georeferencing section", elem_id="georeferencing-title")
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
            <div class="nova-title">Georeferencing</div>
            """)
        # El botón ejecuta cálculo y la interfaz de cesium ion 
        run_button = gr.Button("Run Georeferencing", elem_id="georeferencing-button")
        #cesium_output = gr.HTML(label="CesiumJS Viewer", visible=True, scale=1)

demo.launch()