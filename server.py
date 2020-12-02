#!/usr/bin/env python

import asyncio
import websockets

bot = 'ChatBot'
you = 'You'
unnamed_user = 'New to the party'
message_line = lambda user, message: f'<{user}> {message}'
welcome_message = lambda new_user: f'<{new_user}> Just joined the party!'
goodbye_message = lambda old_user: f'<{old_user}> Justo left the party...'
error_private = lambda user: f'Impossible to send private message to {user}, user not found...' 

class User():
    def __init__(self, name, websocket, path):
        self.name = name
        self.ws = websocket
        self.online = True
    '''
    async def send_message(self,message):
        await self.ws.send(message_line(self.name,message))
    async def receive_message(self):
        return await self.ws.recv()
    '''

class Server():
    def __init__(self):
        self.registered_users = []
        self.forbidden_initials = ['?','/']

    async def start(self, websocket, path):
        await websocket.send(message_line(bot,'Welcome to de chat! Please tell your name...'))
        user = await self.login(websocket,path)
        await self.action_trigger(user)

    async def login(self, websocket, path):
        async for name in websocket:
            await websocket.send(message_line(unnamed_user,name))
            if self.verify_name(name) and name[0] not in self.forbidden_initials:
                new_user = User(name, websocket, path)
                self.registered_users.append(new_user)
                await websocket.send(message_line(bot,'Username accepted! Ready to go'))
                await self.notify_users(new_user)
                return new_user
            else:
                await websocket.send(message_line(bot,'This name is not available, try another...'))
                
    async def logout(self, user):
        user.online = False
        await user.ws.send(message_line(bot,\
            'To log back in, type / again, or // to leave the chatroom'))
        async for message in user.ws:
            await user.ws.send(message_line(you,message))
            if message == '/':
                user.online = True
                break
            elif message == '//':
                self.registered_users.remove(user)
                for receiver in self.registered_users:
                    if receiver.online:
                        await receiver.ws.send(goodbye_message(user.name))
            else:
                user.ws.send(message_line(bot,'Invalid command...'))
    
    async def notify_users(self, new_user):
        for user in self.registered_users:
            if new_user != user and user.online:
                await user.ws.send(welcome_message(new_user.name))

    async def public_message(self, sender, message):
        for receiver in self.registered_users:
            if receiver.name != sender.name and receiver.online:
                await receiver.ws.send(message_line(sender.name, message))
            elif receiver.online:
                await receiver.ws.send(message_line(you, message))

    async def private_message(self, sender, receiver, message):
        for user in self.registered_users:
            if user.name == receiver and user.online:
                await user.ws.send(f'Private message received: {message_line(sender.name, message)}')
                await sender.ws.send(f'Private message sent to {user.name}: {message_line(you, message)}')
                return False
        return True

    async def options(self, user):
        await user.ws.send(message_line(bot,\
            'Your options are:\n - Type ? for help; - Type / to logout'))
        
    async def action_trigger(self, sender):
        async for message in sender.ws:
            if message[0] == '<':
                receiver = ''
                i = 2
                for char in message[1:]:
                    if char == '>':
                        message = message[i:]
                        break
                    receiver += char
                    i += 1
                error = await self.private_message(sender, receiver, message)
                if error:
                    await sender.ws.send(message_line(bot, error_private(receiver)))

            elif message[0] == '/':
                await self.logout(sender)
            elif message[0] == '?':
                await self.options(sender)

            else:
                await self.public_message(sender, message)

    def verify_name(self, name):
        for registered_user in self.registered_users:
            if name == registered_user.name:
                return False
        return True

server = Server()
start_server = websockets.serve(server.start, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()