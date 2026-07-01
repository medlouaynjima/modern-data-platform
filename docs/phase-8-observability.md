# Phase 8: Observability Layer

## Overview

Phase 8 introduces a comprehensive observability stack to monitor the health, throughput, and performance of the Modern Data Platform. We use **Prometheus** for metrics collection and **Grafana** for visualization. 

## Architecture

The observability layer is composed of:
1. **JMX Exporter**: A Java agent injected into the `mdp-kafka` container. It exposes Kafka's internal JMX metrics as a Prometheus-compatible HTTP endpoint on port 8080.
2. **Prometheus**: Scrapes the metrics from the JMX Exporter every 15 seconds and stores them as time-series data.
3. **Grafana**: Connects to Prometheus as a data source and renders the metrics in interactive dashboards.

## Implementation Details

- **Kafka Custom Image**: We created a custom Dockerfile (`kafka/Dockerfile`) based on `apache/kafka:3.7.0` that downloads the `jmx_prometheus_javaagent.jar` and injects it into the Kafka JVM using the `KAFKA_OPTS` environment variable.
- **Prometheus Config**: The `prometheus.yml` is configured to scrape the `kafka:8080` target.
- **Grafana Provisioning**: Grafana is fully auto-provisioned using configuration files in `monitoring/grafana/provisioning`. It automatically loads the Prometheus data source and the predefined Dashboards without any manual UI setup.
- **Pipeline Health Dashboard**: We built a custom JSON dashboard (`pipeline_health.json`) that visualizes key metrics like:
  - **Kafka Messages In (Per Sec)**: Tracks the throughput of the synthetic producers.
  - **Bytes In/Out**: Monitors the network payload.
  - **Active Controllers & Partitions**: Ensures the cluster state is healthy.

## Usage

To spin up the observability layer:
```bash
docker compose --profile monitoring up -d
```

- **Prometheus**: Accessible at [http://localhost:9090](http://localhost:9090).
- **Grafana**: Accessible at [http://localhost:3000](http://localhost:3000) (Login: `admin` / `admin`).

Once running, trigger the Airflow pipeline to see real-time metrics populate in the Pipeline Health dashboard as the producers stream events into Kafka.
