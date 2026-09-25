"""Errors raised within System 0 (the Meta-Arbiter). All are caught at the
gRPC boundary in server.py and translated into a grpc.StatusCode.
"""


class ArbiterError(Exception):
    """Base class for all Meta-Arbiter errors."""


class InvalidRequestError(ArbiterError):
    """The request violated a documented precondition."""


class UnknownRoundError(ArbiterError):
    """A SubmitSample referenced a round_id that Escalate never opened."""


class DuplicateSampleError(ArbiterError):
    """The same arbiter_node_id submitted more than one sample for a round."""


class SigningError(ArbiterError):
    """The arbiter's signing key is unavailable or signing failed."""
