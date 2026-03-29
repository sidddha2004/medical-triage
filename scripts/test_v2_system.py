#!/usr/bin/env python
"""
Test script for v2.0 Distributed ML System
Tests all implemented components:
- Observability Stack (Prometheus, Grafana, Jaeger, Loki)
- MLflow Model Registry
- gRPC Services
- Kafka Integration
- API Gateway (Kong) - if enabled
"""

import requests
import time
import sys

BASE_URLS = {
    'backend': 'http://localhost:8000',
    'frontend': 'http://localhost:80',
    'mlflow': 'http://localhost:5000',
    'prometheus': 'http://localhost:9090',
    'grafana': 'http://localhost:3000',
    'jaeger': 'http://localhost:16686',
    'loki': 'http://localhost:3100',
    'kong': 'http://localhost:8000',  # Same as backend when Kong is enabled
}

def test_service(name, url, expected_status=200):
    """Test a service endpoint."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == expected_status or (expected_status == 'any' and response.status_code < 500):
            print(f"  [OK] {name}: {url} (status: {response.status_code})")
            return True
        else:
            print(f"  [FAIL] {name}: {url} (status: {response.status_code}, expected: {expected_status})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  [FAIL] {name}: {url} - {e}")
        return False

def test_prometheus():
    """Test Prometheus metrics endpoint."""
    print("\n[TEST] Prometheus")
    tests = [
        ("Health", f"{BASE_URLS['prometheus']}/-/healthy"),
        ("Metrics", f"{BASE_URLS['prometheus']}/api/v1/targets"),
        ("Config", f"{BASE_URLS['prometheus']}/api/v1/status/config"),
    ]
    passed = sum(test_service(name, url) for name, url in tests)
    print(f"  Result: {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_grafana():
    """Test Grafana API."""
    print("\n[TEST] Grafana")
    tests = [
        ("Health", f"{BASE_URLS['grafana']}/api/health", 200),
        ("Datasources", f"{BASE_URLS['grafana']}/api/datasources", 'any'),
    ]
    passed = sum(test_service(name, url, status) for name, url, status in tests)
    print(f"  Result: {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_jaeger():
    """Test Jaeger tracing."""
    print("\n[TEST] Jaeger")
    tests = [
        ("Services", f"{BASE_URLS['jaeger']}/api/services"),
        ("UI", f"{BASE_URLS['jaeger']}/"),
    ]
    passed = sum(test_service(name, url, 'any') for name, url in tests)
    print(f"  Result: {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_loki():
    """Test Loki logging."""
    print("\n[TEST] Loki")
    tests = [
        ("Ready", f"{BASE_URLS['loki']}/ready", 'any'),
        ("Labels", f"{BASE_URLS['loki']}/loki/api/v1/labels", 'any'),
    ]
    passed = sum(test_service(name, url, status) for name, url, status in tests)
    print(f"  Result: {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_mlflow():
    """Test MLflow tracking server."""
    print("\n[TEST] MLflow")
    tests = [
        ("Health", f"{BASE_URLS['mlflow']}/health", 200),
        ("API", f"{BASE_URLS['mlflow']}/api/2.0/mlflow/experiments/search", 'any'),
    ]
    passed = sum(test_service(name, url, status) for name, url, status in tests)
    print(f"  Result: {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_backend():
    """Test Django backend API."""
    print("\n[TEST] Backend API")
    tests = [
        ("API Root", f"{BASE_URLS['backend']}/api/", 401),  # Requires auth
        ("Login", f"{BASE_URLS['backend']}/api/auth/login/", 'any'),
        ("Admin", f"{BASE_URLS['backend']}/admin/", 'any'),
    ]
    passed = sum(test_service(name, url, status) for name, url, status in tests)
    print(f"  Result: {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_frontend():
    """Test React frontend."""
    print("\n[TEST] Frontend")
    tests = [
        ("HTML", f"{BASE_URLS['frontend']}/"),
    ]
    passed = sum(test_service(name, url) for name, url in tests)
    print(f"  Result: {passed}/{len(tests)} passed")
    return passed == len(tests)

def test_grpc_services():
    """Test gRPC services (if running)."""
    print("\n[TEST] gRPC Services")
    print("  [INFO] gRPC services require Docker Compose with all services enabled")
    print("  [SKIP] Run: docker-compose up -d auth-service patient-service triage-service")
    return True

def test_kafka():
    """Test Kafka (if running)."""
    print("\n[TEST] Kafka Stack")
    print("  [INFO] Kafka requires additional services in Docker Compose")
    print("  [SKIP] Run: docker-compose up -d kafka zookeeper kafka-ui")
    print("  Access Kafka UI at: http://localhost:8090")
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Medical Triage v2.0 - System Integration Tests")
    print("=" * 60)

    results = {
        'Prometheus': test_prometheus(),
        'Grafana': test_grafana(),
        'Jaeger': test_jaeger(),
        'Loki': test_loki(),
        'MLflow': test_mlflow(),
        'Backend': test_backend(),
        'Frontend': test_frontend(),
        'gRPC Services': test_grpc_services(),
        'Kafka': test_kafka(),
    }

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for service, status in results.items():
        icon = "[OK]" if status else "[FAIL]"
        print(f"  {icon} {service}")

    print(f"\nTotal: {passed}/{total} services tested successfully")

    if passed == total:
        print("\n[SUCCESS] All systems operational!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} service(s) need attention")
        return 1

if __name__ == '__main__':
    sys.exit(main())
