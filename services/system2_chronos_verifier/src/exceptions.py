"""Errors raised within System 2. All are caught at the gRPC boundary in
server.py and translated into a grpc.StatusCode. None of these should ever
be swallowed silently -- a failure here must never be interpreted as a
GROUNDED verdict by omission.
"""


class System2Error(Exception):
    """Base class for all System 2 errors."""


class InvalidRequestError(System2Error):
    """The VerificationRequest violated a documented precondition."""


class GroundTruthUnavailableError(System2Error):
    """One or more ground_truth_refs could not be resolved. Per the
    zero-hallucination lock, this MUST result in REJECTED or ESCALATED --
    never GROUNDED."""


class SigningError(System2Error):
    """The verifier's signing key is unavailable or signing failed. A
    VerificationResult MUST NOT be returned unsigned."""
