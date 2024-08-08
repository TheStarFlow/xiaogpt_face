import asyncio
import json

import websockets

from xiaogpt.config import WAKEUP_KEYWORD


class XiaoAiWebSocketServer:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.server = None

    async def handler(self, websocket, path):
        # 新客户端连接
        self.clients.add(websocket)
        try:
            async for message in websocket:
                # 处理接收到的消息
                print(f"收到消息: {message}")
                # 这里可以添加其他消息处理逻辑
        finally:
            # 客户端断开连接
            self.clients.remove(websocket)

    async def start_server(self):
        self.server = await websockets.serve(self.handler, self.host, self.port)
        print(f"WebSocket 服务器启动在 ws://{self.host}:{self.port}")

    async def stop_server(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print("WebSocket 服务器已关闭")

    async def broadcast(self, message):
        if self.clients:  # 确保有连接的客户端
            await asyncio.gather(
                *[client.send(message) for client in self.clients]
            )

    async def process_message(self, message, need_ask, mute, tts_callback, stop_callback) -> bool:
        # is wake up word
        query = message.get("query", "").strip()
        if query.startwith(WAKEUP_KEYWORD):
            data = {
                "target": "face",
                "content": ""
            }
            await asyncio.create_task(self.broadcast(json.dumps(data)))
            return True
        if "连" in query and "WIFI" in query:
            if mute:
                await stop_callback
            data = {
                "target": "qrcode",
                "content": ""
            }
            await asyncio.create_task(self.broadcast(json.dumps(data)))
            await tts_callback("二维码已打开，快扫码连接吧")
            return True
        return False
        # if message.startswith("XIAOAI"):
        #     asyncio.create_task(self.broadcast("你好，我是服务器。"))

    async def run(self):
        await self.start_server()
        try:
            await asyncio.Future()  # 保持服务器运行
        finally:
            await self.stop_server()
