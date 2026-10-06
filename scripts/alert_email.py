"""Render concise cluster notifications without exposing routing JSON in the body."""

import html
import json
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def details(data):
    context = data.get("context") or {}
    nested = context.get("details") or data.get("details") or {}
    result = dict(nested) if isinstance(nested, dict) else {}
    for layer in (context, data):
        result.update({k: v for k, v in layer.items() if v not in (None, "", {}) or k not in result})
    return result


def node_names(value):
    values = value if isinstance(value, list) else str(value or "").split(",")
    return ", ".join(sorted({str(v).strip() for v in values if str(v).strip()}))


def render(data, run_url=""):
    fields = details(data)
    cluster = str(fields.get("cluster") or "pi-k3s")
    event = str(fields.get("event") or fields.get("status") or "update").lower()
    recovered = event in ("recovery", "resolved", "node-recovered")
    down = node_names(fields.get("nodes_down"))
    restored = node_names(fields.get("nodes_recovered"))
    remaining = node_names(fields.get("nodes_down_current"))
    affected = restored if recovered else down
    label = "Nodes recovered" if recovered else "Node incident"
    if event in ("mixed", "change"):
        label = "Node status changed"
        affected = "; ".join(filter(None, [down, restored]))
    if fields.get("resource_type") == "service":
        label = "Service recovered" if recovered else "Service incident"
    subject = f"[{cluster}] {label}" + (f": {affected}" if affected else "")
    subject = subject.replace("\r", " ").replace("\n", " ")[:200]
    rows = []
    if down:
        rows.append(("Newly down", down))
    if restored:
        rows.append(("Recovered", restored))
    if "nodes_down_current" in fields:
        rows.append(("Still down", remaining or "None"))
    timestamp = str(fields.get("timestamp") or "")
    if timestamp:
        try:
            instant = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if instant.tzinfo is None:
                instant = instant.replace(tzinfo=timezone.utc)
            try:
                display_zone = ZoneInfo("America/New_York")
            except ZoneInfoNotFoundError:
                display_zone = timezone.utc
                rows.append(("Timezone notice", "Eastern timezone data unavailable on the sender; displaying UTC."))
            rows.append(("Time", instant.astimezone(display_zone).strftime("%b %d, %Y at %I:%M:%S %p %Z")))
            rows.append(("UTC", instant.astimezone(timezone.utc).isoformat()))
        except ValueError:
            rows.append(("Time", timestamp))
    routing = fields.get("routing") or {}
    if routing.get("service"):
        rows.append(("Service", str(routing["service"])))
    summary = str(fields.get("summary") or "Cluster node readiness changed.")
    action = "Recovery observed; continue monitoring."
    if remaining or not recovered:
        action = "Check affected node power, network connectivity, and k3s service health."
    if run_url:
        rows.append(("Workflow", run_url))
    plain = "\n".join([subject, "", summary, "", *[f"{k}: {v}" for k, v in rows], "", action])
    color = "#147d40" if recovered and not remaining else "#a32323"
    table = "".join(f'<tr><th style="text-align:left;padding:8px 16px 8px 0;vertical-align:top">{html.escape(k)}</th><td style="padding:8px 0;overflow-wrap:anywhere">{html.escape(v)}</td></tr>' for k, v in rows)
    rich = f'''<!doctype html><html><body style="margin:0;background:#f4f5f7;color:#202124;font:15px Arial,sans-serif">
<main style="max-width:640px;margin:24px auto;padding:24px;background:white;border-top:5px solid {color}">
<p style="color:#555;margin:0 0 12px">{html.escape(cluster)} / cluster operations</p>
<h1 style="font-size:24px;margin:0 0 16px;color:{color}">{html.escape(label)}</h1>
<p>{html.escape(summary)}</p><table style="border-collapse:collapse;width:100%">{table}</table>
<p style="border-top:1px solid #ddd;padding-top:16px">{html.escape(action)}</p>
</main></body></html>'''
    return subject, plain, rich


def main():
    raw = os.environ.get("PAYLOAD")
    if not raw or raw == "null":
        raw = os.environ.get("PAYLOAD_INPUT") or "{}"
    data = json.loads(raw)
    if not isinstance(data, dict) or not data:
        print("Skipped empty alert payload")
        return
    fields = details(data)
    is_node = fields.get("resource_type") == "node" or fields.get("event_type") == "node" or str(fields.get("status", "")).startswith("node-")
    if os.environ.get("ALERT_STAGE") == "triaged" and is_node and os.environ.get("TRIAGED_NODE_EMAIL_ENABLED", "false").lower() != "true":
        print("Skipped duplicate triaged node email; ingress owns node notifications")
        return
    run_url = f'https://github.com/{os.environ["GITHUB_REPOSITORY"]}/actions/runs/{os.environ["GITHUB_RUN_ID"]}' if os.environ.get("GITHUB_REPOSITORY") and os.environ.get("GITHUB_RUN_ID") else ""
    subject, plain, rich = render(data, run_url)
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.environ.get("MAIL_FROM", "preview@example.invalid")
    message["To"] = os.environ.get("MAIL_TO", "preview@example.invalid")
    message.set_content(plain)
    message.add_alternative(rich, subtype="html")
    if os.environ.get("DRY_RUN", "false").lower() == "true":
        print(plain)
        print("Dry run: no email sent")
        return
    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"]), timeout=30) as smtp:
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        smtp.send_message(message)


if __name__ == "__main__":
    main()
