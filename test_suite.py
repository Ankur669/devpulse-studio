"""Comprehensive Test Suite for DevPulse Studio.

Tests AST memory analysis, dynamic tracemalloc profiling, automated docstring
generation and injection, test scaffolding, model builders, git diff and PR
synthesizers, and Flask REST endpoints.
"""

import json
import unittest
from engine.memory_engine import (
    analyze_memory_code,
    profile_code_runtime,
    generate_optimized_code,
    benchmark_comparison
)
from engine.doc_engine import (
    generate_docstrings_for_code,
    inject_docstrings_into_code,
    generate_readme,
    scaffold_unit_tests,
    generate_data_models
)
from engine.git_engine import (
    parse_git_diff,
    generate_pr_description,
    generate_conventional_commit,
    generate_cicd_pipeline,
    fetch_remote_repo_data
)
from app import app


class TestMemoryEngine(unittest.TestCase):
    def test_ast_memory_antipatterns(self):
        sample_code = """
total = sum([x * 2 for x in range(100)])

res = ""
for item in range(10):
    res += str(item)

queue = [1, 2, 3]
first = queue.pop(0)

class DataRecord:
    def __init__(self, a, b):
        self.a = a
        self.b = b
"""
        analysis = analyze_memory_code(sample_code)
        self.assertTrue(analysis["success"])
        self.assertGreaterEqual(analysis["total_issues"], 4)

        rule_ids = {iss["rule_id"] for iss in analysis["issues"]}
        self.assertIn("MEM003", rule_ids)  # sum([...])
        self.assertIn("MEM002", rule_ids)  # s += ...
        self.assertIn("MEM004", rule_ids)  # pop(0)
        self.assertIn("MEM007", rule_ids)  # missing slots

    def test_tracemalloc_profiling(self):
        code = """
import time
data = [i for i in range(100000)]
total = sum(data)
"""
        profile = profile_code_runtime(code, timeout_seconds=5)
        self.assertTrue(profile["success"])
        self.assertGreater(profile["peak_kb"], 500)
        self.assertGreater(profile["time_ms"], 0)
        self.assertIsInstance(profile["top_traces"], list)

    def test_memory_optimization_and_benchmark(self):
        orig_code = "data = sum([x for x in range(50000)])"
        opt = generate_optimized_code(orig_code)
        self.assertIn("sum(x for x in range(50000))", opt["optimized_code"])

        bench = benchmark_comparison(orig_code, opt["optimized_code"])
        self.assertTrue(bench["original"]["success"])
        self.assertTrue(bench["optimized"]["success"])
        self.assertGreaterEqual(bench["memory_saved_percent"], 0)


class TestDocEngine(unittest.TestCase):
    def test_docstring_generation(self):
        code = """
def calculate_tax(income: float, rate: float = 0.2) -> float:
    if income < 0:
        raise ValueError("Income must be positive")
    return income * rate
"""
        google_res = generate_docstrings_for_code(code, style="google")
        self.assertTrue(google_res["success"])
        self.assertEqual(google_res["total_items"], 1)
        doc = google_res["items"][0]["generated_doc"]
        self.assertIn("Args:", doc)
        self.assertIn("income (float)", doc)
        self.assertIn("Returns:", doc)
        self.assertIn("Raises:", doc)

    def test_docstring_injection(self):
        code = """def add_numbers(a: int, b: int) -> int:
    return a + b
"""
        res = inject_docstrings_into_code(code, style="google")
        self.assertTrue(res["success"])
        self.assertEqual(res["injected_count"], 1)
        self.assertIn('"""', res["injected_code"])
        self.assertIn('Args:', res["injected_code"])

    def test_readme_generator(self):
        readme = generate_readme(
            project_name="DataStream X",
            description="Ultra fast stream engine",
            features=["Zero copy", "Tracemalloc tracking"],
            tech_stack=["Python", "Flask"]
        )
        self.assertIn("# DataStream X", readme)
        self.assertIn("Zero copy", readme)
        self.assertIn("Architecture & Memory Optimization", readme)

    def test_test_scaffolder(self):
        code = """
def compute_hash(payload: str) -> str:
    return payload[::-1]
"""
        scaffold = scaffold_unit_tests(code, framework="pytest")
        self.assertTrue(scaffold["success"])
        self.assertIn("def test_compute_hash_basic():", scaffold["test_code"])
        self.assertIn("import pytest", scaffold["test_code"])

    def test_data_model_generator(self):
        schema = json.dumps({"id": 101, "sku": "ABC", "in_stock": True, "price": 49.99})
        res = generate_data_models(schema, model_type="dataclass_slots")
        self.assertTrue(res["success"])
        self.assertIn("@dataclass(slots=True)", res["code"])
        self.assertIn("id: int", res["code"])
        self.assertIn("price: float", res["code"])


class TestGitEngine(unittest.TestCase):
    def test_git_diff_and_pr_description(self):
        diff = """diff --git a/app.py b/app.py
index 1234..5678 100644
--- a/app.py
+++ b/app.py
@@ -10,3 +10,4 @@
-total = sum([x for x in data])
+total = sum(x for x in data)
"""
        pr_desc = generate_pr_description(diff, custom_context="Optimize generator allocations")
        self.assertIn("perf(app)", pr_desc["title"])
        self.assertIn("Summary of Changes", pr_desc["body_markdown"])
        self.assertIn("Performance & Memory Impact", pr_desc["body_markdown"])
        self.assertEqual(pr_desc["diff_stats"]["files_count"], 1)

    def test_conventional_commit(self):
        msg = generate_conventional_commit(
            short_desc="replace eager list with generator",
            scope="stream",
            commit_type="perf",
            is_breaking=False
        )
        self.assertEqual(msg, "perf(stream): replace eager list with generator")

    def test_cicd_generator(self):
        gh_workflow = generate_cicd_pipeline("github", ["3.11", "3.12"])
        self.assertIn("GitHub Actions CI Workflow", gh_workflow)
        self.assertIn("python-version: [\"3.11\", \"3.12\"]", gh_workflow)

        gl_pipeline = generate_cicd_pipeline("gitlab")
        self.assertIn("GitLab CI/CD Pipeline", gl_pipeline)
        self.assertIn("memory_profile", gl_pipeline)

    def test_mock_remote_repo(self):
        mock_data = fetch_remote_repo_data("github", "demo")
        self.assertTrue(mock_data["success"])
        self.assertTrue(mock_data["is_mock"])
        self.assertIn("dev-productivity-suite", mock_data["full_name"])


class TestFlaskAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_page(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"DevPulse Studio", resp.data)

    def test_presets_api(self):
        resp = self.client.get("/api/presets")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertIn("memory_streaming", data["presets"])

    def test_api_memory_analyze(self):
        resp = self.client.post("/api/memory/analyze", json={
            "code": "sum([i for i in range(10)])"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(data["total_issues"], 0)

    def test_api_docs_docstrings(self):
        resp = self.client.post("/api/docs/docstrings", json={
            "code": "def hello(name: str) -> str:\n    return 'hi ' + name",
            "style": "google"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_items"], 1)


if __name__ == "__main__":
    unittest.main()
