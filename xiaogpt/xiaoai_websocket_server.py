import asyncio
import json
import time

import websockets
import socket
import logging

from xiaogpt.config import WAKEUP_KEYWORD


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


class XiaoAiWebSocketServer:
    def __init__(self, host=get_host_ip(), port=8888):
        self.host = host
        self.port = port
        self.clients = set()
        self.server = None
        self.log = logging.getLogger("xiaogpt")

    async def handler(self, websocket, path):
        # 新客户端连接
        self.clients.add(websocket)
        try:
            async for message in websocket:
                # 处理接收到的消息
                self.log.debug(f"收到消息: {message}")
                # 这里可以添加其他消息处理逻辑
                try:
                    message = json.loads(message)
                    if message["target"] == "ping":
                        echo = dict()
                        echo["target"] = "echo"
                        echo["content"] = time.time() * 1000
                        await self.broadcast(json.dumps(echo), True)
                except Exception as e:
                    print("error message " + str(e))
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

    async def broadcast(self, message, is_ping=False):
        if not is_ping:
            print("broadcast message :" + message)
        if self.clients:  # 确保有连接的客户端
            await asyncio.gather(
                *[client.send(message) for client in self.clients]
            )

    async def process_message(self, message, need_ask, mute, tts_callback, stop_callback) -> bool:
        # is wake up word
        query = message.get("query", "").strip()
        print("curr process message :" + query)
        if query.startswith(WAKEUP_KEYWORD):
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
