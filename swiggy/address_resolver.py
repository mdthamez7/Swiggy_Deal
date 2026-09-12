import re
from typing import Any

from swiggy.client import MCPClient, unwrap_tool_result


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _address_text(address: dict) -> str:
    return " ".join(
        str(address.get(k, ""))
        for k in ("addressLine", "addressLine2", "locality", "city", "postalCode", "pincode", "addressTag", "addressCategory")
    )


def _matches(address: dict, target: dict) -> bool:
    text = _address_text(address)
    ntext = _norm(text)
    pin = _norm(target.get("pincode"))
    city = _norm(target.get("city"))
    state = _norm(target.get("state"))

    if pin and pin not in ntext:
        return False
    if city and city not in ntext:
        return False
    # State names are not consistently returned by Swiggy, so do not require
    # them when city + pincode already match.
    return bool(pin or city) and (not state or state in ntext or True)


def fetch_saved_addresses(mcp: MCPClient, page_size: int = 10) -> list[dict]:
    """Fetch every saved address without creating or guessing any address."""
    addresses: list[dict] = []
    page = 1
    while True:
        raw = unwrap_tool_result(
            mcp.call_tool("get_addresses", {"page": page, "pageSize": page_size})
        )
        data = raw.get("data", raw) if isinstance(raw, dict) else {}
        batch = data.get("addresses", []) if isinstance(data, dict) else []
        if isinstance(batch, list):
            addresses.extend(a for a in batch if isinstance(a, dict) and a.get("id"))
        pagination = data.get("pagination", {}) if isinstance(data, dict) else {}
        if not pagination.get("hasMore"):
            break
        page += 1
        if page > 100:
            break
    return addresses


def resolve_targets(targets: list[dict], token: str | None = None) -> tuple[list[tuple[dict, str]], list[dict]]:
    """Resolve target city/pincode to real saved Swiggy address IDs.

    No address ID is invented. If a target has no matching saved address,
    it is returned as unresolved and can be reported/skipped.
    """
    mcp = MCPClient(token=token)
    try:
        mcp.initialize()
        try:
            mcp.initialized()
        except Exception:
            pass
        addresses = fetch_saved_addresses(mcp)
    finally:
        mcp.close()

    resolved: list[tuple[dict, str]] = []
    unresolved: list[dict] = []
    used: set[str] = set()

    for target in targets:
        matches = [a for a in addresses if _matches(a, target)]
        if not matches:
            unresolved.append(target)
            continue

        # Prefer the first matching saved address. get_addresses is ordered by
        # Swiggy by recent usage, so this is deterministic without inventing data.
        chosen = matches[0]
        aid = str(chosen["id"])
        if aid in used:
            # The same saved address can legitimately serve multiple target
            # records only when the target records are aliases. Keep it usable.
            pass
        used.add(aid)
        resolved.append((target, aid))

    return resolved, unresolved
