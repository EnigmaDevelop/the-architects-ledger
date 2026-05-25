# The Architect’s Ledger: A Modular Systems Engineering Library

Welcome to **The Architect’s Ledger**. This repository functions as a monolithic, modular architectural catalog and engineering documentation library mapping practical data infrastructure layouts, microservice constraints, and technical design trade‑offs.

Every step in this repository delivers a complete, reproducible codebase alongside a detailed technical report tracking exact configuration parameters, operational failures, and internal database query execution plans.

---

## 🗺️ Systemic Roadmap & Project Matrix

This repository is organized horizontally across target industries and vertically across storage, backend, and engineering abstraction layers.

### Unified Monorepo Architecture Map

```text
the-architects-ledger/
├── phase-1-storage-modeling/ ──► [Step 1: FinTech Benchmark] ──► (PostgreSQL vs ClickHouse)
│   └── ► [Step 2: Retail Lakehouse] ──► (dbt + DuckDB Serverless)
├── phase-2-backend-mastery/ ──► [Universal Data Gateway] ──► (Async Fast-API / gRPC)
├── phase-3-ai-engineering/ ──► [Semantic Metadata Search] ──► (LangGraph / Vector DBs)
└── phase-4-product-devops/ ──► [The Analyst's OS (MVP)] ──► (Distributed Topology)
```

### Phase & Artifact Matrix

| Phase        | Operational Sector     | Domain Focus                    | Engineering Artifact                 | Primary Documentation                                   |
| :----------- | :--------------------- | :------------------------------ | :----------------------------------- | :----------------------------------------------------- |
| **Phase 1.1** | **FinTech**            | Disk I/O, Indexing Mechanics    | Multi‑Engine Stress Test Suite       | [PostgreSQL vs ClickHouse Storage Audit](#)            |
| **Phase 1.2** | **Retail / E‑Commerce** | Columnar Batch Processing       | Serverless S3 Pseudo‑Lakehouse       | [dbt + DuckDB Local Transformation Specs](#)           |
| **Phase 2**   | **AI SaaS / Infra**     | Asynchronous Gateway Pipelines  | High‑Performance Data Router         | [Async Database Connections & Serialization](#)         |
| **Phase 3**   | **AI SaaS / Analytics** | State Machine Graph Networks    | Autonomous Self‑Correcting SQL Graph | [LangGraph Dynamic Metadata Mapping](#)                |
| **Phase 4**   | **Cross‑Sector Enabler** | Orchestration, MLOps, Tracing   | The Analyst's OS Integrated MVP      | [Blast Radius & Distributed Systems Specs](#)          |

---

## ⚡ Phase 1.1: FinTech Storage Subsystem Internal Hardware Audit

- **Module Directory:** `phase-1-storage-modeling/step-1-fintech-benchmark/`  
- **Core Technical Publication:** *Physical Storage Layouts and Indexing Mechanics Under Hardware Resource Isolation*

### Objective & Setup

This module implements a hardware‑constrained stress test evaluating row‑oriented layouts against columnar‑oriented storage structures at a scale of **5,000,000 discrete records** (approx. 400 MB raw tuple payload).

To expose deep storage processing limitations, both engines were isolated via Linux kernel `cgroups` enforcing a hard resource ceiling:

- **Compute Allocation:** `cpus: '1.0'`  
- **Memory Allocation:** `memory: 512M`

PostgreSQL 16 was configured at initialization with targeted runtime variables to simulate a resource‑starved microservice container environment, while active background processes were deactivated to isolate pure I/O metrics:

- `shared_buffers = 128MB` — Restricting the volatile relational caching layer  
- `work_mem = 4MB` — Imposing strict session‑level limits on aggregation memory  
- `autovacuum = off` — Deactivated during write benchmarks to prevent automated background housekeeping noise

The benchmark executes a targeted range aggregation computing currency transaction distributions over a fixed **30‑second operational window** inside the 5,000,000 row heap. To calculate stable percentiles, the range aggregate query was run across **50 continuous iterations**.

### Verified Empirical Metrics

| Systemic Metric Category       | PostgreSQL 16 (B‑Tree Layout) | PostgreSQL 16 (BRIN Heap Layout) | ClickHouse 24.3 (MergeTree Columnar) |
| :---------------------------- | :----------------------------- | :-------------------------------- | :----------------------------------- |
| **Total Ingestion Duration**  | 71.66 seconds                  | 63.72 seconds                     | 42.20 seconds                        |
| **Write Amplification (WAF)** | 1.42x                          | 1.08x                             | 2.15x (During active merges)         |
| **Post‑Load Index Build Cost**| 0.00 seconds (Implicit PK)     | 1.6732 seconds                    | 0.00 seconds (Implicit MergeTree)    |
| **Analytical Scan p50**       | 1376.77 ms                     | 2.72 ms                           | 0.92 ms                              |
| **Analytical Scan p95**       | 1777.38 ms                     | 3.23 ms                           | 1.32 ms                              |
| **Analytical Scan p99**       | 1814.87 ms                     | 4.08 ms                           | 1.49 ms                              |
| **Physical Disk Blocks**      | 51,419 Blocks                  | 128 Blocks                        | Vectorized File Read                 |
| **Physical Data Read Payload**| **401.71 MB**                  | **1.00 MB**                       | **0.24 MB**                          |

---

### Core Engineering Realities & Production Warnings

1. **The Just‑In‑Time (JIT) Compilation Overhead**  
   Lacking a secondary index tracking time vectors, the PostgreSQL B‑Tree configuration triggered an un‑optimized parallel sequential scan. Under resource starvation, PostgreSQL spent an astronomical **1190.875 ms purely in dynamic LLVM compilation** before running execution paths, significantly inflating the tail latency (p99: `1814.87 ms`).

2. **The Optimizer Paradox & Manual Compaction Limits**  
   High‑volume concurrent asynchronous ingestion heavily fragmented physical page layouts, causing the query planner to repeatedly ignore the BRIN index. A manual, synchronous **`VACUUM FULL`** was required post‑load to defragment data pages and compress tuples monotonically via sequential **UUIDv7 tokens**, allowing a ~32 KB BRIN layout to execute chronological partition pruning and drop read times down to **`2.72 ms`**.

3. **The Production Lockout Risk**  
   While `VACUUM FULL` successfully normalized the isolated lab setup, running this command inside a live production cluster introduces severe risk. It acquires an **`AccessExclusiveLock`**, completely freezing all concurrent incoming transactions and queries. For online, non‑blocking page compaction at scale, enterprise environments must deploy alternative extensions like **`pg_repack`** or **`pg_squeeze`**.

---

## 🛠️ Repository Operational Instructions

### Global Prerequisites

Ensure your local host environment runs a modern Linux kernel or Docker Desktop installation with support for physical resource limitation features.

- Docker Compose `v2.20+`  
- Python `3.11+`  
- `virtualenv` module

### Deploying & Executing Phase 1.1 (FinTech Audit)

```bash
# Navigate to the target step boundary
cd phase-1-storage-modeling/step-1-fintech-benchmark/

# Boot the hardware-throttled containers
docker-compose up -d

# Initialize and activate the isolated virtual environment
python3 -m venv .venv
source .venv/bin/activate
# On Windows use:
# .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the 5,000,000 row stress test routine
python benchmark.py
```

---

## 📄 License

This repository is distributed under the open‑source **MIT License**. All infrastructure layouts, database configurations, and testing scripts are free for replication, system evaluation, and architectural analysis.

*Maintained by Oğuz Kaan Mavice.*