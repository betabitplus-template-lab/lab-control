# RTK - Rust Token Killer (Codex CLI)

**Usage**: Token-optimized CLI proxy for shell commands.

## Rule

Prefer `rtk` when it preserves the command's runtime semantics.

For interpreter- or env-sensitive Python commands, prefer `rtk proxy uv run ...`
or plain `uv run ...`.

Examples:

```bash
rtk git status
rtk cargo test
rtk npm run build
rtk proxy uv run pytest -q
```

## Meta Commands

```bash
rtk gain            # Token savings analytics
rtk gain --history  # Recent command savings history
rtk proxy <cmd>     # Run raw command without filtering or runtime changes
```

## Verification

```bash
rtk --version
rtk gain
which rtk
```
