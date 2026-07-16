# Ready-made tool evaluation

This table records the candidates materially considered. Activity/maturity were checked against official documentation and upstream source in July 2026. Pinning means version, commit SHA or container digest as appropriate. Handoff-02 added private live execution for the selected delivery tools.

| Tool | Task / replacement | Maturity & license | Private/App support | Cross-platform / pinning | Operational cost / decision |
|---|---|---|---|---|---|
| Copier 9.16.0 | generation, answers and three-way update | mature; MIT | private Git works with scoped credential propagation to independent temporary clone | Python/Linux/macOS/Windows; template tags immutable | low; **select**, legacy-answer compatibility fix awaiting handoff-03 |
| Renovate Copier manager 43.262.4 | template freshness PR | active Renovate manager; AGPL-3.0 self-host | live private App/preset test passed | digest `sha256:2c2f2dc64e0c4ef0d4c9f5795877004ee9667eb3d3f1125ebb1dc503aeeae8fe` | moderate scheduled job; **select** |
| Renovate git-submodules | component gitlink PR | active/beta manager | live private component PR path passed | same digest-pinned controller | low incremental; **select** |
| Renovate GitHub Actions | immutable action/reusable refs | mature manager | detection works; workflow mutation needs Workflows permission | pin exact SHA | **select detection**, separate publisher for writes |
| Renovate shareable presets | central dependency policy | mature | private preset authentication passed live | versioned automation repository | low; **select** |
| Renovate `autodiscoverTopics` | registry replacement | mature self-hosted feature | org/topic/disabled matrix passed live | server-side discovery + selected repositories | **select** |
| Renovate regex custom manager | PEP 508 Git runtime/tooling refs | mature extension mechanism | reads public tags, writes only selected lab repos | constrained regex and semver template | **select pending bounded live K06 rerun** |
| Renovate `postUpgradeTasks` | exact `uv lock` refresh | mature but privileged | root/nested private Git lock regeneration passed | scripts disabled; exact command only | **select `uv lock` only** |
| GitHub reusable workflows | central CI | mature hosted feature | private organization sharing and exact-SHA caller passed | Linux/macOS and tagged/exact refs exercised | low; **select** |
| GitHub rulesets | PR/check/tag policy | native GitHub | App bypass supported, but private lab endpoints return plan HTTP 403 | hosted | **select for production**, externally blocked in current lab |
| GitHub auto-merge / merge queue | safe merge of existing PRs | native GitHub | repository policy/plan dependent | hosted | useful but does not create promotion PR; automerge kept false |
| GitHub Apps | least-privilege identities | native GitHub | selected repositories, short-lived tokens and negative access test passed | hosted | **select**, split roles |
| OpenTofu 1.12.0 + GitHub provider 6.6.0 | repositories/settings/branches/topics/rules | mature IaC; MPL-2.0 components | environment token; provider schema validated after correction | CLI cross-platform; exact pins | **select**, full two-phase apply/no-drift awaiting handoff-03 |
| Release Please action 5.0.0 | release PR/changelog/tag/release | mature; Apache-2.0 | private App-token releases v0.4.0/v0.4.1 passed | action pinned SHA | **select** with acceptance + API exact-SHA guard |
| import-linter | import contracts | mature; BSD-family | local source only | Python; version pin | **select** |
| Ruff | lint/private/tidy rules | mature; MIT | local source only | native binaries; pin | **select** |
| Pyright | static typing/private diagnostics | mature; MIT | local source only | Node/Python wrapper; pin | **select** |
| pytest | behavior/public import smoke | mature; MIT | local source only | cross-platform; pin | **select** |
| pre-commit | local/CI hook runner | mature; MIT | Git credentials for private hooks | cross-platform; immutable hook refs | **select optional** |
| pip-audit | dependency vulnerability audit | mature PyPA; Apache-2.0 | private index/auth supported by environment | Python; pin | **select** |
| radon | CC/MI metrics | established; MIT | local source | Python; pin | **select direct**, live parity passed |
| flake8 cognitive-complexity | cognitive rule | small community plugin; permissive | local source | Python; pin | **select direct**, fixture parity passed |
| flake8 class-attributes-order | class ordering rule | small community plugin; permissive | local source | Python; pin | **select direct**, fixture parity passed |
| validate-pyproject | pyproject schema | mature; MIT | local source | Python; pin | useful direct check; no wrapper |
| check-manifest | sdist/VCS contents | mature; MIT | local source | Python; pin | **select**, exact Copier answers ignore required |
| check-wheel-contents 0.6.3 | wheel contents | mature; MIT | local artifacts | pinned ephemeral `uvx` | **select** |
| twine 6.2.0 | distribution metadata/rendering | mature PyPA; Apache-2.0 | local artifacts | pinned ephemeral `uvx` | **select** |
| actionlint 1.7.12 | Actions syntax/static checks | mature; MIT | local workflow files | native binary and release attestation | **select**, reusable set passed; corrected workflow subset awaiting handoff-03 |
| zizmor 1.27.0 | GitHub Actions security audit | active; MIT | local workflow files | offline/pedantic mode | **select**, reusable set and corrected primary audit passed |
| uv 0.8.17 | lock/build/install/workspace | mature; dual Apache-2.0/MIT | private Git auth exercised | cross-platform; pin | **select** |
| Backstage | developer portal/onboarding | mature; Apache-2.0 | broad integrations | service/infrastructure | **reject** as disproportionate |

## Evidence effects

Handoff-02 changed several decisions from “static candidate” to live-selected:

- private reusable workflows and private shareable Renovate presets work;
- topic-based discovery is sufficient for the lab fleet;
- Release Please owns real release lines;
- exact `uv lock` owns root/nested lock refresh;
- direct quality tools preserve old rule behavior;
- selected-repository credentials enforce the components-read boundary.

It did not justify introducing Backstage, a new platform service, a manifest engine, persistent PATs or compatibility wrappers.

## Primary sources

- Copier documentation and source;
- Renovate documentation/source and the pinned live image;
- GitHub Actions, rulesets and App documentation;
- OpenTofu documentation and GitHub provider 6.6.0 schema;
- Release Please action source/docs;
- official documentation/license/source for each selected Python quality/package tool.
