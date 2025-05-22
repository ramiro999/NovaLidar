import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
import foxglove_websocket as fgws
import asyncio
import threading
import os
import pdb  # Debugging tool
import debugpy

# Configuración del debugger
debugpy.listen(("0.0.0.0", 5679))
print("Esperando debugger en el puerto 5678...")
debugpy.wait_for_client()  # Opcional: el script se detiene hasta conectar el debugger
print("Debugger conectado, continuando ejecución...")

# Configuración
TOPICO_NUBE = os.getenv('TOPICO_NUBE', '/points')
FOXGLOVE_URL = os.getenv('FOXGLOVE_URL', 'ws://localhost:8765')
SLAM_TOPIC = os.getenv('SLAM_TOPIC', '/slam_result')
FOXGLOVE_API_KEY = os.getenv('FOXGLOVE_API_KEY', 'fox_sk_00qYHvytMXRmqJA0pEyX6XxYec8PEJPf')

class VisualizadorSLAM(Node):
    def __init__(self):
        super().__init__('visualizador_slam')
        self.get_logger().info('Inicializando VisualizadorSLAM...')

        # Suscripciones ROS
        self.subscription = self.create_subscription(
            PointCloud2,
            TOPICO_NUBE,
            self.callback_nube,
            10)
        self.get_logger().info(f'Suscripción a {TOPICO_NUBE} creada')

        self.slam_subscription = self.create_subscription(
            PointCloud2,
            SLAM_TOPIC,
            self.callback_slam,
            10)
        self.get_logger().info(f'Suscripción a {SLAM_TOPIC} creada')

        # Crear loop asyncio nuevo y correrlo en hilo aparte
        self.loop = asyncio.new_event_loop()
        self.fg_client = None
        t = threading.Thread(target=self._start_asyncio_loop, daemon=True)
        t.start()

        # Lanzar tarea de conexión a Foxglove
        asyncio.run_coroutine_threadsafe(self.iniciar_foxglove(), self.loop)

    def _start_asyncio_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    async def iniciar_foxglove(self):
        self.get_logger().info(f'Conectando a Foxglove en {FOXGLOVE_URL}...')
        self.fg_client = fgws.FoxgloveClient()
        try:
            await self.fg_client.connect(FOXGLOVE_URL, headers={"Authorization": f"Bearer {FOXGLOVE_API_KEY}"})
            self.get_logger().info('Conexión a Foxglove establecida y autenticada.')

            await self.fg_client.advertise(
                [
                    {"topic": "nube_puntos", "encoding": "cdr", "schemaName": "sensor_msgs/PointCloud2"},
                    {"topic": "slam", "encoding": "cdr", "schemaName": "sensor_msgs/PointCloud2"}
                ]
            )
            self.get_logger().info('Tópicos anunciados en Foxglove.')
        except Exception as e:
            self.get_logger().error(f'Error al conectar o autenticar con Foxglove: {e}')

    def callback_nube(self, msg):
        self.get_logger().info('Mensaje recibido en callback_nube.')
        if self.fg_client and self.fg_client.is_connected:
            self.get_logger().info('Enviando mensaje a Foxglove (nube_puntos).')
            asyncio.run_coroutine_threadsafe(
                self.fg_client.send_message("nube_puntos", msg), self.loop)
        else:
            self.get_logger().warn('Cliente Foxglove no conectado o autenticado en callback_nube.')

    def callback_slam(self, msg):
        self.get_logger().info('Mensaje recibido en callback_slam.')
        if self.fg_client and self.fg_client.is_connected:
            self.get_logger().info('Enviando mensaje a Foxglove (slam).')
            asyncio.run_coroutine_threadsafe(
                self.fg_client.send_message("slam", msg), self.loop)
        else:
            self.get_logger().warn('Cliente Foxglove no conectado o autenticado en callback_slam.')

def main(args=None):
    print('Iniciando main() de visualizador_slam.py')
    rclpy.init(args=args)
    visualizador = VisualizadorSLAM()
    print('VisualizadorSLAM instanciado')
    try:
        print('Entrando en rclpy.spin()')
        rclpy.spin(visualizador)
    except KeyboardInterrupt:
        print('KeyboardInterrupt detectado, saliendo...')
    finally:
        print('Destruyendo nodo y cerrando rclpy')
        visualizador.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
