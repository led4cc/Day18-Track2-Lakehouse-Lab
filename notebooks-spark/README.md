# Spark/Docker track

This track runs PySpark, Delta Lake, and MinIO in Docker. The four notebooks
live in this directory and use the `s3a://` paths backed by MinIO buckets.

## Prerequisites

- Docker Desktop 4+ is running.
- At least 8 GB of free RAM is available.
- Ports 8888, 9000, 9001, and 4040 are free.

## Run the lab

From the repository root:

```bash
make spark-up
make spark-smoke
```

If GNU Make is not installed on Windows, run the equivalent commands in
PowerShell:

```powershell
.\scripts\spark.ps1 up
.\scripts\spark.ps1 smoke
```

Open <http://localhost:8888/lab> and sign in with token `lakehouse`. Jupyter
opens this `notebooks-spark/` directory; the container synchronizes each
Jupytext `.py` notebook to `.ipynb` at startup.

Run the notebooks in this order:

1. `01_delta_basics.ipynb`
2. `02_optimize_zorder.ipynb`
3. `03_time_travel.ipynb`
4. Run `make spark-data` (or `.\scripts\spark.ps1 data`), then
   `04_medallion.ipynb`

Open the MinIO Console at <http://localhost:9001> with username and password
`minioadmin`. It contains the `lakehouse`, `bronze`, `silver`, and `gold`
buckets. Use it to capture evidence of a table's `_delta_log/` directory.

## Lifecycle and troubleshooting

- `make spark-down` stops containers and preserves MinIO data and dependency
  caches.
- `make spark-clean` stops containers and deletes those volumes; use it for a
  clean rerun.
- The PowerShell launcher accepts the same lifecycle actions: `up`, `smoke`,
  `data`, `down`, and `clean`.
- If `make spark-up` reports a port conflict, stop the process using that port
  before retrying.
- If the first startup is slow, Docker is downloading images and Spark's Maven
  dependencies. Later starts reuse the `ivy-cache` volume.

The expected checks are: schema enforcement and evolution (NB1), compaction and
Z-order (NB2), MERGE/time travel/RESTORE (NB3), and Bronze-to-Silver-to-Gold
LLM observability metrics (NB4).
