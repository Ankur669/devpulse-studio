"""Developer Productivity Tool - DevPulse Studio.

A web application automating repetitive coding and documentation workflows,
integrating with GitHub and GitLab, and suggesting deep optimizations for memory
usage with live tracemalloc runtime benchmarking.
"""

import os
import sys
from flask import Flask, jsonify, render_template, request

# Ensure engine package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.doc_engine import (
    generate_data_models,
    generate_docstrings_for_code,
    generate_readme,
    inject_docstrings_into_code,
    scaffold_unit_tests,
)
from engine.git_engine import (
    fetch_remote_repo_data,
    generate_cicd_pipeline,
    generate_conventional_commit,
    generate_pr_description,
    parse_git_diff,
)
from engine.memory_engine import (
    analyze_memory_code,
    benchmark_comparison,
    generate_optimized_code,
    profile_code_runtime,
)
from engine.presets import PRESETS

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    """Render the primary single page application."""
    return render_template("index.html")


@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Return all interactive preset scenarios."""
    return jsonify({"success": True, "presets": PRESETS})


# --- Memory Optimization Endpoints ---


@app.route("/api/memory/analyze", methods=["POST"])
def analyze_memory():
    """AST static memory anti-pattern detection."""
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "")
    if not code.strip():
        return jsonify({"success": False, "error": "No code provided for analysis.", "issues": []}), 400

    result = analyze_memory_code(code)
    return jsonify(result)


@app.route("/api/memory/profile", methods=["POST"])
def profile_memory():
    """Live runtime memory and CPU profiling using tracemalloc."""
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "")
    if not code.strip():
        return jsonify({"success": False, "error": "No code provided for profiling."}), 400

    timeout = int(data.get("timeout", 6))
    result = profile_code_runtime(code, timeout_seconds=timeout)
    return jsonify(result)


@app.route("/api/memory/optimize-compare", methods=["POST"])
def optimize_and_compare():
    """Automatically optimize memory patterns and run side-by-side benchmark."""
    data = request.get_json(force=True, silent=True) or {}
    original_code = data.get("code", "")
    custom_optimized = data.get("custom_optimized", "")

    if not original_code.strip():
        return jsonify({"success": False, "error": "No code provided to optimize."}), 400

    if custom_optimized and custom_optimized.strip():
        opt_code = custom_optimized
        changes_made = ["User-provided optimized variant."]
    else:
        opt_data = generate_optimized_code(original_code)
        opt_code = opt_data["optimized_code"]
        changes_made = opt_data["changes_made"]

    benchmark = benchmark_comparison(original_code, opt_code)
    benchmark["optimized_code"] = opt_code
    benchmark["changes_made"] = changes_made
    benchmark["success"] = True

    return jsonify(benchmark)


# --- Documentation & Code Automation Endpoints ---


@app.route("/api/docs/docstrings", methods=["POST"])
def generate_docs():
    """Generate docstrings (Google, NumPy, Sphinx styles)."""
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "")
    style = data.get("style", "google")
    result = generate_docstrings_for_code(code, style=style)
    return jsonify(result)


@app.route("/api/docs/inject", methods=["POST"])
def inject_docs():
    """Inject generated docstrings directly into Python source code."""
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "")
    style = data.get("style", "google")
    result = inject_docstrings_into_code(code, style=style)
    return jsonify(result)


@app.route("/api/docs/readme", methods=["POST"])
def make_readme():
    """Synthesize Markdown README with badges, architecture, and guides."""
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("project_name", "DevPulse Studio")
    description = data.get("description", "")
    features = data.get("features", [])
    tech_stack = data.get("tech_stack", ["Python", "Flask", "Tracemalloc"])
    code_sample = data.get("code_sample", "")

    markdown = generate_readme(name, description, features, tech_stack, code_sample)
    return jsonify({"success": True, "readme": markdown})


@app.route("/api/code/tests", methods=["POST"])
def scaffold_tests():
    """Scaffold pytest/unittest test suites."""
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "")
    framework = data.get("framework", "pytest")
    result = scaffold_unit_tests(code, framework=framework)
    return jsonify(result)


@app.route("/api/code/boilerplate", methods=["POST"])
def create_boilerplate():
    """Generate memory-efficient dataclasses or Pydantic models from schema JSON."""
    data = request.get_json(force=True, silent=True) or {}
    schema_json = data.get("schema_json", "{}")
    model_type = data.get("model_type", "dataclass_slots")
    result = generate_data_models(schema_json, model_type=model_type)
    return jsonify(result)


# --- GitHub & GitLab Integration Endpoints ---


@app.route("/api/git/diff-to-pr", methods=["POST"])
def diff_to_pr():
    """Analyze git diff and generate comprehensive PR description."""
    data = request.get_json(force=True, silent=True) or {}
    diff = data.get("diff", "")
    context = data.get("context", "")
    result = generate_pr_description(diff, custom_context=context)
    result["success"] = True
    return jsonify(result)


@app.route("/api/git/commit-msg", methods=["POST"])
def commit_msg():
    """Format message adhering to Conventional Commits standard."""
    data = request.get_json(force=True, silent=True) or {}
    short_desc = data.get("description", "optimize memory footprint")
    scope = data.get("scope", "memory")
    commit_type = data.get("type", "perf")
    is_breaking = bool(data.get("breaking", False))

    formatted = generate_conventional_commit(short_desc, scope, commit_type, is_breaking)
    return jsonify({"success": True, "commit_message": formatted})


@app.route("/api/git/cicd", methods=["POST"])
def cicd_pipeline():
    """Generate GitHub Actions or GitLab CI workflow configuration."""
    data = request.get_json(force=True, silent=True) or {}
    platform = data.get("platform", "github")
    python_versions = data.get("python_versions", ["3.11", "3.12"])
    check_memory = bool(data.get("check_memory", True))

    pipeline_yaml = generate_cicd_pipeline(platform, python_versions, check_memory)
    return jsonify({"success": True, "platform": platform, "pipeline_yaml": pipeline_yaml})


@app.route("/api/git/fetch-repo", methods=["POST"])
def fetch_repo():
    """Connect to GitHub or GitLab remote REST API."""
    data = request.get_json(force=True, silent=True) or {}
    platform = data.get("platform", "github")
    repo = data.get("repo", "demo")
    token = data.get("token", "")

    result = fetch_remote_repo_data(platform, repo, token)
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting DevPulse Studio server on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
