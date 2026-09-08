"""Memory Analysis and Runtime Profiling Engine.

Provides AST-based static memory anti-pattern detection, dynamic runtime memory
profiling via Python's `tracemalloc`, and automatic optimization rewriting with
before-and-after benchmarks.
"""

import ast
import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional


class MemoryAntiPatternDetector(ast.NodeVisitor):
    """AST visitor to detect Python memory anti-patterns."""

    def __init__(self):
        self.issues: List[Dict[str, Any]] = []
        self.current_loop_depth = 0
        self.classes_analyzed = []

    def visit_For(self, node: ast.For):
        # Check if iterating over a list comprehension instead of generator
        if isinstance(node.iter, ast.ListComp):
            self.issues.append({
                "rule_id": "MEM001",
                "title": "Eager List Comprehension in For Loop",
                "severity": "Warning",
                "line": node.lineno,
                "col": node.col_offset,
                "message": "Iterating over a list comprehension '[...]' allocates the entire list in memory upfront.",
                "suggestion": "Use a generator expression '(...)' or iterate directly over the data source for O(1) memory streaming.",
                "impact": "High memory overhead for large sequences"
            })
        self.current_loop_depth += 1
        self.generic_visit(node)
        self.current_loop_depth -= 1

    def visit_While(self, node: ast.While):
        self.current_loop_depth += 1
        self.generic_visit(node)
        self.current_loop_depth -= 1

    def visit_AugAssign(self, node: ast.AugAssign):
        # Detect string concatenation in loops: s += item
        if self.current_loop_depth > 0 and isinstance(node.op, ast.Add):
            target_name = ""
            if isinstance(node.target, ast.Name):
                target_name = node.target.id
            self.issues.append({
                "rule_id": "MEM002",
                "title": "String Accumulation Inside Loop",
                "severity": "Caution",
                "line": node.lineno,
                "col": node.col_offset,
                "message": f"Augmented string concatenation '{target_name} += ...' creates intermediate string objects in each iteration.",
                "suggestion": "Append parts into a list and call ''.join(parts) after the loop to reduce memory allocations from O(N^2) to O(N).",
                "impact": "Frequent GC churn and repeated memory reallocations"
            })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Check aggregator functions called with eager list comprehensions: sum([...]), any([...]), all([...]), max([...]), min([...])
        if func_name in {"sum", "any", "all", "max", "min", "tuple", "set"}:
            for arg in node.args:
                if isinstance(arg, ast.ListComp):
                    self.issues.append({
                        "rule_id": "MEM003",
                        "title": f"Eager Allocation in '{func_name}()'",
                        "severity": "Warning",
                        "line": node.lineno,
                        "col": node.col_offset,
                        "message": f"'{func_name}()' consumes an iterator. Passing a list comprehension '[...]' allocates full list in memory.",
                        "suggestion": f"Replace '[x for x in ...]' with generator expression '(x for x in ...)' to stream items with O(1) memory.",
                        "impact": "Full collection retained in memory before reduction"
                    })

        # Check list.pop(0) or list.insert(0, ...)
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "pop" and node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and first_arg.value == 0:
                    self.issues.append({
                        "rule_id": "MEM004",
                        "title": "FIFO Dequeue on Python Standard List",
                        "severity": "Caution",
                        "line": node.lineno,
                        "col": node.col_offset,
                        "message": "Calling 'list.pop(0)' shifts all remaining items in memory, causing O(N) memory copy on each call.",
                        "suggestion": "Use 'collections.deque' and call 'deque.popleft()' for O(1) time and memory overhead.",
                        "impact": "Continuous re-indexing and array copying in memory"
                    })
            elif node.func.attr == "insert" and node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and first_arg.value == 0:
                    self.issues.append({
                        "rule_id": "MEM005",
                        "title": "Front Insertion on Python List",
                        "severity": "Caution",
                        "line": node.lineno,
                        "col": node.col_offset,
                        "message": "Calling 'list.insert(0, ...)' shifts every element down in memory buffer.",
                        "suggestion": "Use 'collections.deque.appendleft()' for efficient double-ended memory layout.",
                        "impact": "Continuous memory buffer shifting"
                    })

            # Check unbuffered read: file.read() or file.readlines()
            if node.func.attr in {"read", "readlines"} and not node.args:
                self.issues.append({
                    "rule_id": "MEM006",
                    "title": f"Unbuffered '{node.func.attr}()' Call",
                    "severity": "Warning",
                    "line": node.lineno,
                    "col": node.col_offset,
                    "message": f"Calling '{node.func.attr}()' without size buffer loads the entire file contents into memory at once.",
                    "suggestion": "Iterate directly over the file object ('for line in f:') or read in chunks using a fixed buffer (e.g., 'f.read(65536)').",
                    "impact": "Can exhaust available system RAM on large files"
                })

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Check if class sets instance attributes in __init__ but has no __slots__
        has_slots = any(
            isinstance(stmt, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "__slots__" for t in stmt.targets
            )
            for stmt in node.body
        )

        # Check if decorated with dataclass(slots=True)
        has_dataclass_slots = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == "dataclass":
                for kw in decorator.keywords:
                    if kw.arg == "slots" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        has_dataclass_slots = True

        attrs_assigned = set()
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for stmt in item.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                                attrs_assigned.add(target.attr)

        if attrs_assigned and not has_slots and not has_dataclass_slots:
            attr_tuple = ", ".join(f"'{a}'" for a in sorted(attrs_assigned))
            self.issues.append({
                "rule_id": "MEM007",
                "title": f"Class '{node.name}' Missing '__slots__'",
                "severity": "Recommendation",
                "line": node.lineno,
                "col": node.col_offset,
                "message": f"Class '{node.name}' creates instances with a dynamic '__dict__' dictionary, incurring ~150-200 bytes overhead per instance.",
                "suggestion": f"Define '__slots__ = ({attr_tuple})' or use '@dataclass(slots=True)' to reduce memory footprint by 40-60% per instance.",
                "impact": "High memory footprint when instantiating thousands or millions of objects"
            })

        self.generic_visit(node)


def analyze_memory_code(code_str: str) -> Dict[str, Any]:
    """Perform AST static memory anti-pattern analysis on Python code."""
    try:
        tree = ast.parse(code_str)
        detector = MemoryAntiPatternDetector()
        detector.visit(tree)
        return {
            "success": True,
            "issues": detector.issues,
            "total_issues": len(detector.issues),
            "summary": {
                "high_severity": sum(1 for i in detector.issues if i["severity"] == "Warning"),
                "medium_severity": sum(1 for i in detector.issues if i["severity"] == "Caution"),
                "recommendations": sum(1 for i in detector.issues if i["severity"] == "Recommendation")
            }
        }
    except SyntaxError as e:
        return {
            "success": False,
            "error": f"SyntaxError: {e.msg} at line {e.lineno}",
            "issues": [],
            "total_issues": 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "issues": [],
            "total_issues": 0
        }


def profile_code_runtime(code_str: str, timeout_seconds: int = 6) -> Dict[str, Any]:
    """Safely execute Python code in a subprocess to profile memory with tracemalloc."""
    runner_script = """
import tracemalloc
import time
import sys
import json
import traceback

tracemalloc.start()
start_time = time.perf_counter()

output_data = {
    "success": True,
    "stdout": "",
    "stderr": "",
    "peak_kb": 0.0,
    "current_kb": 0.0,
    "time_ms": 0.0,
    "top_traces": []
}

import io
captured_stdout = io.StringIO()
old_stdout = sys.stdout
sys.stdout = captured_stdout

try:
    # Execute user code in dedicated namespace
    exec_scope = {"__name__": "__main__"}
    code_obj = compile(%r, "<user_code>", "exec")
    exec(code_obj, exec_scope)
except Exception as e:
    output_data["success"] = False
    output_data["stderr"] = traceback.format_exc()

sys.stdout = old_stdout
output_data["stdout"] = captured_stdout.getvalue()

current, peak = tracemalloc.get_traced_memory()
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')[:8]

output_data["peak_kb"] = round(peak / 1024, 2)
output_data["current_kb"] = round(current / 1024, 2)
output_data["time_ms"] = round((time.perf_counter() - start_time) * 1000, 2)

traces = []
for stat in top_stats:
    frame = stat.traceback[0]
    filename = frame.filename
    if "<user_code>" in filename or "user_code" in filename:
        filename = "user_code"
    elif len(filename) > 30:
        filename = "..." + filename[-25:]
    traces.append({
        "file": filename,
        "line": frame.lineno,
        "size_kb": round(stat.size / 1024, 2),
        "count": stat.count
    })
output_data["top_traces"] = traces

tracemalloc.stop()
print("---PROFILER_OUTPUT_BEGIN---")
print(json.dumps(output_data))
print("---PROFILER_OUTPUT_END---")
""" % code_str

    try:
        proc = subprocess.run(
            [sys.executable, "-c", runner_script],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        stdout_raw = proc.stdout
        stderr_raw = proc.stderr

        if "---PROFILER_OUTPUT_BEGIN---" in stdout_raw:
            parts = stdout_raw.split("---PROFILER_OUTPUT_BEGIN---")[1].split("---PROFILER_OUTPUT_END---")[0]
            result = json.loads(parts.strip())
            return result
        else:
            return {
                "success": False,
                "error": stderr_raw or stdout_raw or "Profiler execution failed.",
                "peak_kb": 0.0,
                "current_kb": 0.0,
                "time_ms": 0.0,
                "top_traces": []
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Execution timed out after {timeout_seconds} seconds (infinite loop or excessive memory allocation).",
            "peak_kb": 0.0,
            "current_kb": 0.0,
            "time_ms": timeout_seconds * 1000,
            "top_traces": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "peak_kb": 0.0,
            "current_kb": 0.0,
            "time_ms": 0.0,
            "top_traces": []
        }


def generate_optimized_code(code_str: str) -> Dict[str, Any]:
    """Generate an optimized version of the code and provide detailed explanations."""
    lines = code_str.splitlines()
    changes_made = []
    optimized_lines = list(lines)
    opt_code = code_str

    # 1. Transform sum([x for x in ...]) to sum(x for x in ...)
    if "sum([" in opt_code:
        opt_code = opt_code.replace("sum([", "sum(").replace("])", ")")
        changes_made.append("Converted eager list comprehension inside 'sum()' to lazy generator expression.")

    # 2. Transform any([x for x in ...]) or all([x for x in ...])
    for func in ["any", "all", "max", "min"]:
        if f"{func}([" in opt_code:
            opt_code = opt_code.replace(f"{func}([", f"{func}(").replace("])", ")")
            changes_made.append(f"Converted eager list comprehension inside '{func}()' to generator expression.")

    # 3. Transform for item in [x for x in ...] -> for item in (x for x in ...) or directly
    if " in [" in opt_code and " for " in opt_code:
        # Check simple pattern
        import re
        opt_code = re.sub(r'for\s+([a-zA-Z0-9_]+)\s+in\s+\[([^\]]+)\]:', r'for \1 in (\2):', opt_code)
        changes_made.append("Converted eager list iteration in 'for' loop into a memory-efficient generator.")

    # 4. Transform list.pop(0) to deque.popleft()
    if ".pop(0)" in opt_code:
        if "from collections import deque" not in opt_code and "import collections" not in opt_code:
            opt_code = "from collections import deque\n\n" + opt_code
        opt_code = opt_code.replace(".pop(0)", ".popleft()")
        # If there's an initialization of list like queue = [] or queue = list(...)
        import re
        opt_code = re.sub(r'([a-zA-Z0-9_]+)\s*=\s*\[(.*?)\]', r'\1 = deque([\2])', opt_code, count=1)
        changes_made.append("Replaced O(N) memory-shifting 'list.pop(0)' with O(1) 'collections.deque.popleft()'.")

    # 5. Transform string accumulation in loop
    if "+=" in opt_code and ("for " in opt_code or "while " in opt_code):
        # Look for pattern: result = "" ... for ...: result += chunk ... return result
        import re
        match = re.search(r'([a-zA-Z0-9_]+)\s*=\s*["\']\s*["\']', opt_code)
        if match:
            var_name = match.group(1)
            if f"{var_name} +=" in opt_code:
                opt_code = opt_code.replace(f'{var_name} = ""', f'{var_name}_chunks = []')
                opt_code = opt_code.replace(f'{var_name} = \'\'', f'{var_name}_chunks = []')
                opt_code = re.sub(rf'{var_name}\s*\+=\s*(.+)', rf'{var_name}_chunks.append(\1)', opt_code)
                # Before return or print, join
                opt_code = opt_code.replace(f'return {var_name}', f'return "".join({var_name}_chunks)')
                opt_code = opt_code.replace(f'print({var_name})', f'{var_name} = "".join({var_name}_chunks)\nprint({var_name})')
                changes_made.append(f"Replaced string concatenation '{var_name} += ...' with list chunking and ''.join(...) to eliminate reallocations.")

    # 6. Check missing __slots__ in classes
    try:
        tree = ast.parse(opt_code)
        detector = MemoryAntiPatternDetector()
        detector.visit(tree)
        for issue in detector.issues:
            if issue["rule_id"] == "MEM007":
                # Add __slots__ to class
                class_name = issue["title"].split("'")[1]
                # Find class definition line
                import re
                pattern = rf'class\s+{class_name}(\(.*?\))?:'
                match = re.search(pattern, opt_code)
                if match:
                    # Extract attributes
                    attrs = re.findall(r'self\.([a-zA-Z0-9_]+)\s*=', opt_code)
                    if attrs:
                        unique_attrs = sorted(list(set(attrs)))
                        slots_repr = ", ".join(f"'{a}'" for a in unique_attrs)
                        slots_line = f"\n    __slots__ = ({slots_repr},)"
                        opt_code = opt_code[:match.end()] + slots_line + opt_code[match.end():]
                        changes_made.append(f"Added '__slots__' to class '{class_name}' to eliminate per-instance '__dict__' dictionaries.")
                        break
    except Exception:
        pass

    if not changes_made:
        changes_made.append("Code already adheres to primary memory patterns, or patterns require custom manual refactoring.")

    return {
        "optimized_code": opt_code,
        "changes_made": changes_made
    }


def benchmark_comparison(original_code: str, optimized_code: str) -> Dict[str, Any]:
    """Profile both original and optimized code, and calculate memory savings."""
    prof_orig = profile_code_runtime(original_code)
    prof_opt = profile_code_runtime(optimized_code)

    orig_peak = prof_orig.get("peak_kb", 0.0)
    opt_peak = prof_opt.get("peak_kb", 0.0)

    # Memory reduction percentage
    if orig_peak > 0:
        saved_kb = round(orig_peak - opt_peak, 2)
        saved_percent = round(max(0.0, (orig_peak - opt_peak) / orig_peak * 100), 1)
    else:
        saved_kb = 0.0
        saved_percent = 0.0

    return {
        "original": prof_orig,
        "optimized": prof_opt,
        "memory_saved_kb": saved_kb,
        "memory_saved_percent": saved_percent,
        "speedup_ms": round(prof_orig.get("time_ms", 0.0) - prof_opt.get("time_ms", 0.0), 2)
    }
