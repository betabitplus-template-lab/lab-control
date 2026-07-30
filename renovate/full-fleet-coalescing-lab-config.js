const owner = process.env.RENOVATE_REPOSITORY_OWNER;
const consumer = process.env.RENOVATE_COALESCING_CONSUMER;

if (!owner) {
  throw new Error("RENOVATE_REPOSITORY_OWNER is required");
}
if (!consumer) {
  throw new Error("RENOVATE_COALESCING_CONSUMER is required");
}

module.exports = {
  platform: "github",
  repositories: [`${owner}/${consumer}`],
  onboarding: false,
  requireConfig: "ignored",
  dryRun: "full",
  dependencyDashboard: false,
  enabledManagers: ["pep621"],
  gitAuthor: "Ternforge Lab Renovate <8123085+betabitplus@users.noreply.github.com>",
};
