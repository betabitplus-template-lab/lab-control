const fs = require("fs");
const path = require("path");

const requestPath = path.join(__dirname, "request.json");
const request = JSON.parse(fs.readFileSync(requestPath, "utf8"));
const allowed = new Set([
  "betabitplus-template-lab/python-lib",
  "betabitplus-template-lab/python-internal-package",
  "betabitplus-template-lab/python-starter-platform",
  "betabitplus-template-lab/sandbox-python-lib",
  "betabitplus-template-lab/sandbox-python-platform",
  "betabitplus-template-lab/sandbox-workspace",
]);

if (!Array.isArray(request.repositories) || request.repositories.length === 0) {
  throw new Error("Renovate request must contain a non-empty repositories array");
}
for (const repository of request.repositories) {
  if (!allowed.has(repository)) {
    throw new Error(`Unsafe Renovate repository: ${repository}`);
  }
}
if (![null, "extract", "lookup", "full"].includes(request.dry_run)) {
  throw new Error(`Unsupported dry_run value: ${request.dry_run}`);
}

module.exports = {
  platform: "github",
  autodiscover: false,
  repositories: request.repositories,
  onboarding: false,
  requireConfig: "required",
  ...(request.dry_run === null ? {} : { dryRun: request.dry_run }),
  allowScripts: false,
  branchPrefix: "renovate-lab/",
  dependencyDashboard: true,
  printConfig: true,
};
