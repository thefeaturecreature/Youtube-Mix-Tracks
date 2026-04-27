"""ACRCloud audio fingerprinting — fallback only."""

import base64
import hashlib
import hmac
import os
import time

import requests

HOST = os.environ["ACRCLOUD_HOST"]
ACCESS_KEY = os.environ["ACRCLOUD_ACCESS_KEY"]
ACCESS_SECRET = os.environ["ACRCLOUD_ACCESS_SECRET"]


def _sign(string_to_sign: str, secret: str) -> str:
    return base64.b64encode(
        hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha1).digest()
    ).decode()


def identify_chunk(audio_bytes: bytes, timestamp_sec: int) -> dict:
    ts = str(int(time.time()))
    string_to_sign = "\n".join(["POST", "/v1/identify", ACCESS_KEY, "audio", "1", ts])
    signature = _sign(string_to_sign, ACCESS_SECRET)
    files = {"sample": ("chunk.mp3", audio_bytes, "audio/mpeg")}
    data = {
        "access_key": ACCESS_KEY,
        "sample_bytes": len(audio_bytes),
        "timestamp": ts,
        "signature": signature,
        "data_type": "audio",
        "signature_version": "1",
    }
    resp = requests.post(f"https://{HOST}/v1/identify", files=files, data=data, timeout=20)
    resp.raise_for_status()
    result = resp.json()
    result["_offset_sec"] = timestamp_sec
    return result
