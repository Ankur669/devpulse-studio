"""Pre-configured interactive presets and code samples for one-click demonstration."""

PRESETS = {
    "memory_streaming": {
        "id": "memory_streaming",
        "title": "Large Collection Streaming & Eager Allocations",
        "description": "Exhibits eager list comprehension inside sum(), string += in loop, and list.pop(0).",
        "category": "Memory",
        "code": """# Memory Anti-Pattern Showcase
# 1. Eager list comprehension in sum() loads entire 250,000 integers into RAM
total_sum = sum([i * 2 for i in range(250000)])

# 2. String concatenation in loop causes repeated reallocations
log_summary = ""
for item in range(500):
    log_summary += f"Processing batch_{item}, "

# 3. FIFO queue using list.pop(0) incurs continuous O(N) memory shifting
queue = [x for x in range(5000)]
while queue:
    item = queue.pop(0)

print(f"Total calculated: {total_sum}, Log length: {len(log_summary)}")
"""
    },
    "memory_slots": {
        "id": "memory_slots",
        "title": "High-Volume Class Instances (Missing __slots__)",
        "description": "Instantiating 50,000 objects with dynamic __dict__ vs fixed __slots__.",
        "category": "Memory",
        "code": """# Instantiating 50,000 objects without __slots__
# Incurs ~150 bytes per-instance __dict__ overhead
class TelemetryEvent:
    def __init__(self, event_id, user_id, timestamp, payload, is_active):
        self.event_id = event_id
        self.user_id = user_id
        self.timestamp = timestamp
        self.payload = payload
        self.is_active = is_active

# Allocate high volume of objects
events = [
    TelemetryEvent(i, f"usr_{i}", 1700000000 + i, "METRIC_PING", True)
    for i in range(50000)
]

print(f"Created {len(events)} telemetry events in memory.")
"""
    },
    "docs_api_pipeline": {
        "id": "docs_api_pipeline",
        "title": "Data Pipeline & Service Functions",
        "description": "Functions and classes needing comprehensive docstrings and test coverage.",
        "category": "Documentation",
        "code": """class DataBatchProcessor:
    def __init__(self, batch_size: int, stream_name: str, max_retries: int = 3):
        self.batch_size = batch_size
        self.stream_name = stream_name
        self.max_retries = max_retries

    def transform_record(self, raw_payload: dict, strict_mode: bool = True) -> dict:
        if not raw_payload:
            raise ValueError("Payload cannot be empty")
        return {"processed": True, "keys": list(raw_payload.keys())}

    def compute_moving_average(self, window_data: list, smoothing_factor: float = 0.5) -> float:
        if not window_data:
            raise ZeroDivisionError("Window data is empty")
        return sum(window_data) / len(window_data)

def export_telemetry(metrics_dict: dict, destination_uri: str) -> bool:
    if not destination_uri.startswith("s3://") and not destination_uri.startswith("https://"):
        raise ValueError("Invalid destination URI scheme")
    return True
"""
    },
    "sample_git_diff": {
        "id": "sample_git_diff",
        "title": "Git Diff: Memory Optimization & Stream Loader",
        "description": "Sample multi-file diff showing memory fixes and generator migration.",
        "category": "Git",
        "diff": """diff --git a/services/data_loader.py b/services/data_loader.py
index 4b825dc..f1a942b 100644
--- a/services/data_loader.py
+++ b/services/data_loader.py
@@ -12,7 +12,12 @@ class LargeRecordStreamer:
-    def load_all_records(self, filepath):
-        with open(filepath, 'r') as f:
-            return f.readlines()
+    def stream_records(self, filepath, chunk_size=65536):
+        \"\"\"Stream records in memory-safe chunks.\"\"\"
+        with open(filepath, 'r', buffering=chunk_size) as f:
+            for line in f:
+                yield line.strip()

@@ -45,3 +50,5 @@ def calculate_checksum(data):
-    return sum([hash(x) for x in data])
+    # Migrate from eager list allocation to memory-efficient generator
+    return sum(hash(x) for x in data)
diff --git a/models/session.py b/models/session.py
index 99a12c4..88e331b 100644
--- a/models/session.py
+++ b/models/session.py
@@ -3,2 +3,4 @@ class UserSession:
+    __slots__ = ('session_id', 'user_id', 'created_at', 'expires_at')
+
     def __init__(self, session_id, user_id, created_at, expires_at):
"""
    },
    "sample_schema_json": {
        "id": "sample_schema_json",
        "title": "Telemetry & Payment Schema",
        "description": "Raw JSON object for generating memory-optimized dataclasses and Pydantic models.",
        "category": "Boilerplate",
        "json": """{
  "transaction_id": "tx_984729184",
  "account_id": 49102,
  "amount": 249.50,
  "currency": "USD",
  "is_cleared": true,
  "metadata": {
    "ip_address": "192.168.1.1",
    "risk_score": 0.02
  },
  "tags": ["retail", "express", "pos"]
}"""
    }
}
