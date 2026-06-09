# The Architect’s Ledger: A Modular Systems Engineering Library

Welcome to **The Architect’s Ledger**.  
This repository functions as a monolithic, modular architectural catalog and engineering documentation library mapping practical data infrastructure layouts, microservice constraints, and technical design trade-offs.

Every step in this repository delivers:

- A complete, reproducible codebase  
- A detailed technical report tracking configuration parameters, operational failures, and internal database query execution plans  

---

## 🗺️ Systemic Roadmap & Project Matrix

This repository is organized:

- **Horizontally** across target industries  
- **Vertically** across storage, backend, and engineering abstraction layers  

### Unified Monorepo Architecture Map

```text
the-architects-ledger/
├── phase-1-storage-modeling/
│   ├── step-1-fintech-benchmark/      ──► [Step 1: FinTech Benchmark]      ──► (PostgreSQL vs ClickHouse)
│   └── step-2-retail-lakehouse/       ──► [Step 2: Retail Lakehouse]       ──► (dbt + DuckDB Serverless)
├── phase-2-backend-mastery/
│   ├── step-1-serialization-gateway/  ──► [Step 1: Serialization Gateway]  ──► (Async FastAPI / gRPC Gateway)
│   └── step-2-pooling-masking/        ──► [Step 2: Pooling & Masking]      ──► (Async pg Pool & Serving Filters)
├── phase-3-ai-engineering/            ──► [Semantic Metadata Search]       ──► (LangGraph / Vector DBs)
└── phase-4-product-devops/            ──► [The Analyst's OS (MVP)]         ──► (Distributed Topology)
```

---

### Phase & Artifact Matrix

| Phase        | Operational Sector     | Domain Focus                      | Engineering Artifact                    | Primary Documentation                                |
|-------------|------------------------|-----------------------------------|-----------------------------------------|------------------------------------------------------|
| Phase 1.1   | FinTech                | Disk I/O, Indexing Mechanics      | Multi-Engine Stress Test Suite          | PostgreSQL vs ClickHouse Storage Audit               |
| Phase 1.2   | Retail / E-Commerce    | Columnar Batch Processing         | Serverless Pseudo-Lakehouse             | dbt + DuckDB Local Transformation Specs              |
| Phase 2.1   | AI SaaS / Infra        | Asynchronous Gateway Pipelines    | High-Performance Data Router            | Network Serialization Gateway Audit                  |
| Phase 2.2   | AI SaaS / Infra        | Asynchronous Pool Allocation      | Transactional Routing Engine            | Designing a Low-Allocation Async Gateway             |
| Phase 3     | AI SaaS / Analytics    | State Machine Graph Networks      | Autonomous Self-Correcting SQL Graph    | LangGraph Dynamic Metadata Mapping                   |
| Phase 4     | Cross-Sector Enabler   | Orchestration, MLOps, Tracing     | The Analyst's OS Integrated MVP         | Blast Radius & Distributed Systems Specs             |

---

## ⚡ Phase 1.1: FinTech Storage Subsystem Internal Hardware Audit

- **Module Directory:** `phase-1-storage-modeling/step-1-fintech-benchmark/`  
- **Core Technical Publication:**  
  *Physical Storage Layouts and Indexing Mechanics Under Hardware Resource Isolation*

### Objective & Setup

This module implements a hardware-constrained stress test evaluating row-oriented layouts against columnar-oriented storage structures at a scale of **5,000,000** discrete records (≈ **400 MB** raw tuple payload).

To expose deep storage processing limitations, both engines were isolated via Linux kernel `cgroups` enforcing a hard resource ceiling:

- `cpus: '1.0'`
- `memory: 512M`

PostgreSQL 16 variables were restricted:

- `shared_buffers = 128MB`  
- `work_mem = 4MB`  
- `autovacuum = off`  

to isolate pure I/O metrics under resource starvation across a targeted range aggregation computed over **50 continuous iterations**.

### Verified Empirical Metrics

| Systemic Metric Category       | PostgreSQL 16 (B-Tree Layout) | PostgreSQL 16 (BRIN Heap Layout) | ClickHouse 24.3 (MergeTree Columnar) |
|--------------------------------|--------------------------------|-----------------------------------|--------------------------------------|
| Total Ingestion Duration       | 71.66 seconds                 | 63.72 seconds                    | 42.20 seconds                        |
| Write Amplification (WAF)      | 1.42x                         | 1.08x                            | 2.15x (during active merges)         |
| Post-Load Index Build Cost     | 0.00 seconds (Implicit PK)    | 1.6732 seconds                   | 0.00 seconds (Implicit MergeTree)    |
| Analytical Scan p50            | 1376.77 ms                    | 2.72 ms                          | 0.92 ms                              |
| Analytical Scan p95            | 1777.38 ms                    | 3.23 ms                          | 1.32 ms                              |
| Analytical Scan p99            | 1814.87 ms                    | 4.08 ms                          | 1.49 ms                              |
| Physical Disk Blocks           | 51,419 Blocks                 | 128 Blocks                       | Vectorized File Read                 |
| Physical Data Read Payload     | 401.71 MB                     | 1.00 MB                          | 0.24 MB                              |

### Core Engineering Realities & Production Warnings

**1. The Just-In-Time (JIT) Compilation Overhead**  
Lacking a secondary index tracking time vectors, the PostgreSQL B-Tree configuration triggered an unoptimized parallel sequential scan. Under resource starvation, PostgreSQL spent **1190.875 ms** purely in dynamic LLVM compilation before running execution paths, significantly inflating tail latency (p99: **1814.87 ms**).

**2. The Optimizer Paradox & Manual Compaction Limits**  
High-volume concurrent asynchronous ingestion heavily fragmented physical page layouts, causing the query planner to repeatedly ignore the BRIN index. A manual, synchronous `VACUUM FULL` was required post-load to defragment data pages and compress tuples monotonically via sequential UUIDv7 tokens, allowing a ~32 KB BRIN layout to execute chronological partition pruning and drop read times down to **2.72 ms**.

**3. The Production Lockout Risk**  
While `VACUUM FULL` successfully normalized the isolated lab setup, running this command inside a live production cluster introduces severe risk. It acquires an `AccessExclusiveLock`, completely freezing all concurrent incoming transactions and queries. For online, non-blocking page compaction at scale, enterprise environments must deploy alternative extensions like **pg_repack** or **pg_squeeze**.

---

## ⚡ Phase 1.2: Retail / E-Commerce Local Pseudo-Lakehouse Optimization

- **Module Directory:** `phase-1-storage-modeling/step-2-retail-lakehouse/`  
- **Core Technical Publication:**  
  *Dismantling the Cloud Data Warehouse Invoice: Building a Serverless, Local-First Pseudo-Lakehouse with dbt and DuckDB*

### Objective & Setup

This module profiles the operational efficiency of an in-process vectorized computing engine coupled with a local object storage abstraction layer.

- Target workload: classic star schema (orders, users, products)  
- Scale: **10,000,000** discrete records  
- Compression: Snappy into local disk directories mimicking a cloud data lake format  

Identical container throttling limits apply:

- `cpus: '1.0'`
- `memory: 512M`

The semantic data warehouse layer is orchestrated via **dbt Core**, which:

- Reads unindexed raw Parquet partitions  
- Builds analytical staging layers  
- Tracks multi-row user mutations via dbt snapshots (SCD Type 2)  
- Materializes physical dimensional marts  

### Verified Empirical Metrics

- **Raw Data Lake Serialization Duration:** 123.94 seconds (PyArrow streaming chunk execution)  
- **Total dbt Pipeline Compile & Run (`dbt run`):** 2.67 seconds  
- **Staging View Assembly Latency (`stg_orders`):** 0.20 seconds  
- **Dimension Table Materialization Latency (`dim_products`):** 0.24 seconds  
- **Analytical Fact Table Compilation Latency (`fct_orders`):** 2.06 seconds  
- **Global Analytical Scan (10M joins over lake):** 0.9352 seconds  
- **Directory-Pruned Analytical Scan (partition `month=03`):** 0.1119 seconds  

### Core Engineering Realities & Production Warnings

**1. The Global File-Locking Concurrency Wall**  
DuckDB achieves sub-second columnar aggregation speeds over millions of records because it processes blocks directly in-process, bypassing multi-layered client–server network serialization. However, when executing a write modification layer (`dbt run`), it acquires an **Exclusive Write Lock** over the database file footprint (`retail_lakehouse.db`). In a concurrent enterprise data engineering workspace, this topology triggers immediate `Database is locked` exceptions, defining the explicit architectural inflection point where migration to a distributed, decoupled multi-cluster cloud computing layer (Snowflake / Databricks) is forced.

**2. The Python Serialization Penalty**  
Attempting to process initial staging layers via dbt Python models wrapping PyArrow structures introduced severe data-copying and deserialization bottlenecks inside the restricted memory pool. Reverting the pipeline architecture to pure C++ vectorized SQL compilation (`stg_orders.sql`) dropped execution times down to **0.20 seconds** by enforcing reduced serialization and memory-copy overhead, maximizing CPU L1/L2 cache line locality.

---

## ⚡ Phase 2.1: Universal Data Gateway Network Serialization Audit

- **Module Directory:** `phase-2-backend-mastery/step-1-serialization-gateway/`  
- **Core Technical Publication:**  
  *Network Serialization Latency: Servicing 100,000 Rows Under Throttled Microservice Constraints*

### Objective & Setup

This module monitors the network serialization latency introduced when streaming large analytical extracts out of multi-engine data catalogs back to external services. Runtime parameters mirror the same resource-starved container sandbox:

- `cpus: '1.0'`
- `memory: 512M`

Instrumentation:

- **Memory footprints:** Python `tracemalloc` + Linux `cgroup` memory stats  
- **Thread execution & context switches:** `pidstat -w`  
- **Payload:** extraction of **100,000 wide rows** out of a **10,000,000** row grid via four distinct gateway endpoints  

Statistical variance (σ²) maps population variance over a **50-iteration** continuous client execution loop:

\[
\sigma^2 = \frac{1}{N} \sum_{i=1}^{N} (x_i - \mu)^2
\]

### Verified Empirical Metrics Matrix

| Target Endpoint Variant | Transport Architecture Style   | Server Lifecycle Status | Latency p50 | Latency p95 | Latency p99 | Variance (σ²)      |
|-------------------------|--------------------------------|-------------------------|------------:|------------:|------------:|--------------------:|
| TEST 1: REST Bulk       | Monolithic JSON Packet         | Crashed (HTTP 500)      |      —      |      —      |      —      | N/A (Memory Overrun) |
| TEST 2: gRPC Bulk       | Monolithic Binary Message      | Successful (Up)         | 319.16 ms   | 370.66 ms   | 413.56 ms   | 716.96 ms²          |
| TEST 3: REST Stream     | Chunked JSON Async Stream      | Successful (Up)         | 765.66 ms   | 934.41 ms   | 982.63 ms   | 3,659.18 ms²        |
| TEST 4: gRPC Stream     | Sequential Binary Stream       | Successful (Up)         | 16,703.44 ms| 18,932.23 ms| 19,518.28 ms| 822,277.87 ms²      |

### Core Engineering Realities & Production Warnings

**1. The Pydantic Allocation Boundary (REST Bulk Failure)**  
Forcing 100,000 rows through Pydantic `BaseModel` parsing raises the baseline memory signature from ~6.4MB (native C++ buffer) up to **700–850 bytes per object entry**. Under a 512MB container wall, this exhausts heap space, triggering a native Python `MemoryError` before network flushes occur.

**2. The Server Streaming gRPC Paradox (The 16-Second Bottleneck)**  
Yielding 100,000 row objects individually (`stream OrderRow`) inside a hard single-core constraint (`cpus: '1.0'`) creates massive thread context-switching overhead. The gRPC C-core layer is forced to generate independent HTTP/2 transport frames per row, locking Python’s async event loop and the Cython network layer into continuous state handshakes. This inflates statistical variance to **822,277.87 ms²**, proving that micro-batching or chunked frames are mandatory during gRPC streaming processing.

---

## ⚡ Phase 2.2: Universal Data Gateway Asynchronous Pooling Audit

- **Module Directory:** `phase-2-backend-mastery/step-2-pooling-masking/`  
- **Core Technical Publication:**  
  *Designing a Low-Allocation Async Gateway for Transactional Ledger Operations*

### Objective & Setup

This module monitors baseline connection stability and serialization-driven throughput capacity when exposing active operational relational infrastructure to multi-client internal networks.

- Gateway and PostgreSQL 16 cluster are isolated in separate containers:
  - `cpus: '1.0'`
  - `memory: 512M`

To preserve the **Separation of Concerns** principle, data format conformity is treated as an upstream ETL constraint, leaving the gateway focused on high-throughput streaming execution.

Benchmark:

- **40** concurrent asynchronous client lines  
- Each extracting **5,000 rows**  
- Total of **200,000 wide rows**  
- Connection pool capacity: `min_size=10, max_size=20`  

### Verified Empirical Metrics Matrix

- **Total Successful Transactions Processed:** 40 / 40 (0 Drops / 0 Block Failures)  
- **Total Wall Execution Time:** 2.6852 seconds  
- **Calculated Throughput:** 74,482 rows / second  
- **Latency p50 (Median):** 2,395.29 ms  
- **Latency p95 (Tail):** 2,667.12 ms  
- **Latency p99 (Peak Tail):** 2,671.62 ms  
- **Population Variance (σ²):** 120,564.05 ms²  
- **Post-Test Connection Pool Status:** `pool_free_slots: 20` (0 leaks)  

### Core Engineering Realities & Production Warnings

**1. The Implicit Context Handle Leak Boundary**  
Encapsulating connection handles inside implicit context managers (`async with pool.acquire()`) within asynchronous chunked generators forces the TCP socket to return to the pool immediately upon the first stream yield. This results in connection-closure exceptions as downstream pipes attempt subsequent chunk segments. Relational handles must be acquired explicitly and bounded within `try/finally` blocks to guarantee long-running network pipe stability.

**2. Serialization-Driven CPU Saturation**  
While reading raw database blocks over the Docker bridge network is inherently I/O-bound, the overall system bottleneck becomes CPU-bound during the serialization loop. Converting raw data frames into formatted JSON strings via `json.dumps()` under a single-core constraint (`cpus: '1.0'`) creates an intense thread scheduling run-queue inside the application container. This profile explains the latency baseline and shows that serialization dictates pipeline throughput long before physical disk reads saturate.

---

## 🛠️ Repository Operational Instructions

### Global Prerequisites

Ensure your host environment supports resource limitation features:

- Docker Compose v2.20+  
- Python 3.11+  
- `virtualenv` module  

---

### Deploying & Executing Phase 1.1 (FinTech Audit)

```bash
# Navigate to the target step boundary
cd phase-1-storage-modeling/step-1-fintech-benchmark/

# Boot the hardware-throttled containers
docker-compose up -d

# Initialize and activate the isolated virtual environment
python3 -m venv .venv
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the 5,000,000 row stress test routine
python benchmark.py
```

---

### Deploying & Executing Phase 1.2 (Retail Lakehouse)

```bash
cd phase-1-storage-modeling/step-2-retail-lakehouse/

python3 -m venv .venv
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

# Execute the 10,000,000 row streaming partitioning data generator
python generate_data.py

# Execute local dbt pipelines
cd dbt_project
dbt snapshot --profiles-dir .
dbt run --profiles-dir .
```

---

### Deploying & Executing Phase 2.1 (Serialization Gateway)

```bash
cd phase-2-backend-mastery/step-1-serialization-gateway/

# Compile Protobuf definitions and boot containers
docker-compose down
docker-compose up -d --build

# Local client virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install automated client drivers
pip install httpx numpy grpcio grpcio-tools

# Fire the 50-iteration benchmarking tool
python benchmark_client.py
```

---

### Deploying & Executing Phase 2.2 (Pooling & Masking Gateway)

```bash
cd phase-2-backend-mastery/step-2-pooling-masking/

# Build and start the container matrix
docker-compose up -d --build

# Local client virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install lightweight automated client tools
pip install -r client_requirements.txt

# Execute the asynchronous multi-client concurrency stress engine
python stress_pool_client.py
```

---

## 📄 License

This repository is distributed under the open-source **MIT License**.  
All infrastructure layouts, database configurations, and testing scripts are free for replication, system evaluation, and architectural analysis.

**Maintained by:** Oğuz Kaan Mavice  
