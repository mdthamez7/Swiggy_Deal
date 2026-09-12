import base64
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

import certifi
import httpx
import keyring
from dotenv import load_dotenv

load_dotenv()

BASE = "https://mcp.swiggy.com"
REGISTER_URL = f"{BASE}/auth/register"
AUTHORIZE_URL = f"{BASE}/auth/authorize"
TOKEN_URL = f"{BASE}/auth/token"

CALLBACK_HOST = os.getenv("CALLBACK_HOST", "127.0.0.1")
CALLBACK_PORT = int(os.getenv("CALLBACK_PORT", "3030"))
REDIRECT_URI = f"http://{CALLBACK_HOST}:{CALLBACK_PORT}/callback"

KEYRING_SERVICE = "LootDeal-Swiggy-MCP"
KEYRING_USERNAME = "swiggy-access-token"
META_FILE = Path("data/oauth_session.json")

_received = {}
_event = threading.Event()


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def make_pkce():
    verifier = b64url(secrets.token_bytes(32))
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        qs = urllib.parse.parse_qs(parsed.query)
        _received["code"] = qs.get("code", [None])[0]
        _received["state"] = qs.get("state", [None])[0]
        _received["error"] = qs.get("error", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h2>Swiggy authorization received.</h2>"
            b"<p>You can close this tab.</p></body></html>"
        )
        _event.set()

    def log_message(self, *_):
        return


def register_client(client):
    payload = {
        "client_name": "LootDeal Swiggy Instamart Scanner",
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
    }
    r = client.post(f"{BASE}/auth/register", json=payload)
    r.raise_for_status()
    data = r.json()
    client_id = data.get("client_id")
    if not client_id:
        raise RuntimeError(f"OAuth registration returned no client_id: {data}")
    return client_id


def main():
    Path("data").mkdir(exist_ok=True)
    _received.clear()
    _event.clear()

    print("=" * 72)
    print("LOOTDEAL - SWIGGY OAUTH LOGIN")
    print("=" * 72)
    print(f"Callback: {REDIRECT_URI}")

    with httpx.Client(
        timeout=30,
        verify=certifi.where(),
        follow_redirects=False,
    ) as client:
        print("Registering OAuth client...")
        client_id = register_client(client)

        verifier, challenge = make_pkce()
        state = secrets.token_urlsafe(24)

        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "scope": "mcp:tools",
        }
        url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)

        server = http.server.ThreadingHTTPServer(
            (CALLBACK_HOST, CALLBACK_PORT), CallbackHandler
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        print("Opening Swiggy authorization in your browser...")
        webbrowser.open(url)
        print("Complete the Swiggy phone/OTP authorization in the browser.")
        print("Waiting for callback (up to 3 minutes)...")

        if not _event.wait(180):
            server.shutdown()
            raise TimeoutError("OAuth callback was not received within 3 minutes.")

        server.shutdown()

        if _received.get("error"):
            raise RuntimeError(f"Swiggy authorization failed: {_received['error']}")

        code = _received.get("code")
        callback_state = _received.get("state")
        if not code:
            raise RuntimeError("Authorization callback did not contain a code.")
        if callback_state != state:
            raise RuntimeError("OAuth state mismatch. Please run login again.")

        print("Authorization code received.")
        print("Exchanging authorization code...")

        # Current Swiggy documentation specifies code, verifier and redirect_uri
        # for the authorization_code exchange. client_id is not required here.
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": REDIRECT_URI,
        }

        response = client.post(
            TOKEN_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Token exchange failed: HTTP {response.status_code}. "
                f"Response: {response.text[:1000]}"
            )

        token = response.json()
        access_token = token.get("access_token")
        if not access_token:
            raise RuntimeError(f"Token response has no access_token: {token}")

        expires_in = int(token.get("expires_in", 432000))
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, access_token)

        META_FILE.write_text(
            json.dumps(
                {
                    "client_id": client_id,
                    "token_type": token.get("token_type", "Bearer"),
                    "scope": token.get("scope", "mcp:tools"),
                    "expires_at": int(time.time()) + expires_in,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        print("OAuth successful.")
        print("Access token stored in the Windows credential store.")
        print("You can now run: python run_scanner.py")


if __name__ == "__main__":
    main()
