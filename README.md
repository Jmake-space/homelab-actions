# homelab-actions

GitHub Actions workflows and self-hosted runner for the homelab.

## Flow
```
k3s-node-alert (CronJob or systemd)
  -> repository_dispatch (GitHub App token)
  -> k3s-node-alert.yml
  -> SMTP email
```

## Workflows
- `k3s-node-alert.yml`: sends email alerts when a webhook dispatch is received.

## Runner
- Labels: `self-hosted`, `pi5`, `docker`
- Docker-based runner config lives in `/home/jaideepbir/code/projects/homelab-runner-docker/`.
- Install on `pi5` (not control plane).
