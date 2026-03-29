#!/usr/bin/env python
"""Test Observability Stack."""

import requests

PROMETHEUS_URL = 'http://localhost:9090'
GRAFANA_URL = 'http://localhost:3000'
JAEGER_URL = 'http://localhost:16686'
LOKI_URL = 'http://localhost:3100'


def check_service(name, url, timeout=10):
    try:
        response = requests.get(url, timeout=timeout)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {name}: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"✗ {name}: {e}")
        return False


def test_prometheus():
    print('\n=== Testing Prometheus ===')
    check_service('Prometheus Health', f'{PROMETHEUS_URL}/-/healthy')
    check_service('Prometheus Targets', f'{PROMETHEUS_URL}/api/v1/targets')


def test_grafana():
    print('\n=== Testing Grafana ===')
    check_service('Grafana Login', f'{GRAFANA_URL}/login')
    check_service('Grafana Health', f'{GRAFANA_URL}/api/health')


def test_jaeger():
    print('\n=== Testing Jaeger ===')
    check_service('Jaeger UI', f'{JAEGER_URL}/')
    check_service('Jaeger Services', f'{JAEGER_URL}/api/services')


def test_loki():
    print('\n=== Testing Loki ===')
    check_service('Loki Ready', f'{LOKI_URL}/ready')


def test_metrics_endpoint():
    print('\n=== Testing Application Metrics ===')
    check_service('Backend Metrics', 'http://localhost:8000/metrics')
    check_service('Inference Metrics', 'http://localhost:8004/metrics')


if __name__ == '__main__':
    print('Observability Stack Verification')
    print('=' * 50)

    test_prometheus()
    test_grafana()
    test_jaeger()
    test_loki()
    test_metrics_endpoint()

    print('\n' + '=' * 50)
    print('\nAccess URLs:')
    print(f'  Prometheus:   {PROMETHEUS_URL}')
    print(f'  Grafana:      {GRAFANA_URL} (admin/admin)')
    print(f'  Jaeger:       {JAEGER_URL}')
    print(f'  Loki:         {LOKI_URL}')
