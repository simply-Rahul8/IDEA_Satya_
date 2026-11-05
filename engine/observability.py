"""Sentry wiring (free tier). No-op unless SENTRY_DSN is set; scrubs listing text. Owner: Platform."""

import os


def init_sentry() -> bool:
    dsn = os.environ.get("SENTRY_DSN", "")
    if not dsn:
        return False
    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SATYA_ENV", "local"),
        traces_sample_rate=0.1,
        send_default_pii=False,  # DPDP: no user PII or request bodies (listing text) to a third party
        max_request_body_size="never",
    )
    return True
