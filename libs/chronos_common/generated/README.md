# Generated gRPC stubs

This directory is intentionally empty in version control. Run:

```sh
make proto
```

from the repository root to generate the `*_pb2.py` / `*_pb2_grpc.py`
(Python) stubs from `proto/*.proto` into this directory via
`grpcio-tools`.

Generated code is not committed so that the `.proto` files in `proto/`
remain the single source of truth for the wire contract.

## Import style

`protoc`'s Python plugin emits **flat, non-package-relative** imports
between generated files (e.g. `system2_verifier_pb2_grpc.py` does
`import common_pb2`, not `from . import common_pb2`). Because of that,
this directory is added to `PYTHONPATH` **directly** (not imported as a
dotted subpackage of `chronos_common`) by every service's Dockerfile and
by `make test`. Service code imports the stubs as flat top-level modules:

```python
import common_pb2
import system2_verifier_pb2, system2_verifier_pb2_grpc
```

not `from chronos_common.generated import ...`.
