import os
import sys
from io import BytesIO

sys.path.append('d:/medical-triage/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.core.handlers.wsgi import WSGIHandler

app = WSGIHandler()
environ = {
    'REQUEST_METHOD': 'GET',
    'SCRIPT_NAME': '',
    'PATH_INFO': '/admin/',
    'SERVER_NAME': '127.0.0.1',
    'SERVER_PORT': '8000',
    'HTTP_HOST': '127.0.0.1:8000',
    'wsgi.version': (1,0),
    'wsgi.input': BytesIO(b''),
    'wsgi.errors': sys.stderr,
    'wsgi.multithread': False,
    'wsgi.multiprocess': False,
    'wsgi.run_once': False,
    'wsgi.url_scheme': 'http',
}

def start_response(status, headers, exc_info=None):
    print("STATUS", status)
    print("HEADERS", headers)

try:
    response = app(environ, start_response)
    for data in response:
        print(data.decode('utf-8', errors='replace')[:200])
except Exception as e:
    import traceback
    traceback.print_exc()
