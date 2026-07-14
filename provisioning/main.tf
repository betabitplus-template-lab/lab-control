provider "github" {
  owner = var.owner
  # Authentication is supplied through GITHUB_TOKEN/GH_TOKEN. No secret resource
  # or secret value is stored in OpenTofu state.
}

resource "github_repository" "managed" {
  name                   = var.repository_name
  description            = var.description
  visibility             = "private"
  auto_init              = false
  has_issues             = true
  has_projects           = false
  has_wiki               = false
  allow_merge_commit     = false
  allow_rebase_merge     = false
  allow_squash_merge     = true
  allow_auto_merge       = false
  allow_update_branch    = true
  delete_branch_on_merge = true
  archive_on_destroy     = true
  topics = [
    "betabit-template-managed",
    "betabit-template-python-lib",
  ]
}

resource "github_branch" "main" {
  count         = var.post_bootstrap ? 1 : 0
  repository    = github_repository.managed.name
  branch        = "main"
  source_branch = "dev"
}

resource "github_branch_default" "dev" {
  count      = var.post_bootstrap ? 1 : 0
  repository = github_repository.managed.name
  branch     = "dev"
  depends_on = [github_branch.main]
}

resource "github_actions_variable" "template_lane" {
  count         = var.post_bootstrap ? 1 : 0
  repository    = github_repository.managed.name
  variable_name = "TEMPLATE_LANE"
  value         = "python-lib"
}

resource "github_app_installation_repository" "renovate" {
  count           = var.post_bootstrap && var.renovate_installation_id != null ? 1 : 0
  installation_id = var.renovate_installation_id
  repository      = github_repository.managed.name
}

resource "github_repository_ruleset" "dev" {
  count       = var.post_bootstrap && var.enable_rulesets ? 1 : 0
  name        = "managed-dev"
  repository  = github_repository.managed.name
  target      = "branch"
  enforcement = "active"
  conditions {
    ref_name {
      include = ["refs/heads/dev"]
      exclude = []
    }
  }
  rules {
    deletion         = true
    non_fast_forward = true
    pull_request {
      allowed_merge_methods             = ["squash"]
      required_approving_review_count   = 1
      required_review_thread_resolution = true
      dismiss_stale_reviews_on_push     = true
      require_last_push_approval        = true
    }
    required_status_checks {
      strict_required_status_checks_policy = true
      do_not_enforce_on_create             = true
      required_check {
        context = var.required_check
      }
    }
  }
  depends_on = [github_branch_default.dev]
}

resource "github_repository_ruleset" "main" {
  count       = var.post_bootstrap && var.enable_rulesets ? 1 : 0
  name        = "promotion-main"
  repository  = github_repository.managed.name
  target      = "branch"
  enforcement = "active"
  conditions {
    ref_name {
      include = ["refs/heads/main"]
      exclude = []
    }
  }
  rules {
    deletion         = true
    non_fast_forward = true
    pull_request {
      allowed_merge_methods             = ["squash"]
      required_approving_review_count   = 1
      required_review_thread_resolution = true
      dismiss_stale_reviews_on_push     = true
      require_last_push_approval        = true
    }
    required_status_checks {
      strict_required_status_checks_policy = true
      do_not_enforce_on_create             = true
      required_check {
        context = var.required_check
      }
    }
  }
  depends_on = [github_branch.main]
}

resource "github_repository_ruleset" "release_tags" {
  count       = var.post_bootstrap && var.enable_rulesets ? 1 : 0
  name        = "immutable-release-tags"
  repository  = github_repository.managed.name
  target      = "tag"
  enforcement = "active"
  conditions {
    ref_name {
      include = ["refs/tags/v*"]
      exclude = []
    }
  }
  dynamic "bypass_actors" {
    for_each = var.release_app_id == null ? [] : [var.release_app_id]
    content {
      actor_id    = bypass_actors.value
      actor_type  = "Integration"
      bypass_mode = "always"
    }
  }
  rules {
    deletion         = true
    non_fast_forward = true
  }
}
