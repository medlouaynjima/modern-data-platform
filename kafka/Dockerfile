FROM apache/kafka:3.7.0

USER root

# Download Prometheus JMX Exporter
ADD https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.20.0/jmx_prometheus_javaagent-0.20.0.jar /opt/kafka/jmx_prometheus_javaagent.jar
RUN chmod 644 /opt/kafka/jmx_prometheus_javaagent.jar

# Add config file
COPY kafka/jmx-exporter.yml /opt/kafka/jmx-exporter.yml
RUN chown appuser:appuser /opt/kafka/jmx-exporter.yml /opt/kafka/jmx_prometheus_javaagent.jar

USER appuser

# Add javaagent to KAFKA_OPTS so it is picked up by the startup script
ENV KAFKA_OPTS="-javaagent:/opt/kafka/jmx_prometheus_javaagent.jar=8080:/opt/kafka/jmx-exporter.yml"
