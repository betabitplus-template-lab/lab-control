# Ternforge — финальный отчёт после evidence closure

Дата: 2026-07-18  
Production baseline: `betabitplus/py-lib-starter@d59582375855cff69fb165e467dc5847bc75ca99`  
Production mutations: `0`

Основной live bundle SHA-256: `1d39a1f9e8af91afd073b8a602edecaf5eaee32d981de96c04f2f75f80663785`  
Closure bundle SHA-256: `5bd24f74838c2055e886896fce47cb8e7aa378577164978905347c5e37ec5173`

Предыдущая версия этого файла зафиксировала полный r2 experiment matrix. Настоящая версия включает последующий r3 evidence closure и является итоговой.

## Проверка closure

- Отдельный fine-grained credential ограничен resource owner `betabitplus-template-lab`.
- Lab administration endpoint: HTTP 200.
- Production administration endpoint для `betabitplus/py-lib-starter`: HTTP 403.
- Production write probe не выполнялся.
- `commands.log` содержит 57 command blocks с command/stdout/stderr/exit code/UTC timestamps.
- Сохранены OpenTofu phase 1/2/3, ruleset disable/re-enable, negative Git tests и два финальных no-drift plan с exit code 0.
- JSON files валидны; secret-pattern scan не нашёл секретов.
- r3 control commit: `96d2a7b0dccb3befc81723b81e2500d653338f43`.
- Zero-approval PR #1 merged в `dev`; required-check run `29615656908` успешен.
- Final rulesets: branch `19124611`, tag `19124609`.

Независимая GitHub-проверка подтвердила public r3 repositories, OpenTofu HCL, merged PR и успешный `repository-ci`.

## Итоговая матрица

| Область | Результат | Принятое решение | Fallback |
|---|---|---|---|
| Components/composition | PASS | Responsibility-first taxonomy, exact-SHA submodule, no assembler/`WIRING.json` | Нет |
| Copier ownership/conflicts | PASS | Declarative ownership, explicit create-once paths, native conflicts | Нет |
| Renovate submodule/Copier | PASS | Mend Community Cloud, automerge off | Нет |
| Symlink template commits | PASS WITH REQUIRED SETTING | `platformCommit: disabled` | Стандартная настройка |
| Reusable CI/presets | PASS | Exact workflow SHA; tagged preset | Нет |
| uv Git tags/lock | PASS | Built-in PEP 621; grouped tags and exact `uv.lock` | Regex не нужен |
| Pre-commit | PASS | Built-in manager for selected hooks | Нет |
| Runtime/policy/testkit split | PASS | Три standalone repositories | Нет |
| OpenTofu bootstrap/rulesets | PASS | Provider `6.13.0`; rulesets after successful check | Нет |
| Negative enforcement/no-drift | PASS | Direct/force/delete/tag mutations blocked; IaC disable/re-enable | Нет |
| Production isolation | PASS | Отдельный lab/Ternforge-scoped credential | Нет |
| Targeted rollback | PASS | Локальные git/IaC rollback paths | Нет |

## A. Подтверждённая архитектура

Подтверждены final Copier templates без собственного control plane, exact-SHA components, Mend Community Cloud, built-in managers, thin exact-SHA reusable CI callers, tagged presets, standalone runtime/policy/testkit, двухфазный OpenTofu bootstrap и локальные rollback paths.

## B. Изменения baseline

1. Для symlink-bearing templates задать `platformCommit: disabled`.
2. `.gitmodules branch = vX.Y.Z` использовать только как Renovate marker; release определяется committed gitlink.
3. Использовать built-in PEP 621 без uv regex manager.
4. Не возвращать Workflow Publisher App и custom updater.
5. Не коммитить `WIRING.json`.
6. Разделить runtime, policy и testkit.
7. Pin GitHub provider `6.13.0`; включать rulesets после появления required check.
8. Для implementation использовать credential без доступа к production baseline.

## C. Нерешённые блокеры

Нерешённых архитектурных, продуктовых или evidence-блокеров нет. Обычные implementation review, rollout sequencing и secret handling не являются незакрытыми вопросами этой проверки.

## D. Вердикт

# READY TO PLAN TERNFORGE

Все NEEDS-EXPERIMENT вопросы закрыты. Дополнительный локальный прогон не требуется. Следующий этап — детальное планирование Ternforge; реализация в рамках проверки не начиналась.
