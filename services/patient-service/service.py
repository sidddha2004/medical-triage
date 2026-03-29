"""
Patient Service - gRPC Patient Management Service
"""
import grpc
from concurrent import futures
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patient_service.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Patient, TriageSession, Prediction
import patient_pb2
import patient_pb2_grpc
from datetime import datetime


class PatientServiceServicer(patient_pb2_grpc.PatientServiceServicer):
    """gRPC Patient Service implementation."""

    def GetPatient(self, request, context):
        try:
            patient = Patient.objects.get(user_id=request.user_id)
            return patient_pb2.PatientResponse(
                success=True,
                patient_id=patient.id,
                user_id=patient.user.id,
                email=patient.user.email,
                date_of_birth=str(patient.date_of_birth) if patient.date_of_birth else '',
                gender=patient.gender,
                blood_type=patient.blood_type or '',
                created_at=patient.created_at.isoformat()
            )

        except Patient.DoesNotExist:
            return patient_pb2.PatientResponse(
                success=False,
                error='Patient profile not found'
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return patient_pb2.PatientResponse(
                success=False,
                error=str(e)
            )

    def CreatePatient(self, request, context):
        try:
            user = User.objects.get(id=request.user_id)
            patient = Patient.objects.create(
                user=user,
                date_of_birth=request.date_of_birth if request.date_of_birth else None,
                gender=request.gender or 'prefer_not_to_say',
                blood_type=request.blood_type or None
            )

            return patient_pb2.PatientResponse(
                success=True,
                patient_id=patient.id,
                user_id=patient.user.id,
                email=patient.user.email,
                gender=patient.gender,
                blood_type=patient.blood_type or '',
                created_at=patient.created_at.isoformat()
            )

        except User.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return patient_pb2.PatientResponse(
                success=False,
                error='User not found'
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return patient_pb2.PatientResponse(
                success=False,
                error=str(e)
            )

    def UpdatePatient(self, request, context):
        try:
            patient = Patient.objects.get(id=request.patient_id)

            if request.date_of_birth:
                patient.date_of_birth = request.date_of_birth
            if request.gender:
                patient.gender = request.gender
            if request.blood_type:
                patient.blood_type = request.blood_type

            patient.save()

            return patient_pb2.PatientResponse(
                success=True,
                patient_id=patient.id,
                user_id=patient.user.id,
                email=patient.user.email,
                gender=patient.gender,
                blood_type=patient.blood_type or '',
            )

        except Patient.DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return patient_pb2.PatientResponse(
                success=False,
                error='Patient not found'
            )
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return patient_pb2.PatientResponse(
                success=False,
                error=str(e)
            )

    def GetPatientHistory(self, request, context):
        try:
            sessions = TriageSession.objects.filter(
                patient_id=request.patient_id
            ).order_by('-started_at')[:request.limit]

            entries = []
            for session in sessions:
                prediction = Prediction.objects.filter(session=session).first()
                entries.append(patient_pb2.HistoryEntry(
                    session_id=session.id,
                    started_at=session.started_at.isoformat(),
                    status=session.status,
                    triage_level=session.triage_level or '',
                    symptoms=session.primary_symptoms or [],
                    disease=prediction.disease if prediction else '',
                    confidence=prediction.confidence if prediction else 0.0
                ))

            return patient_pb2.HistoryResponse(
                success=True,
                entries=entries
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return patient_pb2.HistoryResponse(
                success=False,
                error=str(e)
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    patient_pb2_grpc.add_PatientServiceServicer_to_server(
        PatientServiceServicer(), server
    )
    server.add_insecure_port('[::]:50052')
    server.start()
    print('Patient Service started on port 50052')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
