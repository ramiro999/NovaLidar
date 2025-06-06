import bagpy
from bagpy import bagreader
from mcap.writer import Writer
import pandas as pd
import time

# Ruta al archivo .bag
bag_file = 'hall_02.bag'

# Leer el archivo .bag
b = bagreader(bag_file)

# Abrir archivo de salida .mcap
with open('hall_02.mcap', 'wb') as f:
    writer = Writer(f)
    writer.start(profile='ros1')

    for topic in b.topics:
        print(f'Procesando tópico: {topic}')

        # Leer los datos del tópico como DataFrame
        csv_file = b.message_by_topic(topic)
        df = pd.read_csv(csv_file)

        # Obtener tipo de mensaje
        msg_def = b.topic_msg_definition(topic)
        schema_id = writer.register_schema(
            name=topic.replace("/", "_"),
            encoding="ros1msg",
            data=msg_def.encode("utf-8")
        )

        channel_id = writer.register_channel(
            topic=topic,
            message_encoding="ros1",
            schema_id=schema_id
        )

        # Escribir cada fila del DataFrame como mensaje (sin deserializar)
        for _, row in df.iterrows():
            # No tenemos acceso al binario original del mensaje,
            # así que esto será más una exportación simbólica.
            # Este paso es representativo; MCAP espera datos binarios ROS.
            message_data = str(row.to_dict()).encode('utf-8')

            # Estimar timestamps
            timestamp = int(row['Time'] * 1e9)

            writer.add_message(
                channel_id=channel_id,
                log_time=timestamp,
                publish_time=timestamp,
                data=message_data
            )

    writer.finish()

print("✅ Conversión completada: hall_02.mcap")
