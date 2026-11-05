---
name: Fix Windows Plaso Docker
overview: Empty Timesketch sketches happen because Plaso-in-Docker on Windows builds Linux paths with backslashes, so no `.plaso` file lands on the host mount and Timesketch upload fails. Fix path construction and fail loudly when output is missing.
todos:
  - id: posix-docker-paths
    content: Use posixpath.join for in-container paths in localplaso.py when use_docker=True
    status: completed
  - id: validate-plaso-output
    content: ModuleError if .plaso missing/empty after Docker/local run; cite plaso.log path
    status: completed
  - id: tests-docker-paths
    content: Assert Docker command uses forward-slash /data/output paths in localplaso tests
    status: completed
  - id: docs-windows-plaso
    content: Brief getting-started note on plaso_ts + Docker on Windows after fix
    status: completed
isProject: false
---

# Fix empty Timesketch sketch after `plaso_ts` on Windows

## What went wrong (your log)

```mermaid
sequenceDiagram
  participant FS as FilesystemCollector
  participant L2T as LocalPlasoProcessor
  participant Docker as plaso_container
  participant TS as TimesketchExporter

  FS->>L2T: File path E:\...\MOP_P
  L2T->>Docker: log2timeline ... --storage-file /data/output\b355....plaso
  Note over Docker: Linux sees invalid path; no file on host mount
  Docker-->>L2T: container exits (~13s)
  L2T->>TS: callback with expected C:\Temp\...\b355....plaso
  TS->>TS: add_file(.plaso)
  Note over TS: TypeError: file does not exist
  TS->>TS: Found 0 timelines; sketch 2 empty in UI
```

Evidence from your terminal:

- Command line shows **mixed separators**: `/data/output\b355d414....plaso` and `/data/output\plaso.log` ([`localplaso.py`](dftimewolf/lib/processors/localplaso.py) lines 142–166).
- Upload error: `File object ...\b355....plaso needs to be a file that exists.` — the path Timesketch uses is correct on the **host**, but Plaso never created that file.
- Sketch **2** was created (`New sketch created: 2`) but **`Found 0 timelines`** because import failed.
- dfTimewolf still prints **"Modules run successfully!"** despite the exporter callback error (misleading, separate from the root bug).

Root cause: when `use_docker` is true, container paths are built with `os.path.join('/data/output', ...)` on a **Windows** host. On Windows, `os.path.join` uses backslashes, producing paths that are wrong inside the Linux container, so the storage file is not written to the volume bound to `self._output_path`.

The debug line `...b355....plaso/Valetudo Xiomi Robot Vacuum MOP P` is only [`File.__str__`](dftimewolf/lib/containers/containers.py) combining `name` (source folder basename) + `path` (`.plaso`); [`TimesketchExporter`](dftimewolf/lib/exporters/timesketch.py) uses `container.path` for upload, which is the real issue (missing file).

## Fix (code)

**1. Use POSIX joins for all in-container paths** in [`dftimewolf/lib/processors/localplaso.py`](dftimewolf/lib/processors/localplaso.py):

- `import posixpath`
- When `_use_docker`, set:
  - `log_file_path = posixpath.join(plaso_output_dir, 'plaso.log')`
  - `plaso_output_path = posixpath.join(plaso_output_dir, plaso_output_file)`
  - Keep `plaso_storage_file_path = os.path.join(self._output_path, plaso_output_file)` (host path only).

**2. Validate Plaso output after the run** (same file):

- After `_DockerPlasoRun` / `_LocalPlasoRun`, if not `os.path.isfile(plaso_storage_file_path)` (or size is 0), `ModuleError` with:
  - expected host path
  - pointer to `os.path.join(self._output_path, 'plaso.log')` for diagnosis
- Prevents creating an empty sketch with no timeline and surfacing Plaso failures clearly.

**3. Tests** in [`tests/lib/processors/localplaso.py`](tests/lib/processors/localplaso.py):

- Extend `testProcessingDockerized` to assert the Docker `command` string contains `/data/output/` + forward slashes only (no `\` in `/data/...` segments).
- Optional: `@unittest.skipUnless(sys.platform == 'win32', ...)` test that `_processContainer` builds docker cmd with forward slashes when `use_docker=True` (can call internal method with mocked docker).

**4. Docs (short note)** in [`docs/getting-started.md`](docs/getting-started.md):

- Windows + `plaso_ts` uses Docker Plaso by default; after fix, normal flow works.
- Workaround if needed: install Plaso locally and set recipe `use_docker` to false (requires recipe edit or alternate recipe) — only mention if you expose that flag via CLI later (today it is hardcoded `true` in [`data/recipes/plaso_ts.json`](data/recipes/plaso_ts.json)).

## Verify after fix

Re-run your command:

```powershell
uv run dftimewolf plaso_ts "E:\Dropbox (Personal)\Hardware\Valetudo Xiomi Robot Vacuum MOP P" --incident_id 1338
```

Check:

- Log shows `--storage-file /data/output/<uuid>.plaso` (forward slashes only).
- Temp dir contains `<uuid>.plaso` on the host.
- Terminal: `Uploading timeline ...` without `needs to be a file that exists`.
- Sketch shows at least one timeline (may still be sparse if the folder has few parseable artifacts).

## Out of scope (optional follow-ups)

- Propagate callback failures so the recipe does not report success when Timesketch upload fails ([`module_runner.py`](dftimewolf/lib/modules/module_runner.py) callback handling).
- Pass `--timesketch_endpoint http://localhost/` on CLI so debug output does not show stale default `http://localhost:5000/` (your `.timesketchrc` still works).
