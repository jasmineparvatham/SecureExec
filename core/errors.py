"""
Custom error types for Sandbox VM and Verifier
"""


class VMError(Exception):
    """
    Raised when the Virtual Machine encounters a runtime error.
    """
    pass


class VerificationError(Exception):
    """
    Raised when static verification fails.
    """
    pass
