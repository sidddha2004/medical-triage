#!/usr/bin/env python
"""Test Inference Service."""

import requests
import time
import json

BASE_URL = 'http://localhost:8004'


def test_health():
    print('\n=== Testing Health Endpoint ===')
    response = requests.get(f'{BASE_URL}/health')
    print(f'Status: {response.status_code}')
    print(f'Response: {response.json()}')


def test_model_status():
    print('\n=== Testing Model Status ===')
    response = requests.get(f'{BASE_URL}/model/status')
    print(f'Status: {response.status_code}')
    print(f'Response: {json.dumps(response.json(), indent=2)}')


def test_predict():
    print('\n=== Testing Prediction ===')
    payload = {'symptoms': ['fever', 'headache', 'fatigue']}
    start = time.time()
    response = requests.post(f'{BASE_URL}/predict', json=payload)
    latency = (time.time() - start) * 1000
    print(f'Status: {response.status_code}')
    result = response.json()
    print(f'Disease: {result.get("disease")}')
    print(f'Confidence: {result.get("confidence", 0):.2%}')
    print(f'Latency: {latency:.2f}ms')
    print(f'Cache Hit: {result.get("cache_hit")}')


def test_cache():
    print('\n=== Testing Caching ===')
    payload = {'symptoms': ['itching', 'skin_rash', 'fever']}
    response1 = requests.post(f'{BASE_URL}/predict', json=payload)
    result1 = response1.json()
    response2 = requests.post(f'{BASE_URL}/predict', json=payload)
    result2 = response2.json()
    print(f'First request  - Cache Hit: {result1.get("cache_hit")}, Latency: {result1.get("latency_ms", 0):.2f}ms')
    print(f'Second request - Cache Hit: {result2.get("cache_hit")}, Latency: {result2.get("latency_ms", 0):.2f}ms')


def test_metrics():
    print('\n=== Testing Metrics ===')
    response = requests.get(f'{BASE_URL}/metrics')
    metrics = response.text
    for line in metrics.split('\n'):
        if 'inference_' in line and not line.startswith('#'):
            print(line)


if __name__ == '__main__':
    print('Inference Service Tests')
    print('=' * 50)
    test_health()
    test_model_status()
    test_predict()
    test_cache()
    test_metrics()
    print('\n' + '=' * 50)
    print('Tests complete!')
