from __future__ import annotations

import ssl
from pathlib import Path


def create_ssl_context() -> ssl.SSLContext:
    paths = ssl.get_default_verify_paths()
    candidates = (
        paths.cafile,
        paths.openssl_cafile,
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
    )
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return ssl.create_default_context(cafile=candidate)
    return ssl.create_default_context()
