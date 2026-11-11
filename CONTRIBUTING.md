# Contributing

Issues and pull requests are welcome. Open an issue first for anything large, so we can agree the approach before you write it.

## Set up

You need [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just) and [podman](https://podman.io/). Then:

```bash
just deps      # pinned Python tools and the test collections
just lint      # yamllint, ansible-lint (production profile), zizmor
just test default rhel8
```

`just` on its own lists every recipe.

## Rules

- Every variable is in `defaults/main.yml`, `meta/argument_specs.yml` and the README variables table, with the same default and description in all three.
- Internal variables start with `__python_` and live in `vars/main.yml` or are registered in tasks.
- The bootstrap (`tasks/bootstrap.yml`, `tasks/push.yml`) runs before the host has a usable Python, so it may only use `raw`, `script`, and tasks that run on the control node (`set_fact`, `assert`, delegated tasks). Delegated tasks set `ansible_python_interpreter` to `ansible_playbook_python`.
- Use fully qualified module names, name every task, and keep `ansible-lint` on the production profile clean. A `noqa` needs a comment saying why.
- Tasks must be idempotent: `just test` runs an idempotence check on every platform.
- Never commit a real host name, internal URL or credential. Tests use public mirrors and throwaway users.
- Docs and comments are in British English.

## Commits and releases

Write commit subjects in the imperative, wrapped at 72 characters. Add an entry under Unreleased in `CHANGELOG.md`.

Maintainers release with `just release 1.2.3`, which tags and pushes. The Release workflow then creates the GitHub release and imports the tag into Galaxy.
