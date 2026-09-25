FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY libs/chronos_common /app/libs/chronos_common
COPY proto /app/proto
COPY services/system2_chronos_verifier/requirements.txt /app/services/system2_chronos_verifier/requirements.txt

RUN pip install --no-cache-dir -r /app/services/system2_chronos_verifier/requirements.txt \
    && pip install --no-cache-dir grpcio-tools

RUN python -m grpc_tools.protoc \
        -I/app/proto \
        --python_out=/app/libs/chronos_common/generated \
        --grpc_python_out=/app/libs/chronos_common/generated \
        /app/proto/common.proto /app/proto/system1_hypothesis.proto /app/proto/system2_verifier.proto \
    && touch /app/libs/chronos_common/generated/__init__.py

COPY services/system2_chronos_verifier/src /app/services/system2_chronos_verifier/src

ENV PYTHONPATH="/app/libs/chronos_common:/app/libs/chronos_common/generated:/app/services/system2_chronos_verifier"
ENV GRPC_PORT=50052
EXPOSE 50052

WORKDIR /app/services/system2_chronos_verifier
CMD ["python", "-m", "src.server"]
