FROM apache/spark:3.5.1

USER root
WORKDIR /opt/spark/work-dir

COPY spark /opt/spark/work-dir/spark

ADD https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.2.0/delta-spark_2.12-3.2.0.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/io/delta/delta-storage/3.2.0/delta-storage-3.2.0.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/antlr/antlr4-runtime/4.9.3/antlr4-runtime-4.9.3.jar /opt/spark/jars/

RUN chmod 644 /opt/spark/jars/delta-spark_2.12-3.2.0.jar /opt/spark/jars/delta-storage-3.2.0.jar /opt/spark/jars/antlr4-runtime-4.9.3.jar \
    && mkdir -p /opt/spark/work-dir/data/bronze /opt/spark/work-dir/data/silver /home/spark/.ivy2/cache /home/spark/.ivy2/jars \
    && chown -R spark:spark /opt/spark/work-dir /home/spark/.ivy2

USER spark

ENV PYTHONPATH=/opt/spark/work-dir

ENTRYPOINT ["/opt/spark/bin/spark-submit"]
