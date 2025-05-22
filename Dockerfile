# Imagen base oficial de ROS2 Humble en Ubuntu 22.04
FROM ros:humble

# Instalar dependencias del sistema y herramientas útiles
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear espacio de trabajo
WORKDIR /ros2_ws

# Copiar el código fuente del proyecto al contenedor
COPY . /ros2_ws

# Instalar dependencias Python necesarias para el visualizador y debugpy
RUN pip3 install --no-cache-dir foxglove-websocket debugpy

# Configurar el entorno de ROS2
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

# Exponer puertos necesarios: Foxglove y Debugger
EXPOSE 8765
EXPOSE 5678

# Comando por defecto: iniciar bash para desarrollo interactivo
CMD ["bash"]
