const targetRepository = "betabitplus-template-lab/sandbox-private-uv-consumer-20260724-r1";
const sourceRepository = "betabitplus-template-lab/sandbox-private-uv-source-20260724-r1";
const mode = process.env.LAB_MODE;
const dependencyToken = process.env.DEPENDENCY_TOKEN;

if (!["lock-maintenance", "private-update"].includes(mode)) {
  throw new Error(`Unsupported LAB_MODE: ${mode}`);
}
if (!dependencyToken) {
  throw new Error("DEPENDENCY_TOKEN is required");
}

module.exports = {
  platform: "github",
  autodiscover: false,
  repositories: [targetRepository],
  onboarding: false,
  requireConfig: "required",
  allowScripts: false,
  dependencyDashboard: false,
  printConfig: true,
  packageRules:
    mode === "lock-maintenance"
      ? [{ matchPackageNames: ["*"], enabled: false }]
      : [{ matchPackageNames: ["packaging"], enabled: false }],
  branchPrefix:
    mode === "lock-maintenance"
      ? "renovate-lab-lock/"
      : "renovate-lab-private/",
  hostRules: [
    {
      matchHost: `https://api.github.com/repos/${sourceRepository}`,
      token: dependencyToken,
    },
  ],
  secrets: {
    DEPENDENCY_TOKEN: dependencyToken,
  },
  customEnvVariables: {
    GIT_CONFIG_COUNT: "1",
    GIT_CONFIG_KEY_0:
      "url.https://x-access-token:{{ secrets.DEPENDENCY_TOKEN }}@github.com/.insteadOf",
    GIT_CONFIG_VALUE_0: "https://github.com/",
    GIT_TERMINAL_PROMPT: "0",
  },
  force: {
    lockFileMaintenance:
      mode === "lock-maintenance"
        ? { enabled: true, schedule: ["at any time"], branchTopic: "lock-file-maintenance" }
        : { enabled: false },
  },
};
