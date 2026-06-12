# Essemtec temperature plots

Interactive viewer for UT325F CSV temperature measurements. The application loads measurement data, plots available T1-T4 sensor curves, and lets the user calculate time ranges above selected temperature thresholds.

## Requirements

- Python 3.12 or newer
- Poetry 1.8 or newer
- Tk support in the selected Python installation

## Installation

```bash
poetry install
```

This installs the application package and all declared dependencies from `pyproject.toml`.

## Running

Open a file picker:

```bash
poetry run essemtec
```

Load a CSV file directly:

```bash
poetry run essemtec path/to/measurement.csv
```

For local development without installing the package, the same entry point is available as:

```bash
poetry run python scripts/essemtec.py path/to/measurement.csv
```

`PythonApplication1.py` is kept only as a compatibility wrapper for old IDE launch configurations.

## Project structure

- `src/essemtec/data_loader.py` - CSV parsing and temperature cleanup.
- `src/essemtec/thresholds.py` - threshold range calculations.
- `src/essemtec/app.py` - Matplotlib and Tk user interface.
- `src/essemtec/cli.py` - command line entry point.
- `tests/` - focused tests for non-GUI logic.

## Development workflow

Use GitFlow-style feature branches for reviewable work:

```bash
git switch development
git pull
git switch -c feature/<short-description>
```

Open pull requests into `development`. Keep `main` or `master` for tested release versions.

## Tests

```bash
poetry run pytest
```

The current tests cover CSV parsing and threshold calculations. GUI behavior should be covered separately if the application grows.

## Maintenance

Add runtime dependencies with:

```bash
poetry add <package>
```

Add development-only dependencies with:

```bash
poetry add --group dev <package>
```

Keep local virtual environments, caches, and generated build artifacts out of version control.
