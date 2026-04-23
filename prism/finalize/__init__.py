from __future__ import annotations

__all__ = ["build_release", "verify_release"]


def build_release(*args, **kwargs):
    from prism.finalize.build_release import build_release as _build_release

    return _build_release(*args, **kwargs)


def verify_release(*args, **kwargs):
    from prism.finalize.verify_release import verify_release as _verify_release

    return _verify_release(*args, **kwargs)
