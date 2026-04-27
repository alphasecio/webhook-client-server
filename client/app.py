import hmac
import hashlib
import json
import requests
import streamlit as st

st.set_page_config(page_title="Webhook Client", page_icon="🪝")
st.subheader("Webhook Client")
st.caption("Send signed or unsigned HTTP POST requests to any webhook endpoint.")

with st.form("webhook_form"):
    url = st.text_input(
        "Webhook URL",
        value="http://webhook-server.railway.internal/webhook/test",
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

if submitted:
    if not url.strip():
        st.error("Please provide a Webhook URL.")
    else:
        try:
            parsed_payload = json.loads(payload)
        except json.JSONDecodeError:
            st.error("Invalid JSON payload. Please check your input.")
            st.stop()

        headers = {"Content-Type": "application/json"}

        if event_type.strip():
            headers["X-Event-Type"] = event_type.strip()

        if secret.strip():
            body = json.dumps(parsed_payload)
            sig = hmac.new(
                secret.strip().encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={sig}"

        try:
            response = requests.post(url, json=parsed_payload, headers=headers, timeout=10)
            st.success(f"Response: {response.status_code} {response.reason}")

            st.markdown("**Request**")
            with st.expander("Headers sent", expanded=True):
                st.json(dict(headers))
            with st.expander("Payload sent", expanded=True):
                st.json(parsed_payload)

            st.markdown("**Response**")
            content_type = response.headers.get("Content-Type", "")
            with st.expander("Response body", expanded=True):
                if "application/json" in content_type:
                    st.json(response.json())
                else:
                    st.text(response.text)

        except requests.exceptions.ConnectionError:
            st.error("Connection failed. Check the Webhook URL and ensure the server is running.")
        except requests.exceptions.Timeout:
            st.error("Request timed out after 10 seconds.")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
