## DFTimewolf

A framework for orchestrating forensic collection, processing and data export.

dfTimewolf consists of collectors, processors and exporters (modules) that pass
data on to one another. How modules are orchestrated is defined in predefined
"recipes".

<p align="center">
  <img src="https://cloud.githubusercontent.com/assets/13300571/17257013/0065185c-5575-11e6-957d-5e662ec78d8c.png" width="300"/>
</p>

## Status
Github actions |  [Codecov](https://codecov.io/) | [CodeFactor](https://codefactor.io)
--- | --- | --
![Unit tests](https://github.com/log2timeline/dftimewolf/actions/workflows/unittests.yml/badge.svg) ![pylint checks](https://github.com/log2timeline/dftimewolf/actions/workflows/pylint.yml/badge.svg)  ![mypy checks](https://github.com/log2timeline/dftimewolf/actions/workflows/mypy.yml/badge.svg) ![Install](https://github.com/log2timeline/dftimewolf/actions/workflows/install.yml/badge.svg) | [![codecov](https://codecov.io/gh/log2timeline/dftimewolf/branch/main/graph/badge.svg)](https://codecov.io/gh/log2timeline/dftimewolf) | [![CodeFactor](https://www.codefactor.io/repository/github/log2timeline/dftimewolf/badge)](https://www.codefactor.io/repository/github/log2timeline/dftimewolf)

### Getting started

[Documentation](https://dftimewolf.readthedocs.io/en/dev/getting-started.html) is hosted on readthedocs.io.

### Run directly

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11–3.14.

```bash
cd dftimewolf
uv sync
uv run dftimewolf -h
```

Run a recipe (example: `plaso_ts`):

```bash
uv run dftimewolf plaso_ts /path/to/evidence --incident_id 12345
```

On Windows (PowerShell):

```powershell
cd dftimewolf
uv sync
uv run dftimewolf -h
uv run dftimewolf plaso_ts "C:\path\to\evidence" --incident_id 12345


uv run dftimewolf plaso_ts "H:\TEMP\Spike3DEnv_ExploreUpgrade\Spike3DWorkEnv\Spike3D\EXTERNAL" --incident_id 1339
```

Optional: install all dependency groups with `uv sync --all-groups`. To use the installed `dftimewolf` console script without `uv run`, activate `.venv` first (`.venv\Scripts\Activate.ps1` on Windows, `source .venv/bin/activate` on Unix).


### Building Docs

```ps1

uv sync
uv run python docs/generate_recipe_doc.py data/recipes docs
uv run mkdocs build
```