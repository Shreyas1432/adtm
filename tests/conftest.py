import base64
import os

# Dev-only key material for tests (prod uses the client KMS/HSM — ADR-0007).
os.environ.setdefault("ADTM_KEK_DEV", base64.b64encode(os.urandom(32)).decode())
os.environ.setdefault("ADTM_BLIND_INDEX_KEY_DEV", base64.b64encode(os.urandom(32)).decode())
