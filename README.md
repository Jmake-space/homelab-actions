# homelab-actions

GitHub Actions workflows and self-hosted runner for the homelab.

## Flow
```
k3s-alert (watcher dispatch ingress)
  -> repository_dispatch (GitHub App token)
  -> k3s-alert.yml
  -> SMTP email
```

## Workflows
- `k3s-alert.yml`: ingress alert receiver; forwards payload to `k3s-cluster` triage router.
- `triaged-agent-alerts.yml`: receives normalized triaged alerts, sends notifications, and logs support incidents.

## Node notification policy
- Ingress sends the node email; triaged node emails are skipped by default to avoid duplicates. Set repository variable `TRIAGED_NODE_EMAIL_ENABLED=true` only to opt into both stages. Service triage emails and incident routing remain enabled.
- Emails have matching plain-text and HTML bodies with affected/recovered nodes, remaining outages, Eastern time (EDT/EST), UTC, and the source workflow link. Routing JSON is retained in incident logs instead of the email body.
- Manual workflow runs default to `dry_run=true`: preview only, with no SMTP, downstream dispatch, or incident commits. Uncheck it only for an intentional live test.
- Source watcher confirmation thresholds determine transient suppression; do not use email formatting to hide sustained node outages.
- Runners require system `tzdata` for Eastern timestamps. If it is unavailable, the renderer explicitly displays UTC and a timezone notice so a timezone dependency cannot prevent email delivery.

## Runner
- Labels: `self-hosted`, `pi5`, `docker`
- Docker-based runner config lives in `/home/jaideepbir/code/projects/homelab-runner-docker/`.
- Install on `pi5` (not control plane).
