# Ternforge audit: promotion/release and exact-target Renovate routing

Date: 2026-07-23  
Scope: only the two validated directions listed below  
Baseline commit: `d9e92e645491b6d01c723af917b6f1909e7c2d9f`  
Baseline file SHA-256: `3769011ea0d40367159c7a3334b0958314611bc7e6ceea4d98cd787410c9b51f`  
Baseline changed by this audit: **no**

## 1. Scope

This pass independently re-audited only:

1. the `dev → main` promotion and release lifecycle;
2. event-driven exact-target Renovate routing with deterministic shards.

The audit checked four questions:

- whether every important contract has reproducible lab evidence;
- whether the baseline is internally consistent;
- whether the chosen mechanisms are standard or common rather than exotic;
- whether any check, custom code, test, or service can be removed without weakening a required invariant.

## 2. Executive conclusion

Both directions are architecturally sound and suitable for implementation.

The baseline contains no positive remnants of the rejected sync, ancestry, singleton-worker, deterministic-batch, or hard two-minute-SLO models. Markdown structure is valid, headings are unique, and all required contracts are present.

The solution is not a custom platform. It composes standard Git, GitHub Actions, GitHub rulesets, GitHub Apps, GitHub Releases, Release Please, and Renovate. The remaining custom surface is limited to policy that no hosted tool can infer from Ternforge's inventory and branch rules:

- one prospective merge-tree comparison;
- one small idempotent release identity guard;
- one source/profile/target router;
- one deterministic shard assignment;
- basic inventory validation.

No simpler native replacement was found that preserves all current requirements. Several alternatives remove a small amount of local logic only by adding broader permissions, more CI, privileged branch mutation, polling, unstable serialization, or a persistent control plane.

Four operational boundaries should be made explicit before implementation, but they do not change the architecture:

1. Release Please preparation must use a repository-scoped GitHub App token rather than the default `GITHUB_TOKEN`, so its PR triggers CI automatically without manual approval.
2. `actions/create-github-app-token` v3 should use `client-id`; `app-id` remains accepted but is deprecated.
3. release dispatch is at-least-once and duplicate-safe, not exactly-once;
4. native `queue: max` retains up to 100 pending runs per shard; queue age must be observed and nightly routing remains the recovery path after overflow or a lost event.

## 3. Promotion and release lifecycle

### 3.1 Standard mechanisms

The lifecycle uses common Git and GitHub building blocks:

```text
feature/release-preparation PR
→ squash merge into protected dev
→ full CI on exact dev SHA
→ dev-to-main promotion PR
→ read-only promotion guard
→ merge commit into protected main
→ tag and GitHub Release
```

Long-running integration and stable branches are a documented Git workflow. GitHub rulesets natively enforce pull requests, allowed merge methods, immutable tags, exact required-check contexts, and expected App sources. `git merge-tree --write-tree` is standard Git plumbing that computes a real merge result without mutating the index or worktree.

Release Please officially supports preparing a release PR while skipping tag and GitHub Release creation. GitHub CLI and GitHub Releases provide explicit tag targets, generated notes, label filtering, and idempotent readback.

### 3.2 Minimal custom policy

The promotion guard performs only four Ternforge-specific checks:

```text
same repository
source branch == dev
PR head SHA == current dev SHA
prospective merge tree(main, dev) == tree(dev)
```

The content check is one standard Git operation:

```bash
merge_tree="$(git merge-tree --write-tree --no-messages origin/main HEAD)"
dev_tree="$(git rev-parse 'HEAD^{tree}')"
test "$merge_tree" = "$dev_tree"
```

It does not rerun quality CI, create the PR, change branches, inspect patches, implement custom merge logic, or maintain state.

The publisher performs only release identity and idempotency checks:

```text
main has two parents
promoted SHA == main^2
tree(main) == tree(main^2)
version == Release Please manifest
tag and GitHub Release target == promoted SHA
```

It does not calculate versions, write changelogs, reconcile branches, or act as a release controller.

### 3.3 Why `main^2` is justified

Tagging the promoted `dev` commit is the only tested variant that simultaneously preserves:

- a normal merge-commit promotion PR;
- exact reuse of the SHA that passed full CI;
- no privileged `main → dev` synchronization;
- a previous release tag reachable from subsequent `dev` history, which Release Please needs to avoid repeating old changelog entries;
- a release tree identical to the visible `main` tree.

The rule is therefore a small Git-DAG adaptation, not a replacement for Git or Release Please:

```text
tag(vX.Y.Z) == main^2 == promoted dev SHA
tree(tag) == tree(main)
```

### 3.4 Rejected alternatives

The following alternatives were re-evaluated:

- **Tag the `main` merge commit.** Simpler superficially, but the tag is not in unsynchronized `dev` ancestry; the next Release Please run repeated earlier features in live testing.
- **Back-merge or fast-forward `main` into `dev`.** Restores tag ancestry but requires a privileged Sync App, ruleset bypass, branch mutation, special CI path, and more failure handling.
- **Fast-forward `main` directly to `dev`.** Removes the merge commit but bypasses the normal protected-PR merge lifecycle and requires a privileged ref update.
- **Use only one permanent branch.** Simpler but does not meet the accepted integration/stable separation.
- **Use GitHub merge queue.** Intended mainly for busy protected branches with high merge contention; it adds `merge_group` CI handling and does not remove the Ternforge-specific promotion provenance/content invariant.
- **Run full CI again on promotion.** Removes no policy logic, increases cost and latency, and validates a synthetic merge state rather than reusing the exact tested `dev` SHA.

No alternative is both simpler and equivalent under the current requirements.

### 3.5 Lab evidence

Existing final evidence already proves:

- squash-only `dev`;
- merge-only `main`;
- direct-push rejection;
- literal `ci / required` and `promotion / required` contexts;
- expected check source GitHub Actions App integration ID `15368`;
- repeated no-sync promotions;
- stale-head, non-`dev`, and conflict rejection;
- exact promoted-SHA publisher;
- idempotent rerun;
- generated-notes filtering;
- immutable tag rejection;
- wrong-tag fail-closed behavior.

Supplemental current-version preparation test:

```text
Repository:
  betabitplus-template-lab/sandbox-ternforge-release-dev-tag-20260723-r1

Release Please:
  v5.0.0
  45996ed1f6d02564a971a2fa1b5860e934307cf7

create-github-app-token:
  v3.2.0
  bcd2ba49218906704ab6c1aa796996da409d3eb1

Preparation run:
  30007044394 — success, 14 seconds

Created PR:
  #4 chore(dev): release 0.3.0
  bot actor
  label release-preparation

Automatic CI run:
  30007064032
  ci / required — success, 6 seconds
```

The token repository-set readback matched the single target repository. The App-created release PR triggered CI without manual approval. After preparation, neither `v0.3.0` tag nor `v0.3.0` GitHub Release existed, proving `skip-github-release` separation.

## 4. Exact-target Renovate routing

### 4.1 Standard mechanisms

The execution path uses supported Renovate and GitHub primitives:

```text
repository_dispatch
→ read committed inventory
→ source → profiles → exact targets
→ deterministic matrix of non-empty shards
→ explicit RENOVATE_REPOSITORIES list per process
→ repository-scoped GitHub App token
→ native GitHub Actions concurrency queue
→ Renovate PRs
```

Renovate self-hosting natively accepts an explicit list of multiple repositories. GitHub Actions natively supplies matrix fan-out and concurrency. GitHub App installation tokens natively support selecting an explicit repository list. Renovate shareable presets, configuration validation, built-in managers, PR creation, configuration-warning issues, and idempotent rescans remain responsible for dependency-update behavior.

### 4.2 Minimal custom policy

The custom router performs only the Ternforge-specific mapping that Renovate cannot know:

```text
released source
→ profiles declaring that direct source
→ repositories using those profiles
```

The shard function is deliberately simple:

```text
SHA-256(full_repository_name)[0:8] mod shard_count
```

It provides stable per-repository shard identity for overlapping cohorts. That stability matters because the native concurrency group serializes work by shard.

The router does not maintain a dependency graph, queue, scheduler, database, pending-event registry, worker state, or Renovate phase model.

### 4.3 Why not use a simpler alternative

- **Renovate autodiscovery.** Removes the explicit router but scans every repository visible to the credential, weakens exact targeting, and broadens permission scope.
- **One job per repository.** Easy to describe but repeats runner/image/token startup per repository, creates excessive jobs, and hits the 256-job matrix limit.
- **Sorted fixed-size chunks.** Simple for one event, but repository membership shifts when cohorts differ; the same repository can enter different concurrency groups and lose stable serialization.
- **Consistent hashing.** Reduces remapping when shard count changes, but shards contain no persistent state and shard-count changes are reviewed operational events. It adds implementation and test complexity without current benefit.
- **Custom queue/coalescing database.** Unnecessary because `queue: max`, idempotent Renovate scans, and nightly self-healing already cover normal overlap and recovery.
- **Polling-only Renovate.** Simpler dispatch topology but violates the accepted release-driven delivery requirement and can turn minute-scale updates into long polling delays.

The current modulo hash is the smallest deterministic mechanism that preserves stable concurrency identity.

### 4.4 Lab evidence

Real six-repository test:

```text
2 shards × 3 repositories
cold jobs: 75 and 79 seconds, including pinned image startup
all six PRs created within approximately 18 seconds of one another
```

Cold run:

```text
29960009677
```

Native queue test dispatched three events within seconds:

```text
29960130437
29960132010
29960133762
```

All three runs were preserved and completed sequentially per shard; no pending run was replaced.

Failure-isolation run:

```text
29960348634 — success
```

Concrete results:

- `sandbox-renovate-shard-02` PR #2 created;
- `sandbox-renovate-shard-04` PR #2 created;
- invalid `sandbox-renovate-shard-06` produced configuration-warning issue #2;
- the invalid repository did not fail the shard or block healthy repositories.

Repository-scope test:

```text
29999042911
```

Installation-token readback contained exactly one requested repository. A temporary Git ref write succeeded inside the scope and was rejected outside it.

Synthetic deterministic tests:

```text
1,000 repositories → 8 jobs, maximum 140 repositories/shard
5,000 repositories → 32 jobs, maximum 189 repositories/shard
```

Both remain below the 256-job matrix limit and the 500-repository installation-token selection limit.

## 5. Checks and tests: necessity review

### 5.1 Keep

The following checks protect different invariants and are not duplicates:

- **PR CI on `dev`:** validates the GitHub test merge before squash.
- **Push CI on `dev`:** publishes the successful check on the exact SHA later promoted.
- **Expected App source in rulesets:** native protection against a spoofed context name; no script required.
- **Exact current `dev` head:** closes the race where `dev` moves after a promotion PR starts.
- **Merge-tree equality:** rejects conflicts and hidden `main`-only content without rerunning product CI.
- **Publisher parent/tree/version/tag/release readback:** each check protects a different immutable release identity condition.
- **App repository-set readback:** detects accidental broad installation-token scope before a write-capable process starts.
- **Inventory schema, uniqueness, and deterministic fixtures:** cheap pure checks for the only custom routing logic.
- **Live scale acceptance after routing, credential, or concurrency changes:** verifies hosted-runner and API behavior that unit fixtures cannot predict.

### 5.2 Correctly absent

The design correctly avoids:

- full quality CI on promotion;
- branch synchronization acceptance;
- merge queue and `merge_group` CI;
- a custom merge implementation;
- a custom release controller;
- full fleet Renovate dry-run on every PR;
- one test job per managed repository;
- a custom queue, scheduler, database, or coalescing service;
- custom dependency extraction/lookup phases;
- custom JSON/YAML workflow parsers;
- permanent canary repositories.

No existing check can be removed without either losing a distinct invariant or moving responsibility into a larger custom controller.

## 6. Baseline consistency

Automated audit of baseline commit `d9e92e6` confirmed:

- balanced Markdown fences;
- unique headings;
- all agreed lifecycle and routing contracts present;
- old positive sync/ancestry/singleton/batch/hard-SLO contracts absent;
- no internal contradiction between detailed sections, acceptance, release section, implementation plan, and final model.

Three operational details are not yet explicit in the baseline text:

1. preparation PR credentials must be a repository-scoped App token;
2. dispatch semantics are at-least-once and duplicate-safe;
3. `queue: max` holds at most 100 pending runs per concurrency group, after which observability and nightly recovery are required.

These are documentation clarifications, not evidence failures or architectural blockers.

## 7. Official sources reviewed

The internet review was restricted to primary or official sources:

- Git branching workflows and `git merge-tree` documentation;
- GitHub rulesets, merge methods, merge queue, required-check App source, matrix limits, concurrency queue, GitHub Apps, Releases, and generated release notes;
- the official `googleapis/release-please-action` repository and Release Please documentation;
- official Renovate self-hosted configuration, repository-list, autodiscovery, and preset documentation;
- the official `actions/create-github-app-token` repository;
- the actionlint upstream issue/PR state for `queue: max` syntax support.

The review found no official feature that eliminates the merge-tree policy guard or exact-target router while preserving the accepted requirements. The only upstream tooling lag is actionlint recognition of `queue: max`; it justifies one narrow temporary lint exclusion, not custom queue logic.

## 8. Final verdict

```text
Promotion/release architecture: PASS
Exact-target Renovate architecture: PASS
Lab evidence completeness: PASS after supplemental App-token test and run snapshot
Baseline internal consistency: PASS
Standard/common mechanism test: PASS
Minimal custom surface test: PASS
Equivalent simpler native alternative found: NO
Unnecessary mandatory checks found: NO
Architectural blocker: 0
Baseline modified during audit: NO
```

The implementation plan should preserve the exact boundaries above and add no controller or generalized framework unless a new measured requirement appears.
