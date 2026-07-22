const repositories = JSON.parse(process.env.SHARD_REPOSITORIES_JSON || "[]");

if (!Array.isArray(repositories) || repositories.length === 0) {
  throw new Error("SHARD_REPOSITORIES_JSON must contain at least one repository");
}

module.exports = {
  platform: "github",
  repositories,
  onboarding: false,
  requireConfig: "required",
  dependencyDashboard: false,
  gitAuthor: "Ternforge Lab Renovate <8123085+betabitplus@users.noreply.github.com>",
};
