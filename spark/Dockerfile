FROM apache/spark:3.5.1

USER root
WORKDIR /opt/spark/work-dir

COPY spark /opt/spark/work-dir/spark

RUN mkdir -p /opt/spark/work-dir/data/bronze /home/spark/.ivy2/cache /home/spark/.ivy2/jars \
    && chown -R spark:spark /opt/spark/work-dir /home/spark/.ivy2

USER spark

ENV PYTHONPATH=/opt/spark/work-dir

ENTRYPOINT ["/opt/spark/bin/spark-submit"]
