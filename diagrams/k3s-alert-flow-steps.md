# k3s Alert Flow (Current, with Deprecated Path Marked)

1. `node-health-watcher` runs in the cluster and watches node and service health transitions.
2. When an alert condition is detected, watcher sends `repository_dispatch` to `Jmake-space/homelab-actions` with `event_type: k3s-alert` and structured `client_payload`.
3. `homelab-actions/.github/workflows/k3s-alert.yml` starts on that dispatch.
4. `notify` job sends ingress alert email with cluster, event, status, summary, and payload context.
5. `forward-triage-router` job mints a short-lived GitHub App installation token (`K3S_OPS_APP_ID` + `K3S_OPS_APP_PRIVATE_KEY`).
6. `forward-triage-router` dispatches payload to `Jmake-space/k3s-cluster` with `event_type: triage-router-workflow`.
7. `k3s-cluster/.github/workflows/triage-router-workflow.yml` normalizes payload, runs optional read-only SSH triage, and resolves route via `service-agent-map.json`.
8. Triage emits `triaged-agent-alert` to `homelab-actions` with `target_agent`, `route_reason`, `resource_type`, runbook reference, and mitigation context.
9. `homelab-actions/.github/workflows/triaged-agent-alerts.yml` sends triaged alert notification to the mapped agent path.
10. If `target_agent == k3s-support-agent`, `support-incident-log` writes and commits incident markdown under `incidents/k3s-support-agent/YYYY/MM/`.
11. Target service/support agent performs triage-driven remediation steps from runbook/mitigation plan; disruptive actions require explicit approval.

## Deprecated / Disabled Flow (Shown as Disabled in Diagram)

1. Legacy `k3s-node-alert` cronjob path is deprecated and should not be treated as active source of truth.
2. Legacy dispatch payload previously used `event_type: k3s-node-alert`; this is intentionally separated and marked disabled in the updated diagram.
