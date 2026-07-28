"""
Prometheus metrics definitions.

Five metrics as required by the project spec:
  1. moderation_latency_seconds  — Histogram
  2. extraction_latency_seconds  — Histogram
  3. token_cost_usd_total        — Counter
  4. auto_approvals_total        — Counter
  5. throughput_docs_per_minute  — Gauge

All metrics use the 'ledgerlens' namespace prefix.
"""
from prometheus_client import Counter, Gauge, Histogram

moderation_latency = Histogram(
    "ledgerlens_moderation_latency_seconds",
    "Time spent running the content moderation gate",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

extraction_latency = Histogram(
    "ledgerlens_extraction_latency_seconds",
    "Time spent on GPT-4o invoice extraction",
    buckets=[1.0, 2.5, 5.0, 10.0, 20.0, 40.0],
)

token_cost_usd = Counter(
    "ledgerlens_token_cost_usd_total",
    "Cumulative OpenAI token cost in USD",
)

auto_approvals_total = Counter(
    "ledgerlens_auto_approvals_total",
    "Number of documents that passed confidence threshold and were auto-approved",
)

pending_review_total = Counter(
    "ledgerlens_pending_review_total",
    "Number of documents routed to the human review queue",
)

throughput_docs = Gauge(
    "ledgerlens_throughput_docs_per_minute",
    "Rolling documents processed per minute (updated on each ingest)",
)
