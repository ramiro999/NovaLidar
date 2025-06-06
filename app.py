import plotly.express as px
import plotly.graph_objects as go
from typing import Union, Iterable
from gradio.themes.utils import colors, fonts, sizes
from gradio.themes.citrus import Citrus
import gradio as gr
from gradio_modal import Modal


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
                <h1 style="margin: 0; font-size: 28px;">
                    Welcome to <span style='color: #F29D0C;'>Nova LiDAR</span>
                </h1>
            </div>

            <p style="font-size: 20px; margin-top: 15px;">
                This application allows you to analyze, visualize, and georeference LiDAR point clouds to enhance environmental perception for autonomous vehicles.
            </p>

            <ul style="font-size: 18px;">
                <li>🧱 Analyzes LiDAR point clouds to identify objects and surfaces in the environment.</li>
                <li>📊 Visualizes 3D data using interactive tools for improved spatial understanding.</li>
                <li>🌍 Georeferences point clouds to integrate them with maps and precise navigation systems.</li>
            </ul>

            <!-- GIF animado -->
            <div style="text-align: center; margin-top: 20px;">
                <img src="https://i.ibb.co/PGsmFhyZ/Nova-Lidar-Logo-Verde-removebg-preview.png" alt="Near" style="width: 50%;">
            </div>
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
        <div class="nova-title">Nova LiDAR</div>
        """)


    # Primer tab: Point Cloud
    with gr.Tab("Point Cloud"):
        gr.Markdown("## Point Cloud", elem_id="point-cloud-title")
        gr.HTML(""" ...CSS y explicación... """)

        dataset_selection = gr.Radio(
            ["Own data", ".pcd", ".bag"], label="Select Dataset", value="Own data", elem_id="model-selector"
        )

        # Reemplaza dos imágenes por un solo archivo
        file_input = gr.File(label="Upload Point Cloud File", file_types=[".pcd", ".bag", ".csv"])

        run_button = gr.Button("Run Inference", elem_id="inference-button")
        output_image = gr.Image(label="Disparity Map", visible=True, scale=1, elem_id="disparity-map", height="auto", width="100%")

        run_button.click(inputs=[file_input], outputs=output_image)

        generate_depth_button = gr.Button("Generate Depth Map", elem_id="depth-button", scale=1)
        depth_image = gr.Image(label="Depth Map", visible=True)

        generate_depth_button.click(
            inputs=[file_input, dataset_selection],
            outputs=depth_image
        )

    # Segundo tab: Data Analysis
    with gr.Tab("Data Analysis"):
        gr.Markdown("## Data Analysis", elem_id="data-analysis-title")
        gr.HTML(""" ...CSS y explicación... """)
        model_selector = gr.Radio(["RT-DETRv2", "YOLOv11"], label="Detection Model", value="RT-DETRv2", elem_id="model-selector")
        run_button = gr.Button("Run Detection", elem_id="inference-button")
        detect_output_image = gr.Plot(label="Object Detection", visible=True, scale=1)
        cards_placeholder = gr.HTML(label="Detected Objects Info", visible=True)
        run_button.click(inputs=[model_selector, dataset_selection], outputs=[detect_output_image, cards_placeholder])

    # Tercer tab: Georeferencing
    with gr.Tab("Georeferencing"):
        gr.Markdown("## Georeferencing section", elem_id="georeferencing-title")
        gr.HTML(""" ...CSS y explicación... """)
        # Aquí van los sliders, dropdowns y botones para parámetros del vehículo y objetos detectados
        # ...
        # El botón ejecuta cálculo y muestra gráficos

demo.launch(share=True)