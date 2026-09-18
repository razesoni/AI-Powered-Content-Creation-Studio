# Terraform implementation boundary

Select a target cloud before writing deployable resources. Keep these modules provider-specific but expose consistent inputs/outputs:

```text
modules/
  network/       # private/public subnets, firewall/security groups
  database/      # managed PostgreSQL, backups, connection secret
  api/           # container runtime, autoscaling, health checks
  web/           # object storage/CDN or static hosting
  observability/ # logs, metrics, alerts, budget alarm
environments/
  dev/
  prod/
```

Required inputs: region, environment, image tags, frontend origin, domain, database size, API CPU/memory, minimum/maximum instances, backup retention, and alert budget. Outputs: frontend URL, API URL, database secret reference, and log dashboard URL.

Never commit Terraform state or secrets. Use a remote encrypted backend with locking. Pin provider/module versions and require a reviewed plan before apply.
