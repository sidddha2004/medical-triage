"""
Triage Service - gRPC Triage Session Management
"""
import grpc
from concurrent import futures
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'triage_service.settings')
django.setup()

from core.models import Patient, TriageSession, Message
import triage_pb2
import triage_pb2_grpc
from datetime import datetime


class TriageServiceServicer(triage_pb2_grpc.TriageServiceServicer):
    """gRPC Triage Service implementation."""

    def CreateSession(self, request, context):
        try:
            session = TriageSession.objects.create(
                patient_id=request.patient_id,
                status='active',
                primary_symptoms=list(request.symptoms)
            )

            return triage_pb2.SessionResponse(
                success=True,
                session_id=session.id,
                patient_id=session.patient_id,
                started_at=session.started_at.isoformat(),
                status=session.status,
                symptoms=session.primary_symptoms or []
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return triage_pb2.SessionResponse(
                success=False,
                error=str(e)
            )

    def GetSession(self, request, context):
        try:
            session = TriageSession.objects.get(id=request.session_id)
            return triage_pb2.SessionResponse(
                success=True,
                session_id=session.id,
                patient_id=session.patient_id,
                started_at=session.started_at.isoformat(),
                ended_at=session.ended_at.isoformat() if session.ended_at else '',
                status=session.status,
                triage_level=session.triage_level or '',
                symptoms=session.primary_symptoms or []
            )

        except TriageSession.DoesNotExist:
            return triage_pb2.SessionResponse(
                success=False,
                error='Session not found'
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return triage_pb2.SessionResponse(
                success=False,
                error=str(e)
            )

    def UpdateSession(self, request, context):
        try:
            session = TriageSession.objects.get(id=request.session_id)

            if request.status:
                session.status = request.status
            if request.triage_level:
                session.triage_level = request.triage_level

            session.save()

            return triage_pb2.SessionResponse(
                success=True,
                session_id=session.id,
                patient_id=session.patient_id,
                status=session.status,
                triage_level=session.triage_level or ''
            )

        except TriageSession.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return triage_pb2.SessionResponse(
                success=False,
                error='Session not found'
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return triage_pb2.SessionResponse(
                success=False,
                error=str(e)
            )

    def EndSession(self, request, context):
        try:
            session = TriageSession.objects.get(id=request.session_id)
            session.status = 'completed'
            session.ended_at = datetime.now()
            session.save()

            return triage_pb2.SessionResponse(
                success=True,
                session_id=session.id,
                ended_at=session.ended_at.isoformat(),
                status=session.status
            )

        except TriageSession.DoesNotExist:
            return triage_pb2.SessionResponse(
                success=False,
                error='Session not found'
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return triage_pb2.SessionResponse(
                success=False,
                error=str(e)
            )

    def SaveMessage(self, request, context):
        try:
            message = Message.objects.create(
                session_id=request.session_id,
                role=request.role,
                content=request.content
            )

            return triage_pb2.MessageResponse(
                success=True,
                message_id=message.id
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return triage_pb2.MessageResponse(
                success=False,
                error=str(e)
            )

    def GetMessages(self, request, context):
        try:
            messages = Message.objects.filter(
                session_id=request.session_id
            ).order_by('created_at')[:request.limit]

            msg_list = []
            for msg in messages:
                msg_list.append(triage_pb2.Message(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.created_at.isoformat() if msg.created_at else ''
                ))

            return triage_pb2.MessagesResponse(
                success=True,
                messages=msg_list
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return triage_pb2.MessagesResponse(
                success=False,
                error=str(e)
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    triage_pb2_grpc.add_TriageServiceServicer_to_server(
        TriageServiceServicer(), server
    )
    server.add_insecure_port('[::]:50054')
    server.start()
    print('Triage Service started on port 50054')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
