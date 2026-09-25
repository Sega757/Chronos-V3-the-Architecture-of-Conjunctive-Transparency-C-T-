.PHONY: proto proto-clean test up down

PROTO_DIR := proto
GEN_DIR := libs/chronos_common/generated

# Regenerate the Python gRPC stubs from proto/*.proto into
# libs/chronos_common/generated. Requires: pip install grpcio-tools
# (or `pip install -e libs/chronos_common[codegen]`).
proto:
	mkdir -p $(GEN_DIR)
	python -m grpc_tools.protoc \
		-I$(PROTO_DIR) \
		--python_out=$(GEN_DIR) \
		--grpc_python_out=$(GEN_DIR) \
		$(PROTO_DIR)/common.proto \
		$(PROTO_DIR)/system1_hypothesis.proto \
		$(PROTO_DIR)/system2_verifier.proto \
		$(PROTO_DIR)/arbiter.proto
	touch $(GEN_DIR)/__init__.py

proto-clean:
	find $(GEN_DIR) -name '*_pb2*.py' -delete

# Run each service's unit tests. Tests that exercise generator.py /
# server.py logic directly (not the gRPC transport) do not require
# `make proto` to have been run first.
test:
	cd services/system1_hypothesis_generator && python -m pytest tests -v
	cd services/system2_chronos_verifier && python -m pytest tests -v
	cd services/arbiter_module && python -m pytest tests -v

up:
	docker compose up --build

down:
	docker compose down -v
