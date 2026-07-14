# Ready-made tool evaluation

This table records the candidates materially considered. Activity/maturity were checked against official documentation and upstream source in July 2026. Pinning means version, commit SHA or container digest as appropriate.

| Tool | Task / replacement | Maturity & license | Private/App support | Cross-platform / pinning | Operational cost / decision |
|---|---|---|---|---|---|
| Copier | generation, answers and three-way update | mature; MIT | private Git via ordinary credentials; no service | Python/Linux/macOS/Windows; pin package + template tag | low; **select** |
| Renovate Copier manager | template freshness PR | active Renovate manager; AGPL-3.0 self-host | GitHub App and private repositories | container; pin image digest | moderate scheduled job; **select** |
| Renovate git-submodules | component gitlink PR | active/beta manager | same App boundary | git/container; pin digest | low incremental; **select** |
| Renovate GitHub Actions | immutable action/reusable refs | mature manager | workflow mutation needs Workflows permission | pin SHA/digest | **select detection**, separate publisher for writes |
| Renovate shareable presets | central dependency policy | mature | private presets need authenticated repository read | JSON/JSON5 and pinned preset ref | low; **select**, reject if authentication proves noisier than local config |
| Renovate autodiscoverTopics | registry replacement | mature self-hosted feature | org filter + App selected repositories | server-side discovery | **select pending live matrix** |
| Renovate postUpgradeTasks | exact `uv lock` refresh | mature but privileged | self-hosted only; exact allowlist | command environment must be controlled | **select `^uv lock$` only** |
| GitHub reusable workflows | central CI | mature hosted feature | private sharing setting; GitHub token/App secrets | hosted Linux/macOS/Windows; exact SHA safest | low; **select** |
| GitHub rulesets | PR/check/tag policy | native GitHub | App bypass actors and expected check integration | hosted | **select for production**, blocked on current lab plan |
| GitHub auto-merge / merge queue | safe merge of existing PRs | native GitHub | repository policy/plan dependent | hosted | useful but does not create promotion PR |
| GitHub Apps | least-privilege identities | native GitHub | selected repositories and short-lived tokens | hosted | **select**, split roles |
| OpenTofu + GitHub provider | repositories/settings/branches/topics/rules | mature IaC; MPL-2.0 components | App/PAT; some admin resources need separate identity | CLI cross-platform; pin CLI/provider | low-to-moderate; **select** |
| Release Please | release PR/changelog/tag/release | mature; Apache-2.0 | private GitHub and App token | action pinned SHA | **select** with acceptance + SHA guard |
| import-linter | import contracts | mature; BSD-family | local source only | Python; version pin | **select** |
| Ruff | lint/private/tidy rules | mature; MIT | local source only | native binaries; pin | **select** |
| Pyright | static typing/private diagnostics | mature; MIT | local source only | Node/Python wrapper; pin | **select** |
| pytest | behavior/public import smoke | mature; MIT | local source only | cross-platform; pin | **select** |
| pre-commit | local/CI hook runner | mature; MIT | Git credentials for private hooks | cross-platform; immutable hook refs | **select optional** |
| pip-audit | dependency vulnerability audit | mature PyPA; Apache-2.0 | private index/auth supported by environment | Python; pin | **select** |
| radon | CC/MI metrics | established; MIT | local source | Python; pin | **select direct**, preserve stdout threshold semantics |
| flake8 cognitive-complexity | cognitive rule | small community plugin; permissive | local source | Python; pin | **select direct while fixtures prove value** |
| flake8 class-attributes-order | class ordering rule | small community plugin; permissive | local source | Python; pin | **select direct while policy remains desired** |
| validate-pyproject | pyproject schema | mature; MIT | local source | Python; pin | useful direct check; no wrapper |
| check-manifest | sdist/VCS contents | mature; MIT | local source | Python; pin | **select** |
| check-wheel-contents | wheel contents | mature; MIT | local artifacts | Python; pin | **select** |
| twine check | distribution metadata/rendering | mature PyPA; Apache-2.0 | local artifacts | Python; pin | **select** |
| actionlint | Actions syntax/static checks | mature; MIT | local workflow files | native binaries; pin release/SHA | **select**, live run pending |
| zizmor | GitHub Actions security audit | active; MIT | local workflow files | native/Python distribution; pin | **select**, live run pending |
| uv | lock/build/install/workspace | mature; dual Apache-2.0/MIT | private Git auth/index credentials | cross-platform; pin | **select** |
| Backstage | developer portal/onboarding | mature; Apache-2.0 | broad integrations | service/infrastructure | **reject** as disproportionate |

## Sources

- Copier documentation: https://copier.readthedocs.io/
- Renovate documentation and source: https://docs.renovatebot.com/ and https://github.com/renovatebot/renovate
- GitHub Actions/rulesets/App documentation: https://docs.github.com/
- OpenTofu documentation: https://opentofu.org/docs/
- GitHub provider source/docs: https://github.com/integrations/terraform-provider-github
- Release Please source/docs: https://github.com/googleapis/release-please-action
- Python tool documentation and license files in each named upstream repository.
