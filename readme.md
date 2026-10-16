# 🎮 ByteBattle Backend - Advanced Load-Testing & Fault Line Benchmarking

An empirical systems engineering case study documenting load-testing bottlenecks, currency lock optimizations, and structural worker failures of a high-concurrency university quiz application designed with **FastAPI**, **SQLAlchemy ORM**, and **APScheduler**.

## 📊 Performance Engineering Benchmarks & Latency Matrix

Below is the structured data-driven latency profile captured under increasing concurrent user volumes using the **Locust** distributed load testing toolkit. 

Authentication layers dynamically synchronized with the application's underlying cryptographic signing protocols (`HS256` utilizing the application's runtime variables via `.env` injection).

| Performance Metric | Phase 1 (5 Users) | Phase 2 (30 Users) | Phase 3 (100 Users) | Phase 4 (200 Users) | Phase 5 (Peak 500+ Users) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Total Processed Requests** | ~300 | 3,050 | 11,531 | 20,007 | **3,420+ (Aggregated Test)** |
| **Simultaneous Active Swarm** | 5 Users | 30 Users | 100 Users | 200 Users | **500+ Distributed Users** |
| **Median Response Time (50%ile)**| 10 ms | 12 ms | 16 ms | 990 ms | **2,100 ms (2.1 Seconds)** |
| **95th Percentile Latency (95%ile)**| 39 ms | 140 ms | 1,500 ms | 3,100 ms | **2,418 ms** |
| **99th Percentile Latency (99%ile)**| 2,100 ms | 2,100 ms | 2,100 ms | 4,000 ms | **10,929 ms (10.9 Seconds)** |
| **Maximum System Latency** | 2,350 ms | 2,366 ms | 4,663 ms | 5,949 ms | **12,179 ms (12.1 Seconds)** |
| **Overall HTTP Error Rate** | **0.00%** | **0.00%** | **0.00%** | **0.00%** | **~9.11% Connection Drops** |

---

## 🔎 Root-Cause Autopsy of Infrastructure Failure Modes

The performance testing parameters successfully pushed the application architecture past its boundary limits, revealing two major cascading infrastructure vulnerabilities:

### 1. Concurrency Cascade & Thread Pool Starvation (`APScheduler`)
* **Symptom:** Under massive scale loads, the system threw a critical worker execution trace: `RuntimeError: cannot schedule new futures after shutdown`.
* **Root Cause:** The system runs a 1-second interval cron event to check game status bounds (`advance_rooms_questions`). Under high database contention, these background tasks blocked waiting for connections. The thread pool exhausted its maximum stack instances. The runtime environment forcefully terminated the executor pool to prevent complete kernel panic, causing all subsequent ticks to crash instantly.

### 2. Pessimistic Lock Queue Contention (`.with_for_update()`)
* **Symptom:** API write operations for score processing (`/rooms/[room_code]/answer`) reached latency values of **12,179ms** with a **9.11% failure rate**.
* **Root Cause:** To maintain strict database state consistency (preventing race conditions like double-taps or rapid score injection updates), raw rows were secured via database locks. At high volumes, this created an extreme waiting loop queue. As execution wait time neared 12 seconds, SQLAlchemy connection pool buffers overflowed, dropping active connections.

---

## 🚀 Scalability Strategy Roadmap (Next Architectural Actions)

To transition this architecture to seamlessly manage 10,000+ real-time concurrent instances, the following infrastructure revisions are planned:

1. **Distributed Caching for Aggregates (Cache-Aside):** Offload real-time relational query generation (`func.sum` and complex table `JOIN` logic) to an in-memory **Redis** cache tier with a short Time-To-Live (TTL). This will collapse leaderboard latencies from **2.3s down to <5ms**.
2. **Decoupled Event Loops (Asynchronous Message Queuing):** Replace blocking database-level row lock checks with an optimistic transaction model or move answer processing to an out-of-process stream processor (e.g., **Celery** or **ARQ** utilizing Redis event streams), keeping the API surface completely non-blocking.
