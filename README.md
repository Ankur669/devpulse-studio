# 🚀 DevPulse Studio

**Developer Productivity Tool** for memory optimization, documentation automation, and GitHub/GitLab integration.  
Built with Flask, Python, and modern UI components.

---

## 📂 Project Structure

c:\CODE\dev_tool\
├── app.py                     # Primary Flask Web Server & REST API endpoints
├── test_suite.py              # Automated unit and integration test suite (16 tests)
├── engine/
│   ├── memory_engine.py       # AST static analysis, tracemalloc profiler, auto-optimizer
│   ├── doc_engine.py          # Docstring generator, README & test scaffolding
│   ├── git_engine.py          # Diff parser, PR generator, CI/CD configs
│   └── presets.py             # Pre-configured interactive demo scenarios
├── static/
│   ├── css/style.css          # Glassmorphic dark theme, responsive layout
│   └── js/main.js             # Client interactivity, charts, live execution
└── templates/
└── index.html             # Semantic HTML5 workstation layout

Code

---

## ⚡ Key Features

### 1. Memory Usage Optimization
- Detects anti-patterns (`list.pop(0)`, string concatenation in loops, etc.).
- Profiles runtime with `tracemalloc`.
- Auto-optimizes code (generator expressions, `deque`, `__slots__`).
- Benchmarks RAM reduction (40–85%+ savings).

### 2. Documentation & Automation
- Generates Google/NumPy/Sphinx docstrings.
- One-click docstring injection into source code.
- README generator with badges, quickstart, and architecture.
- Unit test scaffolding via AST analysis.
- JSON → slotted dataclass / Pydantic model converter.

### 3. GitHub/GitLab Integration
- Smart PR/MR assistant (scope, type, checklist).
- Conventional Commit formatter.
- CI/CD pipeline generator (GitHub Actions, GitLab CI).
- Remote repo explorer with sandbox mode.

---

## 🧪 Validation

- **16/16 tests passed** (`test_suite.py`).
- Verified endpoints:
  - `/api/memory/analyze`
  - `/api/memory/profile`
  - `/api/docs/docstrings`
- Live server running at `http://127.0.0.1:5000`.

---

## 🚀 Quickstart

```bash
# Clone the repo
git clone https://github.com/Ankur669/devpulse-studio.git
cd devpulse-studio


# Run the server
python app.py

# Visit in browser
http://127.0.0.1:5000
📜 License
This project is MIT License.

🤝 Contributing
Fork the repo

Create a feature branch (git checkout -b feat-new-feature)

Commit changes (git commit -m "feat: add new feature")

Push to branch (git push origin feat-new-feature)

Open a Pull Request

🧑‍💻 Author
Ankur 
