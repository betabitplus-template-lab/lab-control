module.exports = {
  platform: "github",
  autodiscover: false,
  repositories: [
    "betabitplus-template-lab/python-lib",
    "betabitplus-template-lab/sandbox-python-lib",
  ],
  onboarding: false,
  requireConfig: "required",
  dryRun: process.env.RENOVATE_DRY_RUN || "full",
  allowScripts: false,
  branchPrefix: "renovate-lab/",
};
