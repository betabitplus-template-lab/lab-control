# OpenTofu Grafana Cloud lifecycle evidence

## Outcome

**Passed.** Final run `30638444420` completed successfully on workflow commit `4d2f06db38f085ab5f5a6b4329cf716760107952`.

## Validated lifecycle

```text
OpenTofu 1.12.5
+ grafana/grafana 4.40.1
+ locked provider selection

initial plan
→ six creates
→ Cloud plugin 2.8.0
→ folder
→ GitHub data source
→ two-panel dashboard
→ contact point
→ alert rule group

API readback
→ data source health OK
→ plugin readiness wait 0.802 seconds in final run

second plan
→ exit 0, no drift

controlled alert threshold change 600 → 900
→ exit 2
→ only grafana_rule_group.fleet_health updated

post-change plan
→ exit 0, no drift

destroy
→ six resources destroyed
→ plugin, folder, data source, dashboard and alert endpoints HTTP 404
→ contact point absent
```

## Security boundary

* OpenTofu state and binary plans stayed on the ephemeral GitHub-hosted runner and were not uploaded.
* Only sanitized JSON, Markdown and logs were uploaded.
* The evidence secret scan passed.
* The data-source secure configuration makes OpenTofu state sensitive even when plan output masks the value.
* Temporary GitHub Secrets, Grafana service accounts, access policies and tokens were removed after the final run.

## Significant finding

Grafana Cloud plugin installation is asynchronous. The provider can finish the plugin installation resource before the GitHub data-source backend is registered everywhere. Run `30637998674` created and destroyed all six resources but observed a transient `plugin not registered` health response. The final implementation uses a bounded readiness poll and then reaches stable no-drift plans.

## Remaining boundary

This validates the technology path, not the final production ownership decision. A future ADR still has to choose the owning repository, remote state backend, state recovery/locking model and least-privilege Grafana service-account permissions. The personal-account GitHub App acceptance check and post-trial Free check also remain separate.
