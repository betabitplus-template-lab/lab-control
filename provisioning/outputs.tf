output "repository" {
  value = github_repository.managed.full_name
}

output "clone_url" {
  value = github_repository.managed.http_clone_url
}

output "phase" {
  value = var.post_bootstrap ? "post-bootstrap" : "repository-only"
}
