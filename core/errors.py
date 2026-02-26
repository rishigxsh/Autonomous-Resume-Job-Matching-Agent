"""Centralised error helpers for the Resume–Job Matching Agent.

All HTTP error responses produced by this application use the helpers below
so that error shape and wording stay consistent across every module.
"""

from fastapi import HTTPException


def internal_error(reason: str) -> HTTPException:
    """Return a 500 HTTPException with a clean, prefixed message.

    Args:
        reason: A concise explanation of what went wrong.

    Returns:
        An ``HTTPException`` ready to be raised by the caller.

    Example::

        raise internal_error("Example file not found: examples/resume_example.json")
    """
    return HTTPException(
        status_code=500,
        detail=f"Internal server error: {reason}",
    )
