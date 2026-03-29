import os
import sys
import asyncio

sys.path.append('d:/medical-triage/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from backend.asgi import application

async def run_asgi():
    scope = {
        'type': 'http',
        'http_version': '1.1',
        'method': 'GET',
        'path': '/admin/',
        'raw_path': b'/admin/',
        'query_string': b'',
        'headers': [
            (b'host', b'127.0.0.1:8000')
        ]
    }
    
    async def receive():
        return {'type': 'http.request', 'body': b'', 'more_body': False}
        
    async def send(message):
        print("MESSAGE:", message)

    try:
        await application(scope, receive, send)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(run_asgi())
