const repositoryNames = JSON.parse(process.env.SHARD_REPOSITORIES_JSON || "[]");
const owner = process.env.RENOVATE_REPOSITORY_OWNER;

if (!Array.isArray(repositoryNames) || repositoryNames.length === 0) {
  throw new Error("SHARD_REPOSITORIES_JSON must contain at least one repository");
}
if (!owner) {
  throw new Error("RENOVATE_REPOSITORY_OWNER is required");
}

module.exports = {
  platform: "github",
  repositories: repositoryNames.map((name) => `${owner}/${name}`),
  onboarding: false,
  requireConfig: "required",
  dependencyDashboard: false,
  gitAuthor: "Ternforge Lab Renovate <8123085+betabitplus@users.noreply.github.com>",
};
