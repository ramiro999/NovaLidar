# my_server.py
import asyncio
from foxglove_websocket.server import FoxgloveWebSocketServer
from datetime import datetime

async def main():
    async with FoxgloveWebSocketServer() as server:
        await server.start()
        channel_id = server.add_channel({
            "topic": "my_custom_topic",
            "encoding": "json",
            "schemaName": "my_msgs/CustomMsg",
            "schema": '{"type": "object", "properties": {"msg": {"type": "string"}}}',
        })

        while True:
            msg = {"msg": f"Hola desde ROS2 a las {datetime.now().isoformat()}"}
            await server.send_message(channel_id, msg)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
