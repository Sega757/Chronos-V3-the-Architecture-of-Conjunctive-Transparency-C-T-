"""Errors raised within System 1. All are caught at the gRPC boundary in
server.py and translated into an appropriate grpc.StatusCode -- nothing
here should ever propagate as a bare, unhandled exception across the RPC
boundary.
"""


class System1Error(Exception):
    """Base class for all System 1 errors."""


class InvalidRequestError(System1Error):
    """The request violated a documented precondition (e.g. max_candidates
    out of range, empty query, invalid temperature)."""


class GenerationBackendError(System1Error):
    """The underlying hypothesis-generation backend failed or timed out."""


class SigningError(System1Error):
    """The node's signing key is unavailable or a signing operation
    failed. Treated as fatal for the request -- an unsigned candidate MUST
    never leave System 1."""
