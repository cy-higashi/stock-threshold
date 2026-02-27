FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /stub
COPY stub.sh start.sh ./
RUN chmod +x stub.sh start.sh

EXPOSE 8080

ENTRYPOINT ["/stub/start.sh"]
