import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, Conversation

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer to handle the real-time chat.
    Handles connections, message sending/receiving,
    """
    
    async def connect(self):
        """
        Is called when the websocket initiates the connection.
        - Verifies user auth
        - Joins the chat room 
        - Accepts the connection
        """
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """
        Is called when the websocket closes for any reason.
        - Removes the user from the chat
        """
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Is called when we get a text frame from the client.
        - Saves the message to the db
        - Broadcasts the message to all users in the chat room
        """
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Save message to database
        saved_message = await self.save_message(message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_username': self.user.username,
                'timestamp': saved_message.timestamp.isoformat(),
                'message_id': saved_message.id
            }
        )

    async def chat_message(self, event):
        """
        Is called when a message is received from the room.
        - Pass the message to the websocket
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))

    @database_sync_to_async
    def save_message(self, message):
        """
        Save the message to the database.
        - Creates a new Message obj
        - Associates message obj with the current conversation and sender
        """
        conversation = Conversation.objects.get(id=self.conversation_id)
        return Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=message
        )

class UnreadCountConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer to handle unread message count notifications.
    Broadcasts unread message notification to all connected clients.
    """
    
    async def connect(self):
        """
        Is called when the websocket is handshaking.
        - Accepts the connection
        """
        await self.accept()

    async def disconnect(self, close_code):
        """
        Is called when the websocket closes for any reason.
        """
        pass

    async def receive(self, text_data):
        """
        Is called when we get a text frame from the client.
        """
        pass

    async def unread_count_update(self, event):
        """
        Is called when an unread count update is received.
        - Sends the updated unread count to the websocket
        """
        await self.send(text_data=json.dumps({
            'type': 'unread_count_update',
            'conversation_id': event['conversation_id'],
            'count': event['count']
        })) 