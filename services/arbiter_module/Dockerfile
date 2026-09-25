FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY libs/chronos_common /app/libs/chronos_common
COPY proto /app/proto
COPY services/arbiter_module/requirements.txt /app/services/arbiter_module/requirements.txt

RUN pip install --no-cache-dir -r /app/services/arbiter_module/requirements.txt \
    && pip install --no-cache-dir grpcio-tools

RUN python -m grpc_tools.protoc \
        -I/app/proto \
        --python_out=/app/libs/chronos_common/generated \
        --grpc_python_out=/app/libs/chronos_common/generated \
        /app/proto/common.proto /app/proto/system1_hypothesis.proto \
        /app/proto/system2_verifier.proto /app/proto/arbiter.proto \
    && touch /app/libs/chronos_common/generated/__init__.py

COPY services/arbiter_module/src /app/services/arbiter_module/src

ENV PYTHONPATH="/app/libs/chronos_common:/app/libs/chronos_common/generated:/app/services/arbiter_module"
ENV GRPC_PORT=50053
EXPOSE 50053

WORKDIR /app/services/arbiter_module
CMD ["python", "-m", "src.server"]
