# Contributing

This is a personal, educational-use project (see the [README
disclaimer](README.md)), but fixes and improvements are welcome.

## Before opening a PR

1. `hassfest` and HACS validation pass (see `.github/workflows/validate.yml`)
2. Code is linted: `ruff check .`

Run `pre-commit install` once to check both automatically on every commit,
or `pre-commit run --all-files` to check everything by hand.

## Scope

This integration only ever talks to a
[smartmeter-fetch](https://github.com/welworx/smartmeter-fetch) instance's
`/v1` HTTP API — it must not read a database, file, or grid operator portal
directly. If a change would require that, it belongs in smartmeter-fetch
instead.

## Reporting bugs / requesting features

Open a GitHub issue. For security issues, see [SECURITY.md](SECURITY.md)
instead of filing a public issue.
