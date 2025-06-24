# chat/consumers.py
import json
import base64
import binascii
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message, Group, GroupMessage
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        user1 = self.scope['user'].username 
        user2 = self.room_name
        self.room_group_name = f"chat_{''.join(sorted([user1, user2]))}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')
        attachment = text_data_json.get('attachment')
        sender = self.scope['user']
        receiver = await self.get_receiver_user()

        message_instance = await self.save_message(sender, receiver, message, attachment)

        send_data = {
            'type': 'chat_message',
            'sender': sender.username,
            'receiver': receiver.username,
            'message': message,
        }
        if message_instance.attachment:
            send_data['attachment'] = message_instance.attachment.url

        await self.channel_layer.group_send(
            self.room_group_name,
            send_data
        )
        

    async def chat_message(self, event):
        message = event.get('message')
        sender = event['sender']
        receiver = event['receiver']
        attachment = event.get('attachment')

        # Send message to WebSocket
        send_data = {
            'sender': sender,
            'receiver': receiver,
        }
        if message:
            send_data['message'] = message
        if attachment:
            send_data['attachment'] = attachment
            
        await self.send(text_data=json.dumps(send_data))

    @sync_to_async
    def save_message(self, sender, receiver, message, attachment=None):
        attachment_file = None
        if attachment:
            try:
                file_data = base64.b64decode(attachment['data'])
                attachment_file = ContentFile(file_data, name=attachment['name'])
            except (TypeError, ValueError, binascii.Error):
                attachment_file = None

        message_instance = Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=message,
            attachment=attachment_file
        )
        return message_instance

    @sync_to_async
    def get_receiver_user(self):
        return User.objects.get(username=self.room_name)



class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'chat_group_{self.group_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message')
        attachment = text_data_json.get('attachment')
        sender = self.scope['user']
        
        message_instance = await self.save_group_message(sender, self.group_id, message, attachment)

        
        send_data = {
            'type': 'group_chat_message',
            'message': message,
            'sender': sender.username,
        }
        if message_instance.attachment:
            send_data['attachment'] = message_instance.attachment.url
        
        await self.channel_layer.group_send(
            self.room_group_name,
            send_data
        )

    async def group_chat_message(self, event):
        message = event.get('message')
        sender = event['sender']
        attachment = event.get('attachment')

        # Send message to WebSocket
        send_data = {
            'sender': sender,
        }
        if message:
            send_data['message'] = message
        if attachment:
            send_data['attachment'] = attachment
            
        await self.send(text_data=json.dumps(send_data))

    @sync_to_async
    def save_group_message(self, sender, group_id, message, attachment=None):
        group = Group.objects.get(id=group_id)
        
        attachment_file = None
        if attachment:
            try:
                file_data = base64.b64decode(attachment['data'])
                attachment_file = ContentFile(file_data, name=attachment['name'])
            except (TypeError, ValueError, binascii.Error):
                attachment_file = None

        message_instance = GroupMessage.objects.create(
            group=group,
            sender=sender,
            content=message,
            attachment=attachment_file
        )
            
        return message_instance
