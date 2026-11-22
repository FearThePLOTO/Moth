# Moth

A MIPS assembler and step debugger. It shows the source line, the 32-bit machine word, and the register it changes in one view.

## Development

Requires Python 3.11+.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

On Windows, activate with `.venv\Scripts\activate`.

Run the tests and checks:

```sh
python -m pytest
ruff check .
ruff format --check .
```

CI runs the same checks on Ubuntu and Windows.

The UI dependency is optional:

```sh
python -m pip install -e ".[ui]"
```
