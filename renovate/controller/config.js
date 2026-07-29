const dryRun = process.env.RENOVATE_DRY_RUN || 'extract';
if (!['extract', 'lookup', 'full'].includes(dryRun)) {
  throw new Error(`Unsupported RENOVATE_DRY_RUN=${dryRun}`);
}
module.exports = {
  platform: 'github',
  endpoint: 'https://api.github.com/',
  autodiscover: true,
  autodiscoverFilter: ['betabitplus-template-lab/*'],
  autodiscoverTopics: ['betabit-template-managed'],
  writeDiscoveredRepos: process.env.RENOVATE_WRITE_DISCOVERED_REPOS || undefined,
  dryRun,
  onboarding: false,
  requireConfig: 'required',
  allowedCommands: ['^uv lock$'],
  allowScripts: false,
  optimizeForDisabled: true,
  forkProcessing: 'disabled',
};
