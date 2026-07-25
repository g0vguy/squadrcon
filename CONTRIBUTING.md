# Contributing

Pull requests are welcome.

## Setup

```bash
git clone https://github.com/g0vguy/squadrcon.git
cd squadrcon
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

## Linting

```bash
ruff check .
```

## Guidelines

- Keep the library dependency-free (standard library only).
- Add a test for any parser or protocol change.
- If you change a regex in `parsers.py`, include a sample raw line in
  the test that shows the format you're matching against.
- Open an issue first for anything beyond a small fix.
