#!/usr/bin/env python
"""
Inference Service Entrypoint

Runs FastAPI app and gRPC server.
"""

import uvicorn
import os
from api import app

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8004))

    print(f'Starting Inference Service on {host}:{port}')
    print(f'HTTP API: http://{host}:{port}')
    print(f'Metrics: http://{host}:{port}/metrics')

    uvicorn.run(app, host=host, port=port)
