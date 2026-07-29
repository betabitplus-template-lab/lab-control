variable "owner" {
  type    = string
  default = "betabitplus-template-lab"
}

variable "repository_name" {
  type    = string
  default = "sandbox-provisioned"
}

variable "description" {
  type    = string
  default = "Ephemeral production-shaped provisioning experiment"
}

variable "post_bootstrap" {
  type    = bool
  default = false
}

variable "enable_rulesets" {
  type    = bool
  default = false
}

variable "required_check" {
  type    = string
  default = "required / python-library-ci"
}

variable "renovate_installation_id" {
  type     = string
  default  = null
  nullable = true
}

variable "release_app_id" {
  type     = number
  default  = null
  nullable = true
}
