import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class RoomConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        if self.room_id not in {"20", "30"}:
            await self.close(code=4001)
            return
        self.group_name = f"room_{self.room_id}_lobby"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"event": "connected", "room_id": self.room_id})

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        if not text_data:
            return
        payload = json.loads(text_data)
        action = payload.get("action")
        if action == "ping":
            await self.send_json({"event": "pong"})

    async def game_event(self, event):
        await self.send_json(event["payload"])
