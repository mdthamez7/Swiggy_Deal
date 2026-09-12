import json
import os
import time

import certifi
import httpx
import keyring
from dotenv import load_dotenv

load_dotenv()

KEYRING_SERVICE = "LootDeal-Swiggy-MCP"
KEYRING_USERNAME = "swiggy-access-token"


class MCPError(RuntimeError):
    pass


def load_access_token():
    token = os.getenv('SWIGGY_ACCESS_TOKEN', '').strip() or keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
    if not token:
        raise RuntimeError(
            "No Swiggy access token found. Run: "
            "python -m swiggy.oauth_login"
        )
    return token


def parse_response(response):
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        messages = []
        for line in response.text.splitlines():
            if line.startswith("data:"):
                data = line[5:].strip()
                if data:
                    try:
                        messages.append(json.loads(data))
                    except json.JSONDecodeError:
                        pass
        if messages:
            # Return the last JSON-RPC message. MCP notifications may appear
            # before/after the response.
            for msg in reversed(messages):
                if "id" in msg or "result" in msg or "error" in msg:
                    return msg
        raise MCPError("Swiggy MCP returned an empty SSE response.")
    return response.json()


class MCPClient:
    def __init__(self, token=None):
        self.token = token or load_access_token()
        self.url = os.getenv("SWIGGY_IM_MCP_URL", "https://mcp.swiggy.com/im")
        self.session_id = None
        self.msg_id = 0
        self.client = httpx.Client(
            timeout=90,
            verify=certifi.where(),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )

    def close(self):
        self.client.close()

    def _post(self, payload):
        headers = {}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        response = self.client.post(self.url, json=payload, headers=headers)

        if response.status_code == 401:
            raise PermissionError(
                "Swiggy returned HTTP 401. The OAuth token expired/revoked. "
                "Run python -m swiggy.oauth_login again."
            )
        response.raise_for_status()

        sid = response.headers.get("Mcp-Session-Id")
        if sid:
            self.session_id = sid

        return parse_response(response)

    def _request(self, method, params=None):
        self.msg_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params
        return self._post(payload)

    def initialize(self):
        return self._request(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "LootDealScanner",
                    "version": "1.0.0",
                },
            },
        )

    def initialized(self):
        self.msg_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        # Notifications should not contain an id.
        self._post(payload)

    def list_tools(self):
        return self._request("tools/list", {"cursor": None})

    def call_tool(self, name, arguments):
        result = self._request(
            "tools/call",
            {"name": name, "arguments": arguments},
        )
        if "error" in result:
            raise MCPError(str(result["error"]))
        return result.get("result", result)


def unwrap_tool_result(result):
    if not isinstance(result, dict):
        return result

    if "structuredContent" in result:
        return result["structuredContent"]

    content = result.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "")
                try:
                    return json.loads(text)
                except Exception:
                    continue

    return result
