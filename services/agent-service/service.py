"""
Agent Service - gRPC LangChain Agent Service
"""
import grpc
from concurrent import futures
import os
import json

import agent_pb2
import agent_pb2_grpc

# Import LangChain components
try:
    from langchain.chat_models import ChatOpenAI
    from langchain.agents import initialize_agent, Tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class AgentServiceServicer(agent_pb2_grpc.AgentServiceServicer):
    """gRPC Agent Service implementation."""

    def __init__(self):
        self.chat_model = None
        if LANGCHAIN_AVAILABLE and os.environ.get('GOOGLE_API_KEY'):
            try:
                self.chat_model = ChatOpenAI(
                    model='gemini-pro',
                    temperature=0.7
                )
                print('Agent Service initialized with LangChain')
            except Exception as e:
                print(f'Warning: Could not initialize LangChain: {e}')

    def Chat(self, request, context):
        try:
            if not self.chat_model:
                return agent_pb2.ChatResponse(
                    content='AI agent not configured. Set GOOGLE_API_KEY environment variable.',
                    is_complete=True
                )

            # Build conversation history
            history_text = ""
            for msg in request.history:
                role = "Human" if msg.role == "user" else "Assistant"
                history_text += f"{role}: {msg.content}\n"

            # Create prompt
            prompt = f"""You are a helpful medical triage assistant. Help users understand potential health conditions based on their symptoms.

Conversation History:
{history_text}

User: {request.message}
Assistant:"""

            # Generate response
            response = self.chat_model.predict(prompt)

            return agent_pb2.ChatResponse(
                content=response,
                is_complete=True
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return agent_pb2.ChatResponse(
                content='',
                is_complete=True,
                error=str(e)
            )

    def ChatStream(self, request, context):
        """Streaming chat - yields response chunks."""
        try:
            if not self.chat_model:
                yield agent_pb2.ChatResponse(
                    content='AI agent not configured.',
                    is_complete=True
                )
                return

            # For streaming, we'd use the model's streaming capability
            # This is a simplified version
            response = self.Chat(request, context)
            yield response

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            yield agent_pb2.ChatResponse(
                content='',
                is_complete=True,
                error=str(e)
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agent_pb2_grpc.add_AgentServiceServicer_to_server(
        AgentServiceServicer(), server
    )
    server.add_insecure_port('[::]:50055')
    server.start()
    print('Agent Service started on port 50055')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
