"""
Auth Service - gRPC Authentication Service
"""
import grpc
from concurrent import futures
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import auth_pb2
import auth_pb2_grpc


class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    """gRPC Auth Service implementation."""

    def Register(self, request, context):
        try:
            # Check if user exists
            if User.objects.filter(email=request.email).exists():
                context.set_details('User already exists')
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                return auth_pb2.AuthResponse(
                    success=False,
                    error='User with this email already exists'
                )

            # Create user
            user = User.objects.create_user(
                email=request.email,
                password=request.password,
                username=request.email
            )

            # Generate tokens
            refresh = RefreshToken.for_user(user)

            return auth_pb2.AuthResponse(
                success=True,
                access_token=str(refresh.access_token),
                refresh_token=str(refresh),
                user_id=user.id,
                email=user.email
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return auth_pb2.AuthResponse(
                success=False,
                error=str(e)
            )

    def Login(self, request, context):
        try:
            user = authenticate(
                username=request.email,
                password=request.password
            )

            if not user:
                context.set_details('Invalid credentials')
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                return auth_pb2.AuthResponse(
                    success=False,
                    error='Invalid email or password'
                )

            refresh = RefreshToken.for_user(user)

            return auth_pb2.AuthResponse(
                success=True,
                access_token=str(refresh.access_token),
                refresh_token=str(refresh),
                user_id=user.id,
                email=user.email
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return auth_pb2.AuthResponse(
                success=False,
                error=str(e)
            )

    def Verify(self, request, context):
        try:
            from rest_framework_simplejwt.tokens import AccessToken

            try:
                token = AccessToken(request.token)
                from django.contrib.auth.models import User
                return auth_pb2.VerifyResponse(
                    valid=True,
                    user_id=token.get('user_id'),
                    email=User.objects.get(id=token.get('user_id')).email
                )
            except Exception:
                return auth_pb2.VerifyResponse(
                    valid=False,
                    error='Invalid or expired token'
                )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return auth_pb2.VerifyResponse(
                valid=False,
                error=str(e)
            )

    def Refresh(self, request, context):
        try:
            refresh = RefreshToken(request.refresh_token)
            access_token = refresh.access_token

            return auth_pb2.AuthResponse(
                success=True,
                access_token=str(access_token),
                refresh_token=str(refresh)
            )

        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            return auth_pb2.AuthResponse(
                success=False,
                error=str(e)
            )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthServiceServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print('Auth Service started on port 50051')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
