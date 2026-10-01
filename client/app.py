import hashlib
import hmac
import json
import os
from urllib.parse import urlsplit

import requests
import streamlit as st

DEFAULT_URL = os.environ.get("WEBHOOK_URL", "http://webhook-server.railway.internal:3000/webhook/test")
TIMEOUT_SECONDS = 10
MAX_RESPONSE_BYTES = 1_000_000

st.set_page_config(page_title="Webhook Client", page_icon="🪝")
st.subheader("Webhook Client")
st.caption("Send signed or unsigned HTTP POST requests to any webhook endpoint.")

with st.form("webhook_form"):
    url = st.text_input(
        "Webhook URL",
        value=DEFAULT_URL,
        help="The full URL of the webhook endpoint to send the request to.",
    )
    event_type = st.text_input(
        "Event Type",
        value="user.created",
        help="Sent as the X-Event-Type header. Useful for routing events on the server.",
    )
    secret = st.text_input(
        "Webhook Secret (optional)",
        type="password",
        help="If provided, the payload will be signed with HMAC-SHA256 and sent as X-Webhook-Signature.",
    )
    payload = st.text_area(
        "JSON Payload",
        value='{\n  "id": 1,\n  "name": "Alice"\n}',
        height=200,
        help="Must be valid JSON.",
    )
    submitted = st.form_submit_button("Submit")


def read_limited(response):
    """Read at most MAX_RESPONSE_BYTES of the body; return (text, truncated)."""
    body = response.raw.read(MAX_RESPONSE_BYTES + 1, decode_content=True)
    truncated = len(body) > MAX_RESPONSE_BYTES
    text = body[:MAX_RESPONSE_BYTES].decode(response.encoding or "utf-8", errors="replace")
    return text, truncated


if submitted:
    url = url.strip()
    if urlsplit(url).scheme not in ("http", "https") or not urlsplit(url).netloc:
        st.error("Please provide a valid http(s) Webhook URL.")
        st.stop()

    try:
        parsed_payload = json.loads(payload)
    except json.JSONDecodeError:
        st.error("Invalid JSON payload. Please check your input.")
        st.stop()

    # Sign and send the exact same bytes. Compact separators match JavaScript's JSON.stringify.
    body = json.dumps(parsed_payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if event_type.strip():
        headers["X-Event-Type"] = event_type.strip()
    if secret.strip():
        sig = hmac.new(secret.strip().encode("utf-8"), body, hashlib.sha256).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={sig}"

    try:
        with requests.post(
            url, data=body, headers=headers, timeout=TIMEOUT_SECONDS, allow_redirects=False, stream=True
        ) as response:
            text, truncated = read_limited(response)
            status = f"Response: {response.status_code} {response.reason}"
            location = response.headers.get("Location")
            content_type = response.headers.get("Content-Type", "")
    except requests.exceptions.Timeout:
        st.error(f"Request timed out after {TIMEOUT_SECONDS} seconds.")
        st.stop()
    except requests.exceptions.ConnectionError:
        st.error("Connection failed. Check the Webhook URL and ensure the server is running.")
        st.stop()
    except (requests.exceptions.RequestException, ValueError) as e:
        st.error(f"Request failed: {e}")
        st.stop()

    if 200 <= response.status_code < 300:
        st.success(status)
    else:
        st.warning(status)
    if location:
        st.info(f"Redirect to {location} was not followed.")

    st.markdown("**Request**")
    with st.expander("Headers sent", expanded=True):
        st.json(headers)
    with st.expander("Payload sent", expanded=True):
        st.json(parsed_payload)

    st.markdown("**Response**")
    with st.expander("Response body", expanded=True):
        try:
            if "json" not in content_type or truncated:
                raise ValueError
            st.json(json.loads(text))
        except ValueError:
            st.text(text or "(empty)")
        if truncated:
            st.caption(f"Response truncated to {MAX_RESPONSE_BYTES:,} bytes.")
