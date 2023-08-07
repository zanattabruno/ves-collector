# O1 VNF Event Streaming (VES) Collector
Virtual Event Streaming (VES) Collector (formerly known as Standard Event Collector/Common Event Collector) is RESTful collector for processing JSON messages into Kafka. The collector supports individual events or eventbatch posted to collector end-point(s) and post them to interface/bus for other application to subscribe. The collector verifies the source (when authentication is enabled) and validates the events against VES schema before distributing to Kafka topics for downstream system to subscribe. The VESCollector also supports configurable event transformation function and event distribution to Kafka topics.

## VES Schema Validation

VES Collector is configured to support the versions of VES listed below. The corresponding API uses the VES schema definition for event validation.

| VES Version | API version      | Schema Definition                          |
|-------------|------------------|--------------------------------------------|
| VES 1.2     | eventListener/v1 | CommonEventFormat_Vendors_v25.json         |
| VES 4.1     | eventListener/v4 | CommonEventFormat_27.2.json                |
| VES 5.4     | eventListener/v5 | CommonEventFormat_28.4.1.json              |
| VES 7.2.1   | eventListener/v7 | CommonEventFormat_30.2.1_ONAP.json         |


## Features Supported
- VES collector deployed as docker containers

- Acknowledgement to sender with appropriate response code (both successful and failure)

- Support single or batch JSON events input

- General schema validation (against standard VES definition)

- Publish events into Dmaap Topic (with/without AAF)

- The collector can receive events via standard HTTP port (9999)

## VES Collector Helm Installation

### values.yaml
```yaml
# Number of replicas for the deployment
replicaCount: 1

# Namespace where the deployment will be created
namespace: smo

# Docker image configuration
image:
  repository: zanattabruno/ves-collector
  pullPolicy: Always
  tag: latest

# Service configuration
service:
  type: ClusterIP
  port: 9999

# Server configuration
server:
  host: "0.0.0.0"
  port: 9999
  debug: true

# VES configuration
ves:
  api_version: "v5"

# Kafka configuration
kafka:
  host: "kafka.smo.svc.cluster.local"
  port: 9092
  default_topic: "ves"

# Logging configuration
logging:
  level: INFO
```
### Deploying the chart
```bash
cd ves-collector
helm install ves-collector helm/ves-collector -f values.yaml
```