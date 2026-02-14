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

## Runner
- Labels: `self-hosted`, `pi5`, `docker`
- Docker-based runner config lives in `/home/jaideepbir/code/projects/homelab-runner-docker/`.
- Install on `pi5` (not control plane).
