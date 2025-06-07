#realizar un script que lea los mensajes del sensor IMU para su respectivo topico desde un archivo .bag
import os
import gradio as gr
import pandas as pd

#Procesamiento del archivo .bag para extraer datos del IMU y generar un CSV e imagen
# Si el CSV y la imagen ya existen, no volver a procesar
def procesar_imu_bag():
    """
    Procesa el archivo .bag y genera el CSV y la imagen solo si no existen.
    """
    import bagpy
    from bagpy import bagreader
    import pandas as pd
    import matplotlib.pyplot as plt

    # Si ya existe el CSV y la imagen, no reprocesar
    if os.path.exists('output_imu/imu_data.csv') and os.path.exists('output_imu/imu_data.png'):
        return

    # Leer el archivo .bag
    bag = bagreader('../config/lidar_hesai/park_dataset.bag')
    print(bag.topic_table)
    imu_topic = '/imu/data'
    imu_data = bag.message_by_topic(imu_topic)
    print(f"Datos extraídos en: {imu_data}")
    imu_df = pd.read_csv(imu_data)
    print(imu_df.head())
    print(imu_df[{
        'linear_acceleration.x', 'linear_acceleration.y', 'linear_acceleration.z',
        'angular_velocity.x', 'angular_velocity.y', 'angular_velocity.z'}])
    if not os.path.exists('output_imu'):
        os.makedirs('output_imu')
    imu_df.to_csv('output_imu/imu_data.csv', index=False)
    plt.figure(figsize=(10,6))
    plt.subplot(2,1,1)
    plt.plot(imu_df['Time'], imu_df['linear_acceleration.x'], label='Acc X')
    plt.plot(imu_df['Time'], imu_df['linear_acceleration.y'], label='Acc Y')
    plt.plot(imu_df['Time'], imu_df['linear_acceleration.z'], label='Acc Z')
    plt.ylabel('Aceleración (m/s^2)')
    plt.legend()
    plt.title('Aceleraciones IMU')
    plt.subplot(2,1,2)
    plt.plot(imu_df['Time'], imu_df['angular_velocity.x'], label='Gyro X')
    plt.plot(imu_df['Time'], imu_df['angular_velocity.y'], label='Gyro Y')
    plt.plot(imu_df['Time'], imu_df['angular_velocity.z'], label='Gyro Z')
    plt.xlabel('Tiempo (s)')
    plt.ylabel('Velocidad Angular (rad/s)')
    plt.legend()
    plt.title('Velocidades Angulares IMU')
    plt.tight_layout()
    plt.savefig('output_imu/imu_data.png')
    plt.close()

#Recupera los datos para mostratlos en la interfaz de Gradio
def get_imu_data():
    """
    Devuelve un DataFrame con las columnas relevantes del IMU y la ruta de la imagen de la gráfica.
    Procesa el bag solo si el CSV no existe.
    """
 
    if not os.path.exists('output_imu/imu_data.csv') or not os.path.exists('output_imu/imu_data.png'):
        procesar_imu_bag()
    df = pd.read_csv('output_imu/imu_data.csv')
    columnas = [
        'Time',
        'linear_acceleration.x', 'linear_acceleration.y', 'linear_acceleration.z',
        'angular_velocity.x', 'angular_velocity.y', 'angular_velocity.z'
    ]
    tabla = df[columnas]
    return tabla, 'output_imu/imu_data.png'

with gr.Blocks() as demo:
    gr.Markdown("# Visualización de datos IMU desde .bag")
    btn = gr.Button("Mostrar datos IMU")
    tabla = gr.Dataframe(label="Datos IMU", interactive=False)
    imagen = gr.Image(label="Gráfica IMU")
    btn.click(get_imu_data, outputs=[tabla, imagen])

if __name__ == "__main__":
    demo.launch()
