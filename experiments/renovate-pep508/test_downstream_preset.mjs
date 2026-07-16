import assert from "node:assert/strict";
import fs from "node:fs";

const configPath = process.argv[2] ?? "renovate/presets/downstream.json5";
const config = JSON.parse(fs.readFileSync(configPath, "utf8"));

const fixtures = new Map([
  [
    "py-lib-runtime",
    '"py-lib-runtime @ git+https://github.com/betabitplus/py-lib-starter.git@v0.32.3#subdirectory=packages/py-lib-runtime",',
  ],
  [
    "py-lib-tooling",
    '"py-lib-tooling @ git+https://github.com/betabitplus/py-lib-starter.git@v0.32.3#subdirectory=packages/py-lib-tooling",',
  ],
]);

assert.equal(config.customManagers.length, 2);
for (const manager of config.customManagers) {
  const depName = manager.depNameTemplate;
  const fixture = fixtures.get(depName);
  assert.ok(fixture, `unexpected dependency manager: ${depName}`);
  const regex = new RegExp(manager.matchStrings[0]);
  const match = fixture.match(regex);
  assert.ok(match, `${depName} fixture was not extracted`);
  assert.equal(match.groups.currentValue, "0.32.3");
  const updatedMatch = match[0].replace(match.groups.currentValue, "0.32.4");
  const updatedFixture = fixture.replace(match[0], updatedMatch);
  assert.match(updatedFixture, /@v0\.32\.4#/);
  assert.equal(updatedFixture.match(regex)?.groups.currentValue, "0.32.4");
}

const group = config.packageRules.find(
  (rule) => rule.groupName === "Shared Python Git packages",
);
assert.ok(group, "shared Git dependency group is missing");
assert.deepEqual(group.matchDepNames, ["py-lib-runtime", "py-lib-tooling"]);
assert.equal(group.matchPackageNames, undefined);
assert.equal(group.minimumGroupSize, 2);
assert.deepEqual(group.matchDatasources, ["github-tags"]);

console.log("downstream preset regression checks passed");
