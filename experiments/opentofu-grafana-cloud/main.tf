terraform {
  required_version = ">= 1.12.4, < 1.13.0"

  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "= 4.40.1"
    }
  }
}

provider "grafana" {
  alias = "cloud"
}

provider "grafana" {
  alias      = "stack"
  retries    = 3
  retry_wait = 5
}

resource "grafana_cloud_plugin_installation" "github" {
  provider = grafana.cloud

  stack_slug = var.grafana_stack_slug
  slug       = "grafana-github-datasource"
  version    = "2.8.0"
}

resource "grafana_folder" "fleet_health" {
  provider = grafana.stack

  uid   = "ternforge-opentofu-lab"
  title = "Ternforge OpenTofu Lab"
}

resource "grafana_data_source" "github" {
  provider = grafana.stack

  type        = "grafana-github-datasource"
  name        = "Ternforge OpenTofu GitHub Lab"
  uid         = "ternforge-opentofu-github-lab"
  access_mode = "proxy"

  json_data_encoded = jsonencode({
    selectedAuthType = "github-app"
    appId            = var.github_app_id
    installationId   = var.github_app_installation_id
    cachingEnabled   = true
  })

  secure_json_data_encoded = var.github_data_source_secret

  depends_on = [grafana_cloud_plugin_installation.github]
}

resource "grafana_dashboard" "fleet_health" {
  provider = grafana.stack

  folder    = grafana_folder.fleet_health.uid
  overwrite = true
  message   = "OpenTofu Grafana Cloud lifecycle lab"

  config_json = jsonencode({
    uid           = "ternforge-opentofu-lab"
    title         = "Ternforge OpenTofu Lab"
    tags          = ["ternforge", "lab", "opentofu"]
    timezone      = "browser"
    schemaVersion = 41
    refresh       = "1m"
    time = {
      from = "now-24h"
      to   = "now"
    }
    panels = [
      {
        id    = 1
        type  = "stat"
        title = "Fleet health placeholder"
        datasource = {
          type = "prometheus"
          uid  = "grafanacloud-prom"
        }
        gridPos = { h = 8, w = 8, x = 0, y = 0 }
        targets = [{
          refId = "A"
          expr  = "vector(1)"
        }]
      },
      {
        id    = 2
        type  = "table"
        title = "Managed repositories"
        datasource = {
          type = "grafana-github-datasource"
          uid  = grafana_data_source.github.uid
        }
        gridPos = { h = 8, w = 16, x = 8, y = 0 }
        targets = [{
          refId      = "A"
          queryType  = "Repositories"
          owner      = "betabitplus-template-lab"
          repository = ""
          options    = {}
        }]
        transformations = [{
          id = "filterByValue"
          options = {
            match = "all"
            type  = "include"
            filters = [{
              fieldName = "name"
              config = {
                id      = "equal"
                options = { value = "lab-control" }
              }
            }]
          }
        }]
      }
    ]
  })
}

resource "grafana_contact_point" "lab" {
  provider = grafana.stack

  name = "Ternforge OpenTofu Lab"

  webhook {
    url                     = "https://example.invalid/ternforge-opentofu-lab"
    http_method             = "POST"
    disable_resolve_message = false
    title                   = "Ternforge OpenTofu lab"
  }
}

resource "grafana_rule_group" "fleet_health" {
  provider = grafana.stack

  name             = "ternforge-opentofu-lab"
  folder_uid       = grafana_folder.fleet_health.uid
  interval_seconds = 60

  rule {
    uid            = "ternforge-opentofu-rule-lab"
    name           = "Ternforge OpenTofu processing duration"
    condition      = "B"
    for            = "0s"
    no_data_state  = "OK"
    exec_err_state = "Error"
    is_paused      = false

    annotations = {
      summary = "OpenTofu-managed lab rule"
    }

    labels = {
      service = "ternforge"
      scope   = "lab"
    }

    data {
      ref_id         = "A"
      datasource_uid = "grafanacloud-prom"

      relative_time_range {
        from = 600
        to   = 0
      }

      model = jsonencode({
        datasource = {
          type = "prometheus"
          uid  = "grafanacloud-prom"
        }
        editorMode    = "code"
        expr          = "vector(1)"
        instant       = true
        intervalMs    = 1000
        maxDataPoints = 43200
        range         = false
        refId         = "A"
      })
    }

    data {
      ref_id         = "B"
      datasource_uid = "-100"

      relative_time_range {
        from = 0
        to   = 0
      }

      model = jsonencode({
        conditions = [{
          evaluator = {
            params = [var.alert_threshold_seconds]
            type   = "gt"
          }
          operator = { type = "and" }
          query    = { params = ["B"] }
          reducer  = { params = [], type = "last" }
          type     = "query"
        }]
        datasource = {
          type = "__expr__"
          uid  = "-100"
        }
        expression    = "A"
        intervalMs    = 1000
        maxDataPoints = 43200
        refId         = "B"
        type          = "threshold"
      })
    }

    notification_settings {
      contact_point = grafana_contact_point.lab.name
    }
  }
}

output "managed_resources" {
  value = {
    plugin_slug      = grafana_cloud_plugin_installation.github.slug
    folder_uid       = grafana_folder.fleet_health.uid
    datasource_uid   = grafana_data_source.github.uid
    dashboard_uid    = grafana_dashboard.fleet_health.uid
    contact_point_id = grafana_contact_point.lab.id
    alert_rule_group = grafana_rule_group.fleet_health.name
  }
}
