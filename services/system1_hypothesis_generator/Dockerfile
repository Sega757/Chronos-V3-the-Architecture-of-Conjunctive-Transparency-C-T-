FROM python:3.12-slim AS base

WORKDIR /app

# System dependencies for cryptography's build (skipped on manylinux wheels,
# kept for arches that fall back to source builds).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY libs/chronos_common /app/libs/chronos_common
COPY proto /app/proto
COPY services/system1_hypothesis_generator/requirements.txt /app/services/system1_hypothesis_generator/requirements.txt

RUN pip install --no-cache-dir -r /app/services/system1_hypothesis_generator/requirements.txt \
    && pip install --no-cache-dir grpcio-tools

# Generate the gRPC stubs into the shared library at image build time.
RUN python -m grpc_tools.protoc \
        -I/app/proto \
        --python_out=/app/libs/chronos_common/generated \
        --grpc_python_out=/app/libs/chronos_common/generated \
        /app/proto/common.proto /app/proto/system1_hypothesis.proto \
    && touch /app/libs/chronos_common/generated/__init__.py

COPY services/system1_hypothesis_generator/src /app/services/system1_hypothesis_generator/src

ENV PYTHONPATH="/app/libs/chronos_common:/app/libs/chronos_common/generated:/app/services/system1_hypothesis_generator"
ENV GRPC_PORT=50051
EXPOSE 50051

WORKDIR /app/services/system1_hypothesis_generator
CMD ["python", "-m", "src.server"]
