# TECHNICAL ARCHITECTURE SPECIFICATION - PROJECT AURORA

## 1. Cloud Infrastructure Architecture
The cloud architecture utilizes a dual-region active-passive setup across AWS us-east-1 and us-west-2. Traffic is routed via Route53 Latency-based Routing policies.

### Component Breakdown:
* **API Gateway**: Handles CORS validation, throttle limitations, and rate-limiting at 10,000 requests per minute per API token.
* **Auto-Scaling Compute (EKS)**: Runs Dockerized microservices on AWS Fargate. Minimum cluster size is 3 nodes, max 24 nodes.
* **Database Layer (Aurora Postgres Global Database)**: Uses physical replication. Primary write cluster is in us-east-1; read-only replica resides in us-west-2.

## 2. API Schema Definitions
The microservices interact via REST interfaces:
* `GET /api/v1/inventory/{sku_id}` - Returns current stock levels. Latency target: <50ms.
* `POST /api/v1/inventory/update` - Adjusts warehouse inventory values. Requires `WriteInventory` JWT scope permissions.

## 3. Disaster Recovery Plan
* **RTO (Recovery Time Objective)**: Under 5 minutes.
* **RPO (Recovery Point Objective)**: Under 10 seconds.
* Failover is triggered automatically via CloudWatch alarms monitoring database health checks.
