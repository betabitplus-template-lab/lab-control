const repositoryNames = JSON.parse(
  process.env.FULL_FLEET_REPOSITORIES_JSON || "[]",
);
const owner = process.env.RENOVATE_REPOSITORY_OWNER;

if (!Array.isArray(repositoryNames) || repositoryNames.length === 0) {
  throw new Error("FULL_FLEET_REPOSITORIES_JSON must contain repositories");
}
if (!owner) {
  throw new Error("RENOVATE_REPOSITORY_OWNER is required");
}

module.exports = {
  platform: "github",
  repositories: repositoryNames.map((name) => `${owner}/${name}`),
  onboarding: false,
  requireConfig: "ignored",
  dryRun: "full",
  dependencyDashboard: false,
  enabledManagers: ["copier", "github-actions", "pep621", "vendir"],
  gitAuthor: "Ternforge Lab Renovate <8123085+betabitplus@users.noreply.github.com>",
};
