"""
WebSocket Consumer for Health Triage Chat

Handles real-time communication with the AI agent.
"""

import json
import asyncio
from typing import List, Dict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

from .langchain_agent import triage_agent
from core.models import TriageSession, AgentMessage, Patient

@database_sync_to_async
def get_user_from_token(token_str):
    from rest_framework_simplejwt.tokens import AccessToken
    try:
        access_token = AccessToken(token_str)
        user_id = access_token.get('user_id')
        return User.objects.get(id=user_id)
    except Exception:
        return None


class TriageConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time triage chat."""

    async def connect(self):
        """Handle WebSocket connection."""
        # Get session ID from URL
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            from urllib.parse import parse_qs
            qs = parse_qs(self.scope.get('query_string', b'').decode('utf-8'))
            token = qs.get('token', [None])[0]
            if token:
                user = await get_user_from_token(token)
                if user:
                    self.user = user
                    self.scope['user'] = user

        if not self.user.is_authenticated:
            await self.close()
            return

        # Accept connection
        await self.channel_layer.group_add(
            f"triage_{self.user.id}",
            self.channel_name
        )
        await self.accept()

        # Send welcome message
        await self.send_json({
            'type': 'connection',
            'status': 'connected',
            'session_id': self.session_id
        })

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f"triage_{self.user.id}",
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming message from user."""
        try:
            data = json.loads(text_data)
            message = data.get('message', '')

            if not message:
                await self.send_json({
                    'type': 'error',
                    'message': 'Empty message'
                })
                return

            # Save user message to database
            if self.session_id:
                await self.save_message_async('user', message)

            # Get agent response
            agent_response = await self.get_agent_response(message)

            # Send response
            await self.send_json({
                'type': 'message',
                'content': agent_response,
                'session_id': self.session_id
            })

            # Save agent response to database
            if self.session_id:
                await self.save_message_async('agent', agent_response)

        except json.JSONDecodeError:
            await self.send_json({
                'type': 'error',
                'message': 'Invalid JSON'
            })
        except Exception as e:
            await self.send_json({
                'type': 'error',
                'message': str(e)
            })

    async def get_agent_response(self, message: str) -> str:
        """Get response from AI agent."""
        try:
            # Use synchronous call in async context
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: triage_agent.chat(message, self.session_id)
            )
            return response
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"

    @database_sync_to_async
    def save_message_async(self, role: str, content: str):
        """Save message to database (async wrapper)."""
        try:
            session = TriageSession.objects.get(id=self.session_id)
            AgentMessage.objects.create(
                session=session,
                role=role,
                content=content
            )
        except Exception:
            pass  # Silently fail if session doesn't exist

    async def send_escalation_alert(self, event):
        """Handle escalation alert event."""
        await self.send_json({
            'type': 'escalation',
            'triage_level': event.get('triage_level'),
            'message': event.get('message')
        })


class SimpleTriageConsumer(AsyncWebsocketConsumer):
    """
    Simplified WebSocket consumer for /ws/triage/ endpoint.
    Handles session-less chat that creates sessions automatically.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        try:
            self.user = self.scope.get('user')
            print(f'Consumer connect: user={self.user}')

            # Check if user is authenticated
            if not self.user or not hasattr(self.user, 'is_authenticated') or not self.user.is_authenticated:
                print(f'WebSocket reject: user={self.user}')
                await self.close(code=4001)
                return

            print(f'WebSocket accepted for user: {self.user.email}')
            await self.accept()

            await self.send(json.dumps({
                'type': 'connected',
                'message': 'Connected to Health Triage Assistant'
            }))
        except Exception as e:
            print(f'Error in connect: {e}')
            import traceback
            traceback.print_exc()
            await self.close()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f"user_{self.user.id}",
                self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming message."""
        try:
            data = json.loads(text_data)
            message = data.get('message', '')
            session_id = data.get('session_id')

            if not message:
                await self.send(json.dumps({'type': 'error', 'message': 'Empty message'}))
                return

            # Get or create session
            if session_id:
                session = await self.get_session_async(session_id)
            else:
                session = await self.create_session_async()
                session_id = session.id

            # Save user message first
            await self.save_message_async(session_id, 'user', message)

            # Load conversation history (after saving current message)
            history = await self.get_conversation_history(session_id)

            # Get agent response with history
            response = await self.get_agent_response_with_history(message, session_id, history)

            # Save and send response
            await self.save_message_async(session_id, 'agent', response)
            await self.send(json.dumps({
                'type': 'message',
                'content': response,
                'session_id': session_id
            }))

        except Exception as e:
            await self.send(json.dumps({'type': 'error', 'message': str(e)}))

    async def get_agent_response_with_history(self, message: str, session_id: int, history: List[Dict]) -> str:
        """Get response from AI agent with conversation history."""
        from langchain_core.messages import AIMessage

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: triage_agent.chat(message, session_id, history)
        )

        # Extract text from various response formats
        if isinstance(result, AIMessage):
            content = result.content
            # Handle Gemini's complex content format (list of dicts)
            if isinstance(content, list):
                # Extract text from Gemini response format
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if 'text' in item:
                            text_parts.append(item['text'])
                        elif 'content' in item:
                            text_parts.append(item['content'])
                    elif isinstance(item, str):
                        text_parts.append(item)
                return ' '.join(text_parts) if text_parts else str(content)
            return content
        elif isinstance(result, dict) and 'messages' in result:
            msgs = result['messages']
            if msgs:
                last = msgs[-1]
                if isinstance(last, AIMessage):
                    content = last.content
                    # Handle Gemini's complex content format
                    if isinstance(content, list):
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict):
                                if 'text' in item:
                                    text_parts.append(item['text'])
                                elif 'content' in item:
                                    text_parts.append(item['content'])
                            elif isinstance(item, str):
                                text_parts.append(item)
                        return ' '.join(text_parts) if text_parts else str(content)
                    return content
                elif isinstance(last, dict) and 'content' in last:
                    return last['content']
        elif isinstance(result, str):
            return result
        return str(result)

    @database_sync_to_async
    def get_conversation_history(self, session_id: int) -> List[Dict]:
        """Get conversation history for a session."""
        try:
            messages = AgentMessage.objects.filter(
                session_id=session_id
            ).order_by('timestamp')[:20]  # Last 20 messages

            return [
                {'role': msg.role, 'content': msg.content}
                for msg in messages
            ]
        except Exception as e:
            print(f"Error loading history: {e}")
            return []

    @database_sync_to_async
    def get_session_async(self, session_id: int):
        """Get session by ID."""
        return TriageSession.objects.get(id=session_id)

    @database_sync_to_async
    def create_session_async(self):
        """Create new triage session for user."""
        patient, _ = Patient.objects.get_or_create(user=self.user)
        return TriageSession.objects.create(
            patient=patient,
            status='active',
            primary_symptoms=[]
        )

    @database_sync_to_async
    def save_message_async(self, session_id: int, role: str, content: str):
        """Save message to database."""
        try:
            session = TriageSession.objects.get(id=session_id)
            AgentMessage.objects.create(
                session=session,
                role=role,
                content=content
            )
        except Exception:
            pass
