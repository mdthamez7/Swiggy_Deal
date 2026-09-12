import os
import ssl
import smtplib

from collections import defaultdict
from email.message import EmailMessage

import certifi
from dotenv import load_dotenv

load_dotenv()


def send_deal_email(deals, unmapped, errors):
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    to = os.getenv("ALERT_TO", "").strip()

    # Handle empty/invalid SMTP port safely
    port_raw = os.getenv("SMTP_PORT", "").strip()

    try:
        port = int(port_raw) if port_raw else 587
    except ValueError:
        port = 587

    # Email is optional.
    # If SMTP settings are not configured, skip email without failing the scan.
    if not all([host, user, password, to]):
        print("Email alert not configured; skipping.")
        return False

    grouped = defaultdict(list)

    for d in deals:
        grouped[d["state"]].append(d)

    lines = [
        "LootDeal - Swiggy Instamart Deal Alert",
        "=" * 70,
        "",
    ]

    for state in sorted(grouped):
        lines += [
            f"STATE: {state}",
            "-" * 70,
        ]

        for d in grouped[state]:
            lines += [
                f"Category: {d['category']}",
                f"Product: {d['name']}",
                f"Brand: {d['brand'] or '-'}",
                f"Pack: {d['pack'] or '-'}",
                (
                    f"MRP: ₹{d['mrp']:.2f}"
                    if d["mrp"] is not None
                    else "MRP: -"
                ),
                f"Current: ₹{d['price']:.2f}",
                (
                    f"Previous Low: ₹{d['previous_low']:.2f}"
                    if d["previous_low"] is not None
                    else "Previous Low: -"
                ),
                f"Location: {d['city']} - {d['pincode']}",
                f"Reason: {', '.join(d['reasons'])}",
                f"Product ID: {d['product_id']} | SKU ID: {d['sku_id']}",
                "",
            ]

    if unmapped:
        lines += [
            "TARGETS WITHOUT REAL SWIGGY ADDRESS MAPPING",
            "-" * 70,
        ]

        lines += [
            f"- {t['state']} / {t['city']} / {t['pincode']}"
            for t in unmapped
        ]

        lines.append("")

    if errors:
        lines += [
            "SCAN ERRORS",
            "-" * 70,
        ]

        lines += [
            f"- {e['state']} / {e['city']} {e['pincode']} / "
            f"{e['category']}: {e['error']}"
            for e in errors[:100]
        ]

    msg = EmailMessage()
    msg["Subject"] = f"LootDeal Alert - {len(deals)} new deal(s)"
    msg["From"] = user
    msg["To"] = to
    msg.set_content("\n".join(lines))

    try:
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls(
                context=ssl.create_default_context(
                    cafile=certifi.where()
                )
            )
            s.login(user, password)
            s.send_message(msg)

        print(f"Email alert sent: {len(deals)} deal(s)")
        return True

    except Exception as exc:
        # Email failure should not make the scanner fail.
        print(f"Email alert failed; continuing scan: {exc}")
        return False