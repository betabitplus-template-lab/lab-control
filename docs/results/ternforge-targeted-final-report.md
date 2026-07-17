# Целевая проверка архитектуры Ternforge — финальный отчёт

Дата: 2026-07-17  
Production baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`  
Рабочая ветка отчёта: `betabitplus-template-lab/lab-control@experiment/ternforge-targeted-20260717`  
Bundle локального агента: `handoff-ternforge-live-final.zip`  
SHA-256 bundle: `1d39a1f9e8af91afd073b8a602edecaf5eaee32d981de96c04f2f75f80663785`

## 1. Объём проверки и качество evidence

Проверка выполнялась только в `betabitplus-template-lab`. Production baseline анализировался в detached, clean, read-only checkout. По отчёту локального агента и проверенной истории lab production mutations равны `0`.

Локальный агент выполнил все технически необходимые live-проверки: создал public sandbox-репозитории, установил Mend Renovate Community Cloud только на четыре выбранных r2-репозитория, выпустил теги, получил реальные Renovate PR, запустил Copier/uv/pre-commit/OpenTofu и выполнил отрицательные Git/ruleset тесты. Я дополнительно сверил через GitHub ключевые commits, PR diffs, авторство `renovate[bot]`, exact gitlinks, exact lock commits, CI runs и конечную OpenTofu-конфигурацию.

Есть два ограничения evidence-процесса:

1. Локальный агент продолжил работу с credential, имевшим `admin/push` как в lab, так и в production, хотя handoff требовал остановиться. Пользователь локально разрешил продолжение. Фактических production mutations не обнаружено, а Mend Renovate был установлен только на четыре sandbox-репозитория, но least-privilege граница не была технически обеспечена.
2. В bundle сокращены raw `tofu plan/apply` и negative-push outputs: `experiments/opentofu-rulesets/commands.log` содержит итоговую ссылку вместо полного transcript. Репозиторий, HCL, ruleset IDs, PR, branches, protected refs и итоговые состояния сохранены, но полнота raw CLI evidence ниже требуемой.

Поэтому архитектурные механизмы считаются подтверждёнными, а общий вердикт учитывает явные ограничения процедуры и traceability.

## 2. Авторитетная lab-цепочка

Второй, `r2`, набор репозиториев является авторитетным: первые sandbox-наборы сохранены как история неудачных immutable-release попыток, а не переписаны.

- Components:
  - `v0.1.0` → `fbaf8fede9ad66635bd5cb117a1ae17baa166e27`
  - `v0.2.0` → `cd784042d8b3a89066484530fda659c7aa861317`
  - untagged `main` → `a1a44465cbf6dd6a733a8dc9fc20dfd371205a30`
- Infra template:
  - `v0.1.0` → `eb1bad457712a42eb0d302c0f918fc0629300581`
  - `v0.2.0` → `352067a010e8ba32f988b4ed46e9dc40d31326b0`
- Python template:
  - `v0.1.0` → `0a1eed2…`
  - `v0.2.0` → `10e34a7…`
- Reusable CI:
  - `v0.1.0` → `0cf8ab57a6cc16d69ac38e49e10f9f3489ecee5c`
  - `v0.2.0` → `d4888afe533f5e9dae136f908c39827c9c2f3487`
- Tooling v0.2.0:
  - runtime → `a4fa84809aa9c5aced3c0a367b23fbcc7f5466d0`
  - policy → `d44737a0887c6bf5d8702d03221845c62e0fed4b`
  - testkit → `233ebec6a1106fd1b65b84803019494522338667`

## 3. Итоговая таблица

| Вопрос | Почему требовал проверки | Что было сделано | Evidence | Результат | Минимальное принятое решение | Нужен ли custom fallback |
|---|---|---|---|---|---|---|
| Responsibility-first components | Новая taxonomy и ownership не проверялись старым lab | Созданы `agents`, `repository`, `project/py`, `quality/py`, `delivery`; два final templates используют exact-SHA submodule | `sandbox-ternforge-components-20260717-r2`; tags `v0.1.0/v0.2.0`; template tags | **PASS** | Сохранить предложенную taxonomy без assembler/manifests/registry | Нет |
| Whole-file symlink, несколько `.agents/`, compound Jinja | Требовались три реальных способа композиции | `.editorconfig`/`.gitattributes` wired symlink; agent files из двух components; `pyproject.toml` включает несколько fragments | components commit `fbaf8fe…`; template commits; render acceptance | **PASS** | Один выходной путь — один владелец; compound file принадлежит final template | Нет |
| Отказ от `WIRING.json` | Старый lab сохранял ownership manifest | Render проверял broken links, leakage, duplicate ownership, TOML/YAML, modes и conflict markers без committed manifest | `experiments/composition`; `wiring_manifest_committed=false` | **PASS** | Не коммитить `WIRING.json`; ephemeral ownership report допустим только как CI evidence | Нет |
| `_components` и executable mode | Нужно исключить submodule из результата и сохранить executable helper | Render обоих tags, `find -L`, `git ls-files -s`, acceptance helper `100755` | `broken_symlinks=0`, `components_leakage=0`, mode `100755` | **PASS** | `_exclude` для `_components`; executable wrapper остаётся обычным executable template file/Jinja wrapper | Нет |
| Infra Copier ownership | README должен стать create-once, managed core — обновляться | v0.1→v0.2 с user README, unrelated file и non-overlapping managed edit; отдельный deleted-README case | `experiments/copier-infra`; relevant diff | **PASS** | README и user files не перезаписывать; удалённый README не восстанавливать | Нет |
| Python Copier ownership | Нужно доказать шесть user-owned областей и managed updates без trust | Изменены `src/tests/docs/examples/workbench/README`; обновлены workflow/pre-commit/release surfaces; clean frozen sync | `experiments/copier-py-library`; hosted PR #4 | **PASS** | `_skip_if_exists` только для явно user-owned paths; templates остаются declarative, без tasks/migrations/extensions | Нет |
| Явный managed-file conflict | Конфликт не должен маскироваться | Старый lab уже дал реальный conflict PR; новый clean case проверил отсутствие `.rej` и silent loss | inherited `sandbox-python-lib#3`; новый Copier evidence | **LAB-CONFIRMED** | Оставлять native Copier conflict markers и запрещать automerge | Нет |
| Hosted submodule update по release tag | Старый lab использовал другой Renovate execution model | Mend PR в обоих templates изменил только `.gitmodules` и gitlink `v0.1.0→v0.2.0`; untagged commit не выбран | template PR #1 в обоих r2 repos; green Template acceptance | **PASS** | `.gitmodules branch = vX.Y.Z` используется как Renovate version marker; version source истины — exact gitlink; никогда не использовать `git submodule update --remote` | Нет |
| `platformCommit` и symlinks | GitHub Trees API не принял intentional symlink | После `422 GitRPC::SymlinkDisallowed` включён стандартный `platformCommit: disabled`; hosted Git commit/push создал PR | infra template PR #1; Mend job; strict config validation | **CONDITIONAL** | Во всех symlink-bearing template repos явно ставить `platformCommit: disabled` | Нет; это стандартная Renovate опция |
| Hosted Copier updater | Нужны реальные Community Cloud PR без private token/trust | Mend обнаружил `.copier-answers.yml`, создал infra и Python PR; CI green; infra PR закрыт без merge | consumer-infra PR #1; consumer-py PR #4 | **PASS** | Mend Community Cloud — единственный template updater; automerge off | Нет |
| Reusable workflow exact SHA | Нужно проверить job-level `uses:` и workflow-file PR | Mend PR #1 поменял только caller SHA/comment `v0.1.0→v0.2.0`; reusable CI green | consumer-py PR #1; CI run `29608440386` | **PASS** | Thin caller с 40-char SHA и tag comment; Workflow Publisher App не нужен | Нет |
| Минимальный reusable CI | Требовалась конечная интеграция прямых команд | Ubuntu reusable job запускает `uv sync`, Ruff check/format, Pyright, pytest, build напрямую | infra-ci `python-library.yml@d4888a…`; green smoke consumers | **PASS** | Один representative workflow; pre-commit не заменяет прямые CI commands | Нет |
| Versioned Renovate preset | Нужно обновление pinned tag и strict validation | Mend PR #2 меняет только `#v0.1.0→#v0.2.0`; validator strict и CI green | consumer-py PR #2 | **PASS** | Preset хранится в `infra-updates`, pinned по tag, без зависимости от `main` | Нет |
| `tool.uv.sources` Git tags | Документация не гарантировала built-in update | Built-in `pep621` сгруппировал runtime/policy/testkit, обновил tags и exact commits в `uv.lock` | consumer-py PR #6; exact lock SHAs; CI/pre-commit green | **PASS** | Использовать built-in PEP 621; groupName для атомарного split-tooling update | Нет; regex не нужен |
| Pre-commit revisions | Manager beta/opt-in | Mend PR #5 изменил только Ruff hook rev; local `pre-commit run --all-files` и hosted check green | consumer-py PR #5 | **PASS** | Включить Renovate pre-commit manager только для выбранных hooks | Нет |
| Standalone runtime | Старый runtime жил внутри monorepo | Отдельный repo, 44 tests, standalone sync/build, runtime deps только product deps | runtime r2 tags; `pyproject.toml`; tooling evidence | **PASS** | `ternforge-tooling-py-runtime` — обычная product library, независимая от policy/testkit | Нет |
| Standalone policy | Minimal checker ранее был только experiment | Отдельный stdlib-only package, 8 tests/build, один CLI, no generic wrappers | policy r2 tags; `pyproject.toml` | **PASS** | Сохранить только Ternforge-specific policy checker | Нет |
| Standalone testkit | DEFER helpers нужно было реально извлечь | Отдельный package с VCR, console, image, e2e, setup/path helpers; 7 representative tests/build | testkit r2 tags; initial extraction commit `c33a8fe…` | **PASS** | `testkit → runtime` разрешён только для реально нужных helpers; policy dependency отсутствует | Нет |
| Representative frozen consumer | Нужны три отдельные tagged repos и exact lock | runtime в project deps, policy в dev, testkit в test; frozen sync и tests; hosted grouped update | consumer-py main и PR #6 | **PASS** | Git tags + `uv.lock` exact commits; не публиковать в PyPI | Нет |
| OpenTofu bootstrap order | Старый fixture не соответствовал public/approval-zero target | Двухфазно создан repo, branches/check, затем один branch ruleset и один tag ruleset; PR #1/#2 merged | repository-control HCL; controlled repo PR #1/#2; ruleset IDs `19116413/19116415` | **CONDITIONAL** | Использовать OpenTofu 1.12.x + provider 6.13.0, rulesets off до появления check; затем enable | Нет; raw CLI transcript в bundle неполон |
| Branch/tag enforcement | Нужны реальные negative tests и no-drift | Агент зафиксировал блокировку direct/force/delete, immutable tag, zero-approval PR, repeat plan и disable/re-enable | `experiments/opentofu-rulesets`; protected branches/tags; merged PRs | **CONDITIONAL** | Один ruleset на `dev/main`; отдельный `v*`; `dev→main` — convention, не source restriction | Нет |
| Targeted rollback | Нужно проверить только новые рискованные цепочки | Gitlink rollback, Copier PR close, caller SHA rollback, Git tags+lock rollback, ruleset disable/re-enable | `experiments/rollbacks`; commits и PR #1 closed/unmerged | **PASS** | Rollback выполняется локально в одном repo/PR/IaC apply, без fleet control plane | Нет |
| Production isolation процесса | Требовалась строгая read-only граница | Production checkout detached/clean, mutations `0`; но активный credential имел production admin/push | `security/credential-boundary.json`, security log | **CONDITIONAL** | До реального Ternforge rollout обязательно использовать отдельный selected-repository App/token без production write | Нет custom software; нужна правильная credential configuration |

## 4. Карта старой функциональности → runtime / policy / testkit / удаление

### Runtime

Весь продуктовый namespace frozen baseline:

```text
packages/py-lib-runtime/src/py_lib_runtime/**
→ ternforge-tooling-py-runtime/src/py_lib_runtime/**
```

Сюда относятся публичные и private implementation APIs для cache, config, logging, previews, validation и типов. Они остаются ordinary runtime product code. Generic CI, release и template lifecycle не входят в runtime.

### Policy

Старые organization-specific structural rules:

```text
py_lib_tooling/_internal/project_structure_policy/common.py
py_lib_tooling/_internal/project_structure_policy/docs.py
py_lib_tooling/_internal/project_structure_policy/examples.py
py_lib_tooling/_internal/project_structure_policy/project.py
py_lib_tooling/_internal/project_structure_policy/root_entrypoint.py
py_lib_tooling/_internal/project_structure_policy/workbench.py
→ один standalone py-lib-policy checker
```

Он сохраняет только правила, которые не выражаются стандартными Ruff/Pyright/import-linter/pytest средствами: facade/root-init shape, console-script boundary, literal dynamic private imports, `# %%` examples и обязательный skeleton.

### Testkit

Точное перенесение helper families:

```text
py_lib_tooling/_api/test_support.py
→ py_lib_testkit/_api/test_support.py

py_lib_tooling/_internal/test_support/_console_appearance.py
→ py_lib_testkit/_internal/test_support/_console_appearance.py

py_lib_tooling/_internal/test_support/_vcr_shared.py
→ py_lib_testkit/_internal/test_support/_vcr_shared.py

py_lib_tooling/_internal/test_support/console.py
→ py_lib_testkit/_internal/test_support/console.py

py_lib_tooling/_internal/test_support/e2e_vcr_guard.py
→ py_lib_testkit/_internal/test_support/e2e_vcr_guard.py

py_lib_tooling/_internal/test_support/images.py
→ py_lib_testkit/_internal/test_support/images.py

py_lib_tooling/_internal/test_support/paths.py
→ py_lib_testkit/_internal/test_support/paths.py

py_lib_tooling/_internal/test_support/setup.py
→ py_lib_testkit/_internal/test_support/setup.py

py_lib_tooling/_internal/test_support/vcr_matchers.py
→ py_lib_testkit/_internal/test_support/vcr_matchers.py
```

Namespace переименован в `py_lib_testkit`; конфигурационный доступ к старому monorepo root заменён небольшим standalone repo-root/TOML boundary. Testkit может зависеть от runtime как от обычной runtime dependency; policy не является его dependency.

### Удаляется или заменяется стандартными инструментами

Удаляются как собственный framework:

- template assembler, manifests, committed builds и component registry;
- template answer/check/update wrappers и lock orchestration;
- downstream/fleet registry, doctor/synchronizer и central API;
- generic Ruff/Pyright/pytest/import-linter/uv/radon/pip-audit/build wrappers;
- custom workflow updater, Workflow Publisher App и Renovate phase controller;
- promotion guard и постоянный canary fleet.

Стандартные команды и hosted tools вызываются напрямую.

## 5. Проверка целевой topology

Подтверждён рабочий состав:

```text
ternforge-template-components
ternforge-template-infra-repository
ternforge-template-py-library

ternforge-infra-repository-control
ternforge-infra-ci
ternforge-infra-updates

ternforge-tooling-py-runtime
ternforge-tooling-py-policy
ternforge-tooling-py-testkit
```

Для каждого создаваемого repository остаётся один конечный Copier template, один `copier.yml`, один answers file и одна update chain. Постоянные canary repositories не требуются.

## A. Подтверждённая архитектура

Можно переносить в план Ternforge без дополнительных архитектурных экспериментов:

1. Responsibility-first components repository с предложенной taxonomy и exact-SHA submodule `template/_components`.
2. Final templates без assembler, manifests, committed builds, registry, graph и `WIRING.json`.
3. Whole-file symlinks, несколько component-owned agent paths и final-template-owned compound Jinja files при строгом one-owner rule.
4. Declarative Copier ownership: `_skip_if_exists` только для create-once/user-owned paths; managed config обновляется обычным three-way update; tasks/migrations/extensions отсутствуют до реальной необходимости.
5. Mend Renovate Community Cloud как единственный updater, selected repositories, automerge off.
6. Built-in managers: `git-submodules`, `copier`, `github-actions`, `pep621`, `pre-commit`; custom regex для uv Git tags не нужен.
7. Reusable CI в отдельном `infra-ci`, caller pinned exact SHA + tag comment.
8. Tagged Renovate presets в `infra-updates`.
9. Standalone runtime, policy и testkit с направлением dependency `consumer → runtime`, dev/test groups → policy/testkit и допустимым `testkit → runtime`.
10. Public repository-control через двухфазный OpenTofu bootstrap, один branch ruleset для `dev/main`, отдельный immutable tag ruleset.
11. Rollback отдельной цепочки выполняется одним gitlink/caller/tag+lock/IaC изменением или закрытием PR; custom control plane не нужен.

## B. Изменения baseline

По результатам проверки baseline нужно изменить только так:

1. Для template repositories с symlinks явно добавить стандартное Renovate setting:

   ```json
   { "platformCommit": "disabled" }
   ```

   Иначе GitHub Trees API может отклонить commit с `GitRPC::SymlinkDisallowed`.
2. Считать `.gitmodules branch = vX.Y.Z` только Renovate version marker. Обычный `git submodule update --remote` запрещён архитектурной convention; checkout всегда использует committed exact gitlink.
3. Не добавлять uv regex manager: built-in PEP 621 корректно обновляет Git `tag` и `uv.lock`.
4. Не возвращать Workflow Publisher App: hosted Renovate обновляет job-level reusable workflow SHA обычным PR.
5. Не коммитить `WIRING.json`: one-owner design + render acceptance достаточны.
6. Старое объединение runtime/tooling заменить тремя standalone repositories: runtime, minimal policy, testkit.
7. OpenTofu pin обновить с старого lab `6.6.0` на проверенный GitHub provider `6.13.0`; rulesets включать только после успешного required check.
8. Перед реальной Ternforge реализацией заменить broad operator credential на отдельный least-privilege selected-repository App/token.

## C. Нерешённые блокеры

Архитектурных или продуктовых блокеров, мешающих начать планирование Ternforge, не обнаружено.

Остаются два обязательных rollout-условия:

1. credential boundary должна быть технической, а не только процедурной: production write/admin исключается самим App installation/repository selection;
2. при production pilot нужно сохранить полный raw transcript `tofu plan/apply` и отрицательных Git operations, поскольку текущий bundle содержит итоговые состояния, но не весь запрошенный CLI output.

Они не требуют нового framework или изменения целевой topology.

## D. Вердикт

# READY WITH EXPLICIT LIMITATIONS

Целевая архитектура функционально подтверждена и готова к переносу в детальный план Ternforge. Дополнительные архитектурные эксперименты не нужны. До начала реальных mutations необходимо обеспечить least-privilege credential boundary и повторно сохранить полный OpenTofu/negative-test transcript на первом production-like pilot.
