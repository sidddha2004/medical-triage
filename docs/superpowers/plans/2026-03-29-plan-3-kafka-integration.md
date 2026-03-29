# Kafka Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Apache Kafka for event-driven communication between services.

**Architecture:** Kafka replaces direct service calls for async operations. Services publish events to topics and consume events they care about. Enables event sourcing, replay, and loose coupling.

**Tech Stack:** Apache Kafka (Docker), confluent-kafka Python client, Kafka Streams for processing, Schema Registry for message validation

---

## Files Overview

| File | Action | Responsibility |
|------|--------|----------------|
| `docker/docker-compose.yml` | Modify | Add Kafka + Schema Registry |
| `backend/kafka_config.py` | Create | Kafka producer/consumer config |
| `backend/kafka/producers.py` | Create | Event publishers |
| `backend/kafka/consumers.py` | Create | Event subscribers |
| `backend/kafka/schemas.py` | Create | Message schemas |
| `backend/kafka/topics.py` | Create | Topic definitions |

---

### Task 1: Kafka Docker Infrastructure

**Files:**
- Modify: `docker/docker-compose.yml`

- [ ] **Step 1: Add Kafka and Zookeeper to docker-compose**

Read current docker-compose.yml, then add:

```yaml
services:
  # ... existing postgres, redis, etc ...

  # Zookeeper (required for Kafka)
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: medical_triage_zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"
    networks:
      - medical_triage_network
    healthcheck:
      test: ["CMD", "nc", "-z", "localhost", "2181"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Kafka Broker
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: medical_triage_kafka
    depends_on:
      zookeeper:
        condition: service_healthy
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092,PLAINTEXT_HOST://0.0.0.0:9092
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_NUM_PARTITIONS: 3
    volumes:
      - kafka_data:/var/lib/kafka/data
    networks:
      - medical_triage_network
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Kafka UI (for monitoring)
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: medical_triage_kafka_ui
    depends_on:
      - kafka
    ports:
      - "8090:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: medical-triage
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181
    networks:
      - medical_triage_network

  # Schema Registry (for message validation)
  schema-registry:
    image: confluentinc/cp-schema-registry:7.5.0
    container_name: medical_triage_schema_registry
    depends_on:
      - kafka
    ports:
      - "8081:8081"
    environment:
      SCHEMA_REGISTRY_HOST_NAME: schema-registry
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: kafka:29092
      SCHEMA_REGISTRY_LISTENERS: http://0.0.0.0:8081
    networks:
      - medical_triage_network

volumes:
  kafka_data:
```

- [ ] **Step 2: Commit**

```bash
git add docker/docker-compose.yml
git commit -m "infra: add Kafka, Zookeeper, Schema Registry, and Kafka UI"
```

---

### Task 2: Kafka Python Configuration

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/kafka_config.py`

- [ ] **Step 1: Add Kafka dependencies**

Add to `backend/requirements.txt`:

```txt
# Kafka
confluent-kafka>=2.3.0
fastavro>=1.9.0  # For Avro schema support
```

- [ ] **Step 2: Create Kafka configuration**

```python
# backend/kafka_config.py
"""
Kafka Configuration for Health Triage Assistant.

Centralized Kafka producer/consumer configuration.
"""

from django.conf import settings
import json


# Kafka Broker Configuration
KAFKA_BOOTSTRAP_SERVERS = getattr(
    settings, 'KAFKA_BOOTSTRAP_SERVERS',
    ['localhost:9092']
)

KAFKA_SCHEMA_REGISTRY = getattr(
    settings, 'KAFKA_SCHEMA_REGISTRY',
    'http://localhost:8081'
)

# Producer Configuration
KAFKA_PRODUCER_CONFIG = {
    'bootstrap.servers': ','.join(KAFKA_BOOTSTRAP_SERVERS),
    'client.id': 'health-triage-producer',
    'acks': 'all',  # Wait for all replicas to acknowledge
    'retries': 5,
    'retry.backoff.ms': 100,
    'delivery.timeout.ms': 30000,
    'linger.ms': 5,  # Batch messages within 5ms window
    'batch.num.messages': 10000,
    'batch.size': 1048576,  # 1MB batch size
    'compression.type': 'snappy',  # Compression for efficiency
    'enable.idempotence': True,  # Exactly-once semantics
}

# Consumer Configuration
KAFKA_CONSUMER_CONFIG = {
    'bootstrap.servers': ','.join(KAFKA_BOOTSTRAP_SERVERS),
    'group.id': 'health-triage-consumer',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'auto.commit.interval.ms': 1000,
    'session.timeout.ms': 30000,
    'max.poll.records': 500,
}

# Topic Definitions
KAFKA_TOPICS = {
    'triage-requests': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': 604800000,  # 7 days
            'cleanup.policy': 'delete',
        }
    },
    'inference-jobs': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': 86400000,  # 1 day
            'cleanup.policy': 'delete',
        }
    },
    'async-events': {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': 259200000,  # 3 days
            'cleanup.policy': 'delete',
        }
    },
    'audit-logs': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': 7776000000,  # 90 days
            'cleanup.policy': 'delete',
        }
    },
    'triage-completions': {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': 604800000,  # 7 days
            'cleanup.policy': 'delete',
        }
    },
    'escalation-alerts': {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': 259200000,  # 3 days
            'cleanup.policy': 'delete',
        }
    },
}


def get_topic_config(topic_name: str) -> dict:
    """Get configuration for a specific topic."""
    return KAFKA_TOPICS.get(topic_name, {
        'partitions': 3,
        'replication_factor': 1,
        'config': {}
    })


def create_topics():
    """Create all required Kafka topics."""
    from confluent_kafka.admin import AdminClient, NewTopic

    admin_client = AdminClient({
        'bootstrap.servers': ','.join(KAFKA_BOOTSTRAP_SERVERS)
    })

    topics = []
    for topic_name, config in KAFKA_TOPICS.items():
        topic = NewTopic(
            topic_name,
            num_partitions=config['partitions'],
            replication_factor=config['replication_factor'],
            config=config['config']
        )
        topics.append(topic)

    # Create topics
    fs = admin_client.create_topics(topics)

    # Wait for each operation to finish
    for topic, future in fs.items():
        try:
            future.result()
            print(f'Topic created: {topic}')
        except Exception as e:
            if 'TOPIC_ALREADY_EXISTS' in str(e):
                print(f'Topic already exists: {topic}')
            else:
                print(f'Error creating topic {topic}: {e}')

    admin_client.close()
```

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt backend/kafka_config.py
git commit -m "feat(kafka): add Kafka configuration and topic definitions"
```

---

### Task 3: Kafka Message Schemas

**Files:**
- Create: `backend/kafka/schemas.py`
- Create: `backend/kafka/topics.py`

- [ ] **Step 1: Define message schemas**

```python
# backend/kafka/schemas.py
"""
Kafka Message Schemas for Health Triage.

Defines the structure of messages published to Kafka topics.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class TriageRequestEvent:
    """Event: User submitted symptoms for triage."""
    event_id: str
    session_id: int
    patient_id: int
    user_id: int
    symptoms: List[str]
    notes: str
    timestamp: str
    source: str = 'web'

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'TriageRequestEvent':
        d = json.loads(data)
        return cls(**d)


@dataclass
class InferenceRequestEvent:
    """Event: Request for ML inference."""
    event_id: str
    request_id: str
    session_id: int
    symptoms: List[str]
    model_version: Optional[str] = None
    priority: str = 'normal'  # normal, high
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class InferenceResponseEvent:
    """Event: ML inference completed."""
    event_id: str
    request_id: str
    session_id: int
    disease: str
    confidence: float
    matched_symptoms: List[str]
    precautions: List[str]
    model_version: str
    latency_ms: float
    cache_hit: bool
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class TriageCompletionEvent:
    """Event: Triage session completed."""
    event_id: str
    session_id: int
    patient_id: int
    user_id: int
    disease: str
    confidence: float
    triage_level: str
    total_duration_seconds: float
    message_count: int
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class EscalationAlertEvent:
    """Event: High-priority escalation alert."""
    event_id: str
    session_id: int
    patient_id: int
    triage_level: str  # emergency, urgent_care
    disease: str
    reason: str
    alert_sent_to: List[str]
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self))


@dataclass
class AuditLogEvent:
    """Event: Audit log entry."""
    event_id: str
    event_type: str
    user_id: int
    session_id: Optional[int]
    action: str
    resource: str
    resource_id: Optional[int]
    metadata: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: str = ''

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps(asdict(self))


# Schema registry for validation
SCHEMA_REGISTRY = {
    'triage-requests': TriageRequestEvent,
    'inference-jobs': InferenceRequestEvent,
    'inference-responses': InferenceResponseEvent,
    'triage-completions': TriageCompletionEvent,
    'escalation-alerts': EscalationAlertEvent,
    'audit-logs': AuditLogEvent,
}
```

- [ ] **Step 2: Define topic constants**

```python
# backend/kafka/topics.py
"""
Kafka Topic Constants.

Centralized topic name definitions.
"""


class KafkaTopics:
    """Kafka topic names."""

    # Core triage flow
    TRIAGE_REQUESTS = 'triage-requests'
    INFERENCE_JOBS = 'inference-jobs'
    INFERENCE_RESPONSES = 'inference-responses'
    TRIAGE_COMPLETIONS = 'triage-completions'

    # Alerts and notifications
    ESCALATION_ALERTS = 'escalation-alerts'
    EMAIL_NOTIFICATIONS = 'email-notifications'

    # Audit and compliance
    AUDIT_LOGS = 'audit-logs'

    # Async processing
    ASYNC_EVENTS = 'async-events'


# Topic descriptions
TOPIC_DESCRIPTIONS = {
    KafkaTopics.TRIAGE_REQUESTS: 'User symptom submissions for triage',
    KafkaTopics.INFERENCE_JOBS: 'ML inference job requests',
    KafkaTopics.INFERENCE_RESPONSES: 'ML inference results',
    KafkaTopics.TRIAGE_COMPLETIONS: 'Completed triage sessions',
    KafkaTopics.ESCALATION_ALERTS: 'High-priority escalation alerts',
    KafkaTopics.EMAIL_NOTIFICATIONS: 'Email notification requests',
    KafkaTopics.AUDIT_LOGS: 'Audit trail for compliance',
    KafkaTopics.ASYNC_EVENTS: 'General async event processing',
}
```

- [ ] **Step 3: Commit**

```bash
git add backend/kafka/schemas.py backend/kafka/topics.py
git commit -m "feat(kafka): define message schemas and topic constants"
```

---

### Task 4: Kafka Producers

**Files:**
- Create: `backend/kafka/producers.py`

- [ ] **Step 1: Create Kafka producer wrapper**

```python
# backend/kafka/producers.py
"""
Kafka Producers for Health Triage.

Provides high-level producer methods for publishing events.
"""

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient
import json
import logging
from typing import Dict, Any, Optional
from django.conf import settings

from .kafka_config import KAFKA_PRODUCER_CONFIG, KAFKA_BOOTSTRAP_SERVERS
from .topics import KafkaTopics

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Kafka message producer with delivery callbacks."""

    def __init__(self):
        self.config = KAFKA_PRODUCER_CONFIG
        self.producer = None
        self._delivery_reports = []

    def connect(self):
        """Initialize Kafka producer."""
        try:
            self.producer = Producer(self.config)
            logger.info(f'Kafka producer connected to {KAFKA_BOOTSTRAP_SERVERS}')
        except Exception as e:
            logger.error(f'Failed to connect to Kafka: {e}')
            raise

    def _delivery_callback(self, err, msg):
        """Called when message is delivered or fails."""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
            self._delivery_reports.append({'success': False, 'error': str(err)})
        else:
            logger.debug(
                f'Message delivered to {msg.topic()} [{msg.partition()}] '
                f'at offset {msg.offset()}'
            )
            self._delivery_reports.append({
                'success': True,
                'topic': msg.topic(),
                'partition': msg.partition(),
                'offset': msg.offset()
            })

    def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Publish a message to a Kafka topic.

        Args:
            topic: Target Kafka topic
            message: Message payload (will be JSON encoded)
            key: Optional message key for partitioning
            headers: Optional message headers

        Returns:
            True if message was queued successfully
        """
        if not self.producer:
            self.connect()

        try:
            # Serialize message
            value = json.dumps(message).encode('utf-8')
            key_bytes = key.encode('utf-8') if key else None

            # Prepare headers
            kafka_headers = None
            if headers:
                kafka_headers = [(k, v.encode('utf-8')) for k, v in headers.items()]

            # Produce message
            self.producer.produce(
                topic=topic,
                value=value,
                key=key_bytes,
                headers=kafka_headers,
                on_delivery=self._delivery_callback
            )

            # Trigger delivery callbacks
            self.producer.poll(0)

            return True

        except Exception as e:
            logger.error(f'Failed to publish message to {topic}: {e}')
            return False

    def flush(self, timeout: int = 10):
        """Wait for all pending messages to be delivered."""
        if self.producer:
            remaining = self.producer.flush(timeout)
            if remaining > 0:
                logger.warning(f'{remaining} messages still pending delivery')
            return remaining
        return 0

    def close(self):
        """Close the producer connection."""
        if self.producer:
            self.flush()
            self.producer.close()
            self.producer = None


# Global producer instance
_kafka_producer = None


def get_producer() -> KafkaProducer:
    """Get or create the global Kafka producer."""
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = KafkaProducer()
        _kafka_producer.connect()
    return _kafka_producer


# High-level publishing functions

def publish_triage_request(event_data: Dict[str, Any]) -> bool:
    """Publish a triage request event."""
    producer = get_producer()
    return producer.publish(
        topic=KafkaTopics.TRIAGE_REQUESTS,
        message=event_data,
        key=str(event_data.get('session_id', ''))
    )


def publish_inference_request(event_data: Dict[str, Any]) -> bool:
    """Publish an inference job request."""
    producer = get_producer()
    return producer.publish(
        topic=KafkaTopics.INFERENCE_JOBS,
        message=event_data,
        key=str(event_data.get('session_id', '')),
        headers={'priority': event_data.get('priority', 'normal')}
    )


def publish_triage_completion(event_data: Dict[str, Any]) -> bool:
    """Publish a triage completion event."""
    producer = get_producer()
    return producer.publish(
        topic=KafkaTopics.TRIAGE_COMPLETIONS,
        message=event_data,
        key=str(event_data.get('patient_id', ''))
    )


def publish_escalation_alert(event_data: Dict[str, Any]) -> bool:
    """Publish an escalation alert."""
    producer = get_producer()
    return producer.publish(
        topic=KafkaTopics.ESCALATION_ALERTS,
        message=event_data,
        key=str(event_data.get('session_id', '')),
        headers={'alert_type': 'escalation'}
    )


def publish_audit_log(event_data: Dict[str, Any]) -> bool:
    """Publish an audit log entry."""
    producer = get_producer()
    return producer.publish(
        topic=KafkaTopics.AUDIT_LOGS,
        message=event_data,
        key=str(event_data.get('user_id', ''))
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/kafka/producers.py
git commit -m "feat(kafka): implement Kafka producers with delivery callbacks"
```

---

### Task 5: Kafka Consumers

**Files:**
- Create: `backend/kafka/consumers.py`

- [ ] **Step 1: Create Kafka consumer worker**

```python
# backend/kafka/consumers.py
"""
Kafka Consumers for Health Triage.

Provides consumer classes for processing events from Kafka topics.
"""

from confluent_kafka import Consumer, KafkaException, TopicPartition
from confluent_kafka.admin import AdminClient
import json
import logging
import signal
import threading
from typing import Callable, Dict, Any, Optional, List
from django.conf import settings

from .kafka_config import KAFKA_CONSUMER_CONFIG, KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPICS
from .topics import KafkaTopics

logger = logging.getLogger(__name__)


class KafkaConsumerWorker:
    """
    Background worker that consumes from Kafka topics.

    Runs in a separate thread and processes messages continuously.
    """

    def __init__(self, topics: List[str], group_id: str):
        self.topics = topics
        self.config = {
            **KAFKA_CONSUMER_CONFIG,
            'group.id': group_id,
        }
        self.consumer = None
        self.running = False
        self.thread = None
        self.message_handlers: Dict[str, Callable] = {}

    def connect(self):
        """Initialize Kafka consumer."""
        try:
            self.consumer = Consumer(self.config)
            self.consumer.subscribe(self.topics)
            logger.info(f'Kafka consumer subscribed to {self.topics}')
        except Exception as e:
            logger.error(f'Failed to connect to Kafka: {e}')
            raise

    def register_handler(self, topic: str, handler: Callable[[Dict[str, Any]], None]):
        """Register a message handler for a topic."""
        self.message_handlers[topic] = handler
        logger.info(f'Registered handler for topic: {topic}')

    def _process_message(self, msg):
        """Process a single Kafka message."""
        try:
            topic = msg.topic()
            value = msg.value().decode('utf-8')
            key = msg.key().decode('utf-8') if msg.key() else None
            data = json.loads(value)

            logger.debug(f'Received message from {topic}: {data}')

            # Call registered handler
            if topic in self.message_handlers:
                self.message_handlers[topic](data)
            else:
                logger.warning(f'No handler registered for topic: {topic}')

            # Commit offset after successful processing
            self.consumer.commit(asynchronous=False)

        except json.JSONDecodeError as e:
            logger.error(f'Failed to decode message: {e}')
        except Exception as e:
            logger.error(f'Error processing message: {e}')

    def _run_consumer(self):
        """Main consumer loop (runs in background thread)."""
        logger.info('Kafka consumer started')

        while self.running:
            try:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == 11:  # Partition EOF
                        continue
                    raise KafkaException(msg.error())

                self._process_message(msg)

            except KafkaException as e:
                logger.error(f'Kafka error: {e}')
            except Exception as e:
                logger.error(f'Consumer error: {e}')

        # Cleanup
        self.consumer.close()
        logger.info('Kafka consumer stopped')

    def start(self):
        """Start the consumer in a background thread."""
        if not self.consumer:
            self.connect()

        self.running = True
        self.thread = threading.Thread(target=self._run_consumer, daemon=True)
        self.thread.start()
        logger.info('Kafka consumer thread started')

    def stop(self):
        """Stop the consumer gracefully."""
        logger.info('Stopping Kafka consumer...')
        self.running = False

        if self.thread:
            self.thread.join(timeout=10)

        logger.info('Kafka consumer stopped')


class TriageRequestConsumer:
    """Consumer for triage request events."""

    def __init__(self):
        self.worker = KafkaConsumerWorker(
            topics=[KafkaTopics.TRIAGE_REQUESTS],
            group_id='triage-request-consumers'
        )
        self.worker.register_handler(KafkaTopics.TRIAGE_REQUESTS, self._handle_triage_request)

    def _handle_triage_request(self, event_data: Dict[str, Any]):
        """Handle incoming triage request."""
        from core.models import TriageSession

        logger.info(f'Processing triage request for session {event_data.get("session_id")}')

        try:
            # Update session status
            session_id = event_data.get('session_id')
            if session_id:
                session = TriageSession.objects.get(id=session_id)
                session.status = 'processing'
                session.save()
                logger.info(f'Updated session {session_id} status to processing')

        except Exception as e:
            logger.error(f'Error handling triage request: {e}')

    def start(self):
        self.worker.start()

    def stop(self):
        self.worker.stop()


class EscalationAlertConsumer:
    """Consumer for escalation alert events."""

    def __init__(self):
        self.worker = KafkaConsumerWorker(
            topics=[KafkaTopics.ESCALATION_ALERTS],
            group_id='escalation-alert-consumers'
        )
        self.worker.register_handler(KafkaTopics.ESCALATION_ALERTS, self._handle_escalation)

    def _handle_escalation(self, event_data: Dict[str, Any]):
        """Handle escalation alert - send notifications."""
        from core.models import TriageSession

        logger.warning(
            f'ESCALATION ALERT: Session {event_data.get("session_id")} '
            f'- Level: {event_data.get("triage_level")}'
        )

        try:
            # In production, send email/SMS/notification
            session_id = event_data.get('session_id')
            if session_id:
                session = TriageSession.objects.get(id=session_id)
                session.status = 'escalated'
                session.save()
                logger.info(f'Marked session {session_id} as escalated')

                # TODO: Send email to medical team
                # send_escalation_email.delay(session_id)

        except Exception as e:
            logger.error(f'Error handling escalation alert: {e}')

    def start(self):
        self.worker.start()

    def stop(self):
        self.worker.stop()


class AuditLogConsumer:
    """Consumer for audit log events."""

    def __init__(self):
        self.worker = KafkaConsumerWorker(
            topics=[KafkaTopics.AUDIT_LOGS],
            group_id='audit-log-consumers'
        )
        self.worker.register_handler(KafkaTopics.AUDIT_LOGS, self._handle_audit_log)

    def _handle_audit_log(self, event_data: Dict[str, Any]):
        """Handle audit log entry - persist to database."""
        logger.debug(f'Processing audit log: {event_data.get("action")}')

        # In production, persist to audit_logs table or external system
        # For now, just log
        logger.info(
            f'AUDIT: {event_data.get("action")} by user {event_data.get("user_id")} '
            f'on {event_data.get("resource")}'
        )

    def start(self):
        self.worker.start()

    def stop(self):
        self.worker.stop()


# Global consumer instances
_consumers = []


def start_all_consumers():
    """Start all Kafka consumers."""
    global _consumers

    consumers = [
        TriageRequestConsumer(),
        EscalationAlertConsumer(),
        AuditLogConsumer(),
    ]

    for consumer in consumers:
        consumer.start()
        _consumers.append(consumer)

    logger.info(f'Started {len(consumers)} Kafka consumers')


def stop_all_consumers():
    """Stop all Kafka consumers gracefully."""
    global _consumers

    for consumer in _consumers:
        consumer.stop()

    _consumers = []
    logger.info('All Kafka consumers stopped')
```

- [ ] **Step 2: Commit**

```bash
git add backend/kafka/consumers.py
git commit -m "feat(kafka): implement Kafka consumers with background workers"
```

---

### Task 6: Integration with Existing Code

**Files:**
- Modify: `backend/agent/consumers.py`
- Modify: `backend/api/views.py`
- Modify: `backend/backend/__init__.py`

- [ ] **Step 1: Update WebSocket consumer to publish events**

Read `backend/agent/consumers.py`, then add after imports:

```python
from kafka.producers import publish_triage_request, publish_triage_completion, publish_escalation_alert
```

Add in `receive` method after getting session:

```python
# Publish triage request event to Kafka
publish_triage_request({
    'event_id': f'triage_{session_id}_{timezone.now().isoformat()}',
    'session_id': session.id,
    'patient_id': session.patient.id,
    'user_id': session.patient.user.id,
    'symptoms': session.primary_symptoms,
    'notes': session.notes,
    'timestamp': timezone.now().isoformat(),
})
```

- [ ] **Step 2: Update Django app lifecycle**

Modify `backend/backend/__init__.py`:

```python
"""
Health Triage Assistant - Django Application
"""

# Default_app_config removed (Django 3.2+ auto-detects)

# Kafka consumers lifecycle
_kafka_consumers_started = False


def start_kafka_consumers():
    """Start Kafka consumers on application startup."""
    global _kafka_consumers_started

    if not _kafka_consumers_started:
        try:
            from kafka.consumers import start_all_consumers
            start_all_consumers()
            _kafka_consumers_started = True
        except Exception as e:
            print(f'Warning: Failed to start Kafka consumers: {e}')


def stop_kafka_consumers():
    """Stop Kafka consumers on application shutdown."""
    try:
        from kafka.consumers import stop_all_consumers
        stop_all_consumers()
    except Exception as e:
        print(f'Warning: Error stopping Kafka consumers: {e}')
```

- [ ] **Step 3: Commit**

```bash
git add backend/agent/consumers.py backend/backend/__init__.py
git commit -m "feat(kafka): integrate Kafka events with existing WebSocket flow"
```

---

### Task 7: Testing & Verification

**Files:**
- Create: `backend/kafka/tests.py`
- Create: `scripts/test_kafka.py`

- [ ] **Step 1: Create Kafka test script**

```python
#!/usr/bin/env python
# scripts/test_kafka.py
"""Test Kafka integration."""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from kafka.producers import (
    publish_triage_request,
    publish_inference_request,
    publish_triage_completion,
    publish_escalation_alert,
    get_producer
)
from kafka.topics import KafkaTopics


def test_producer():
    """Test Kafka producer."""
    print('\n=== Testing Kafka Producer ===')

    # Test triage request event
    result = publish_triage_request({
        'event_id': 'test-001',
        'session_id': 1,
        'patient_id': 1,
        'user_id': 1,
        'symptoms': ['fever', 'headache'],
        'notes': 'Test symptoms',
        'timestamp': '2026-03-29T10:00:00Z',
    })
    print(f'Publish triage request: {result}')

    # Test inference request
    result = publish_inference_request({
        'event_id': 'test-002',
        'request_id': 'req-001',
        'session_id': 1,
        'symptoms': ['fever', 'headache'],
        'priority': 'normal',
    })
    print(f'Publish inference request: {result}')

    # Test escalation alert
    result = publish_escalation_alert({
        'event_id': 'test-003',
        'session_id': 1,
        'patient_id': 1,
        'triage_level': 'emergency',
        'disease': 'Stroke',
        'reason': 'Emergency keywords detected',
        'alert_sent_to': ['admin@example.com'],
    })
    print(f'Publish escalation alert: {result}')

    # Flush pending messages
    producer = get_producer()
    remaining = producer.flush()
    print(f'Pending messages after flush: {remaining}')


def verify_topics():
    """Verify Kafka topics exist."""
    from confluent_kafka.admin import AdminClient

    print('\n=== Verifying Kafka Topics ===')

    admin_client = AdminClient({
        'bootstrap.servers': 'localhost:9092'
    })

    topics = admin_client.list_topics(timeout=10)

    print(f'Available topics: {list(topics.topics.keys())}')

    expected_topics = [
        KafkaTopics.TRIAGE_REQUESTS,
        KafkaTopics.INFERENCE_JOBS,
        KafkaTopics.ESCALATION_ALERTS,
        KafkaTopics.AUDIT_LOGS,
    ]

    for topic in expected_topics:
        exists = topic in topics.topics
        print(f'  {topic}: {"✓" if exists else "✗"}')


if __name__ == '__main__':
    print('Kafka Integration Tests')
    print('=' * 50)

    verify_topics()
    test_producer()

    print('\n' + '=' * 50)
    print('Tests complete!')
```

- [ ] **Step 2: Run tests**

```bash
# Start Kafka
cd docker
docker-compose up -d kafka zookeeper schema-registry

# Wait for Kafka to be ready
sleep 10

# Run test script
cd ..
python scripts/test_kafka.py
```

Expected: All topics exist, messages published successfully

- [ ] **Step 3: Verify in Kafka UI**

Open browser: `http://localhost:8090`

Check:
- Topics are listed
- Messages appear in topic browser
- Consumer groups are created

- [ ] **Step 4: Commit**

```bash
git add backend/kafka/tests.py scripts/test_kafka.py
git commit -m "test(kafka): add Kafka integration tests"
```

---

## Success Criteria

- [ ] Kafka, Zookeeper, Schema Registry start without errors
- [ ] Kafka UI accessible at `localhost:8090`
- [ ] All 6 topics created automatically
- [ ] Producer can publish messages to all topics
- [ ] Consumers receive and process messages
- [ ] Messages visible in Kafka UI
- [ ] Test script passes
- [ ] Existing triage flow publishes events

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Kafka won't start | Check Zookeeper is healthy first |
| Connection refused | Verify advertised listeners in docker-compose |
| Topic not found | Enable auto-create or run `create_topics()` |
| Messages not consumed | Check consumer group ID, offset reset policy |
