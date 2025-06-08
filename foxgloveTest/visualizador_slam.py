import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import os
import debugpy
from foxglove.client import Client
import time

# Configuración del debugger
# debugpy.listen(("0.0.0.0", 5679))
# print("Esperando debugger en el puerto 5679...")
# debugpy.wait_for_client()
# print("Debugger conectado, continuando ejecución...")

# Configuración desde variables de entorno
TOPICO_NUBE = os.getenv('TOPICO_NUBE', '/points')
SLAM_TOPIC = os.getenv('SLAM_TOPIC', '/slam_result')
FOXGLOVE_API_KEY = 'fox_sk_00qYHvytMXRmqJA0pEyX6XxYec8PEJPf'

# Cliente REST
client = Client(token=FOXGLOVE_API_KEY)
print(dir(client))

class VisualizadorSLAM(Node):
    def __init__(self):
        super().__init__('visualizador_slam_restapi')
        self.get_logger().info('Inicializando VisualizadorSLAM usando REST API...')

        # Suscripciones ROS
        self.subscription = self.create_subscription(
            PointCloud2,
            TOPICO_NUBE,
            self.callback_nube,
            10)
        self.slam_subscription = self.create_subscription(
            PointCloud2,
            SLAM_TOPIC,
            self.callback_slam,
            10)

        # Usar la API REST
        self.usar_api_rest()

    def usar_api_rest(self):
        try:
            # 1. Listar dispositivos
            devices = client.get_devices()
            for dev in devices:
                self.get_logger().info(f"Dispositivo: {dev['name']} (ID: {dev['id']})")

            recordings = client.get_recordings()
            self.get_logger().info(f"{len(recordings)} grabaciones encontradas.")

            #evento = client.create_event({
            #    "type": "info",
            #    "timestamp": int(time.time() * 1000),
            #    "message": "Grabación iniciada desde ROS2"
            #})
            #self.get_logger().info(f"Evento creado con ID: {evento['id']}")
    
        except Exception as e:
            self.get_logger().error(f"Error usando la REST API de Foxglove: {e}")

    def callback_nube(self, msg):
        self.get_logger().info('Mensaje recibido en callback_nube')

    def callback_slam(self, msg):
        self.get_logger().info('Mensaje recibido en callback_slam')

def main(args=None):
    rclpy.init(args=args)
    visualizador = VisualizadorSLAM()
    try:
        rclpy.spin(visualizador)
    except KeyboardInterrupt:
        pass
    finally:
        visualizador.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
