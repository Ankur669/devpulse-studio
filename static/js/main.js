// DevPulse Studio - Core Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initMemoryModule();
  initDocsModule();
  initGitModule();
  initPresetsModule();
  loadDefaultPreset();
});

/* Global Toast Notification */
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : '⚠'}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function copyToClipboard(text, successMsg = 'Copied to clipboard!') {
  if (!navigator.clipboard) {
    const el = document.createElement('textarea');
    el.value = text;
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    showToast(successMsg);
    return;
  }
  navigator.clipboard.writeText(text).then(() => {
    showToast(successMsg);
  }).catch(err => {
    showToast('Failed to copy: ' + err, 'error');
  });
}

/* Tab Navigation */
function initTabs() {
  const tabBtns = document.querySelectorAll('.nav-tabs .tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      activateTab(targetId);
    });
  });
}

function activateTab(tabId) {
  document.querySelectorAll('.nav-tabs .tab-btn').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-tab') === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === tabId);
  });
}

/* ========================================================================= */
/* MEMORY OPTIMIZATION & PROFILER MODULE                                      */
/* ========================================================================= */

function initMemoryModule() {
  const btnScan = document.getElementById('btn-mem-scan');
  const btnProfile = document.getElementById('btn-mem-profile');
  const btnOptimize = document.getElementById('btn-mem-optimize');
  const btnApplyOpt = document.getElementById('btn-apply-opt');
  const btnCopyOpt = document.getElementById('btn-copy-opt');
  const memPresetSelect = document.getElementById('mem-preset-select');
  const editor = document.getElementById('mem-code-editor');

  if (btnScan) {
    btnScan.addEventListener('click', async () => {
      const code = editor.value;
      if (!code.trim()) return showToast('Please provide code to analyze.', 'error');

      btnScan.disabled = true;
      btnScan.innerHTML = '<span class="spinner"></span> Scanning AST...';

      try {
        const resp = await fetch('/api/memory/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code })
        });
        const data = await resp.json();
        renderStaticAnalysis(data);
        showToast(`Scan complete: ${data.total_issues} pattern(s) identified.`);
      } catch (err) {
        showToast('Static analysis failed: ' + err.message, 'error');
      } finally {
        btnScan.disabled = false;
        btnScan.innerHTML = '🔍 AST Static Scan';
      }
    });
  }

  if (btnProfile) {
    btnProfile.addEventListener('click', async () => {
      const code = editor.value;
      if (!code.trim()) return showToast('Please provide code to profile.', 'error');

      btnProfile.disabled = true;
      btnProfile.innerHTML = '<span class="spinner"></span> Profiling RAM...';

      try {
        const resp = await fetch('/api/memory/profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, timeout: 8 })
        });
        const data = await resp.json();
        renderProfileResults(data);
        if (data.success) {
          showToast(`Profiled successfully: Peak ${data.peak_kb} KB.`);
        } else {
          showToast('Execution error during profiling: ' + (data.error || 'Unknown'), 'error');
        }
      } catch (err) {
        showToast('Runtime profiling failed: ' + err.message, 'error');
      } finally {
        btnProfile.disabled = false;
        btnProfile.innerHTML = '⚡ Dynamic Tracemalloc Profile';
      }
    });
  }

  if (btnOptimize) {
    btnOptimize.addEventListener('click', async () => {
      const code = editor.value;
      if (!code.trim()) return showToast('Please provide code to optimize.', 'error');

      btnOptimize.disabled = true;
      btnOptimize.innerHTML = '<span class="spinner"></span> Benchmarking...';

      try {
        const resp = await fetch('/api/memory/optimize-compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code })
        });
        const data = await resp.json();
        renderOptimizationBenchmark(data);
        showToast(`Optimization complete: Saved ${data.memory_saved_percent}% RAM!`);
      } catch (err) {
        showToast('Optimization failed: ' + err.message, 'error');
      } finally {
        btnOptimize.disabled = false;
        btnOptimize.innerHTML = '🚀 Auto-Optimize & Benchmark';
      }
    });
  }

  if (btnApplyOpt) {
    btnApplyOpt.addEventListener('click', () => {
      const optCode = document.getElementById('opt-code-output').textContent;
      if (optCode && optCode.trim()) {
        editor.value = optCode;
        showToast('Optimized code applied to primary editor!');
      }
    });
  }

  if (btnCopyOpt) {
    btnCopyOpt.addEventListener('click', () => {
      const optCode = document.getElementById('opt-code-output').textContent;
      copyToClipboard(optCode);
    });
  }

  if (memPresetSelect) {
    memPresetSelect.addEventListener('change', async (e) => {
      const val = e.target.value;
      if (!val) return;
      loadPresetById(val, 'mem-code-editor');
    });
  }
}

function renderStaticAnalysis(data) {
  const container = document.getElementById('mem-issues-container');
  const countBadge = document.getElementById('mem-issues-count');
  if (!container) return;

  if (countBadge) countBadge.textContent = data.total_issues || '0';

  if (!data.success || !data.issues || data.issues.length === 0) {
    container.innerHTML = `
      <div style="padding: 1.5rem; text-align: center; color: var(--accent-emerald);">
        <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">✓</div>
        <div style="font-weight: 600;">No Memory Anti-Patterns Detected</div>
        <div style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.3rem;">
          Code adheres to lazy generator streaming and slot allocation guidelines.
        </div>
      </div>
    `;
    return;
  }

  container.innerHTML = data.issues.map(iss => {
    const sevClass = iss.severity.toLowerCase();
    return `
      <div class="issue-item severity-${sevClass}">
        <div class="issue-top">
          <span class="issue-rule">${iss.rule_id}</span>
          <span class="issue-line">Line ${iss.line}:${iss.col}</span>
        </div>
        <div class="issue-title">${iss.title}</div>
        <div class="issue-msg">${iss.message}</div>
        <div class="issue-suggestion">💡 <strong>Remedy:</strong> ${iss.suggestion}</div>
      </div>
    `;
  }).join('');
}

function renderProfileResults(data) {
  document.getElementById('stat-peak-mem').textContent = data.peak_kb !== undefined ? `${data.peak_kb} KB` : '--';
  document.getElementById('stat-curr-mem').textContent = data.current_kb !== undefined ? `${data.current_kb} KB` : '--';
  document.getElementById('stat-exec-time').textContent = data.time_ms !== undefined ? `${data.time_ms} ms` : '--';

  const traceContainer = document.getElementById('trace-table-body');
  if (traceContainer) {
    if (data.top_traces && data.top_traces.length > 0) {
      traceContainer.innerHTML = data.top_traces.map(t => `
        <tr>
          <td>${t.file}:${t.line}</td>
          <td style="color: var(--accent-rose); font-weight: 600;">${t.size_kb} KB</td>
          <td>${t.count}</td>
        </tr>
      `).join('');
    } else {
      traceContainer.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--text-muted);">No trace snapshots available</td></tr>`;
    }
  }

  const stdoutBox = document.getElementById('runtime-stdout');
  if (stdoutBox) {
    stdoutBox.textContent = data.stdout || (data.stderr ? `Error:\n${data.stderr}` : '(No output returned)');
  }
}

function renderOptimizationBenchmark(data) {
  document.getElementById('stat-saved-percent').textContent = `${data.memory_saved_percent}%`;
  document.getElementById('stat-saved-kb').textContent = `${data.memory_saved_kb} KB`;
  document.getElementById('stat-speedup').textContent = `${data.speedup_ms >= 0 ? '+' : ''}${data.speedup_ms} ms`;

  // Render before & after peak cards
  const origPeak = data.original?.peak_kb ?? '--';
  const optPeak = data.optimized?.peak_kb ?? '--';
  document.getElementById('benchmark-orig-peak').textContent = `${origPeak} KB`;
  document.getElementById('benchmark-opt-peak').textContent = `${optPeak} KB`;

  const changesList = document.getElementById('opt-changes-list');
  if (changesList && data.changes_made) {
    changesList.innerHTML = data.changes_made.map(c => `<li>✓ ${c}</li>`).join('');
  }

  const optOutput = document.getElementById('opt-code-output');
  if (optOutput) {
    optOutput.textContent = data.optimized_code || '';
  }
}

/* ========================================================================= */
/* DOCS & CODE AUTOMATION MODULE                                             */
/* ========================================================================= */

function initDocsModule() {
  const btnGenDocs = document.getElementById('btn-gen-docs');
  const btnInjectDocs = document.getElementById('btn-inject-docs');
  const btnGenReadme = document.getElementById('btn-gen-readme');
  const btnGenTests = document.getElementById('btn-gen-tests');
  const btnGenModels = document.getElementById('btn-gen-models');
  const btnCopyDocOutput = document.getElementById('btn-copy-doc-output');
  const codeEditor = document.getElementById('docs-code-editor');
  const docOutput = document.getElementById('docs-result-output');

  if (btnGenDocs) {
    btnGenDocs.addEventListener('click', async () => {
      const code = codeEditor.value;
      const style = document.getElementById('doc-style-select').value;
      if (!code.trim()) return showToast('Please enter Python code.', 'error');

      btnGenDocs.disabled = true;
      try {
        const resp = await fetch('/api/docs/docstrings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, style })
        });
        const data = await resp.json();
        if (data.success) {
          let outputText = `# Generated ${style.toUpperCase()} Docstrings (${data.total_items} items found)\n\n`;
          data.items.forEach(item => {
            outputText += `### ${item.type.toUpperCase()}: ${item.name} (Line ${item.line})\n`;
            outputText += `\"\"\"\n${item.generated_doc}\n\"\"\"\n\n`;
          });
          docOutput.textContent = outputText;
          showToast(`Generated docstrings for ${data.total_items} symbol(s)!`);
        } else {
          showToast(data.error || 'Doc generation failed', 'error');
        }
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
      } finally {
        btnGenDocs.disabled = false;
      }
    });
  }

  if (btnInjectDocs) {
    btnInjectDocs.addEventListener('click', async () => {
      const code = codeEditor.value;
      const style = document.getElementById('doc-style-select').value;
      if (!code.trim()) return showToast('Please enter Python code.', 'error');

      btnInjectDocs.disabled = true;
      try {
        const resp = await fetch('/api/docs/inject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, style })
        });
        const data = await resp.json();
        if (data.success) {
          codeEditor.value = data.injected_code;
          docOutput.textContent = `# Cleanly Injected ${data.injected_count} Docstrings into Source Code!\n\nReview the updated editor on the left.`;
          showToast(`Injected ${data.injected_count} docstrings into source code!`);
        } else {
          showToast(data.error || 'Injection failed', 'error');
        }
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
      } finally {
        btnInjectDocs.disabled = false;
      }
    });
  }

  if (btnGenReadme) {
    btnGenReadme.addEventListener('click', async () => {
      const code = codeEditor.value;
      const projectName = document.getElementById('readme-name-input').value || 'DevPulse Suite';
      const description = document.getElementById('readme-desc-input').value;

      btnGenReadme.disabled = true;
      try {
        const resp = await fetch('/api/docs/readme', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_name: projectName,
            description: description,
            features: [
              'Zero-copy generator pipelines for low memory footprint',
              'Automated docstring synthesis and injection',
              'GitHub & GitLab PR and CI/CD workflow automation'
            ],
            tech_stack: ['Python 3.12', 'Flask', 'Tracemalloc', 'GitHub Actions'],
            code_sample: code
          })
        });
        const data = await resp.json();
        if (data.success) {
          docOutput.textContent = data.readme;
          showToast('README.md synthesized successfully!');
        }
      } catch (err) {
        showToast('README synthesis failed: ' + err.message, 'error');
      } finally {
        btnGenReadme.disabled = false;
      }
    });
  }

  if (btnGenTests) {
    btnGenTests.addEventListener('click', async () => {
      const code = codeEditor.value;
      if (!code.trim()) return showToast('Please enter Python code.', 'error');

      btnGenTests.disabled = true;
      try {
        const resp = await fetch('/api/code/tests', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code, framework: 'pytest' })
        });
        const data = await resp.json();
        if (data.success) {
          docOutput.textContent = data.test_code;
          showToast(`Scaffolded ${data.functions_tested.length} pytest unit tests!`);
        } else {
          showToast(data.error || 'Test scaffolding failed', 'error');
        }
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
      } finally {
        btnGenTests.disabled = false;
      }
    });
  }

  if (btnGenModels) {
    btnGenModels.addEventListener('click', async () => {
      const schemaJson = document.getElementById('model-schema-input').value;
      const modelType = document.getElementById('model-type-select').value;

      btnGenModels.disabled = true;
      try {
        const resp = await fetch('/api/code/boilerplate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ schema_json: schemaJson, model_type: modelType })
        });
        const data = await resp.json();
        if (data.success) {
          docOutput.textContent = data.code;
          showToast(`Generated memory-efficient ${modelType} data model!`);
        } else {
          showToast(data.error || 'Model generation failed', 'error');
        }
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
      } finally {
        btnGenModels.disabled = false;
      }
    });
  }

  if (btnCopyDocOutput) {
    btnCopyDocOutput.addEventListener('click', () => {
      copyToClipboard(docOutput.textContent);
    });
  }
}

/* ========================================================================= */
/* GITHUB & GITLAB HUB MODULE                                                */
/* ========================================================================= */

function initGitModule() {
  const btnDiffToPr = document.getElementById('btn-diff-to-pr');
  const btnGenCommit = document.getElementById('btn-gen-commit');
  const btnGenCicd = document.getElementById('btn-gen-cicd');
  const btnFetchRepo = document.getElementById('btn-fetch-repo');
  const btnCopyGitOutput = document.getElementById('btn-copy-git-output');
  const gitOutput = document.getElementById('git-result-output');

  if (btnDiffToPr) {
    btnDiffToPr.addEventListener('click', async () => {
      const diff = document.getElementById('git-diff-input').value;
      const context = document.getElementById('git-pr-context').value;
      if (!diff.trim()) return showToast('Please paste a git diff.', 'error');

      btnDiffToPr.disabled = true;
      try {
        const resp = await fetch('/api/git/diff-to-pr', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ diff, context })
        });
        const data = await resp.json();
        if (data.success) {
          document.getElementById('pr-title-display').textContent = data.title;
          gitOutput.textContent = data.body_markdown;
          showToast(`PR Description generated: ${data.diff_stats.files_count} file(s) changed.`);
        }
      } catch (err) {
        showToast('Diff to PR failed: ' + err.message, 'error');
      } finally {
        btnDiffToPr.disabled = false;
      }
    });
  }

  if (btnGenCommit) {
    btnGenCommit.addEventListener('click', async () => {
      const desc = document.getElementById('commit-desc-input').value;
      const scope = document.getElementById('commit-scope-input').value;
      const type = document.getElementById('commit-type-select').value;
      const breaking = document.getElementById('commit-breaking-check').checked;

      btnGenCommit.disabled = true;
      try {
        const resp = await fetch('/api/git/commit-msg', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ description: desc, scope, type, breaking })
        });
        const data = await resp.json();
        if (data.success) {
          document.getElementById('pr-title-display').textContent = data.commit_message;
          gitOutput.textContent = `# Conventional Commit Formatted:\n\n${data.commit_message}\n\n# CLI Shortcut:\ngit commit -m "${data.commit_message}"`;
          showToast('Conventional commit message synthesized!');
        }
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
      } finally {
        btnGenCommit.disabled = false;
      }
    });
  }

  if (btnGenCicd) {
    btnGenCicd.addEventListener('click', async () => {
      const platform = document.getElementById('cicd-platform-select').value;
      const checkMemory = document.getElementById('cicd-memory-check').checked;

      btnGenCicd.disabled = true;
      try {
        const resp = await fetch('/api/git/cicd', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ platform, check_memory: checkMemory })
        });
        const data = await resp.json();
        if (data.success) {
          gitOutput.textContent = data.pipeline_yaml;
          showToast(`Generated ${platform === 'github' ? 'GitHub Actions' : 'GitLab CI'} pipeline!`);
        }
      } catch (err) {
        showToast('CI/CD generation failed: ' + err.message, 'error');
      } finally {
        btnGenCicd.disabled = false;
      }
    });
  }

  if (btnFetchRepo) {
    btnFetchRepo.addEventListener('click', async () => {
      const platform = document.getElementById('remote-platform-select').value;
      const repo = document.getElementById('remote-repo-input').value || 'demo';
      const token = document.getElementById('remote-token-input').value;

      btnFetchRepo.disabled = true;
      try {
        const resp = await fetch('/api/git/fetch-repo', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ platform, repo, token })
        });
        const data = await resp.json();
        renderRemoteRepoDetails(data);
        showToast(`Loaded ${data.is_mock ? 'Sandbox Demo' : 'Live'} Repo: ${data.name}`);
      } catch (err) {
        showToast('Repo fetch failed: ' + err.message, 'error');
      } finally {
        btnFetchRepo.disabled = false;
      }
    });
  }

  if (btnCopyGitOutput) {
    btnCopyGitOutput.addEventListener('click', () => {
      copyToClipboard(gitOutput.textContent);
    });
  }
}

function renderRemoteRepoDetails(data) {
  const container = document.getElementById('remote-repo-details');
  if (!container) return;

  container.innerHTML = `
    <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <span style="font-weight: 700; color: var(--accent-cyan); font-size: 1rem;">${data.full_name || data.name}</span>
        <span style="font-size: 0.75rem; background: rgba(255,255,255,0.08); padding: 0.2rem 0.5rem; border-radius: 4px;">
          ${data.is_mock ? 'Sandbox Sandbox Mode' : 'Live Remote'}
        </span>
      </div>
      <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.8rem;">
        ${data.description || 'No description'}
      </div>
      <div style="display: flex; gap: 1rem; font-size: 0.82rem; font-family: var(--font-mono); color: var(--text-muted);">
        <span>⭐ Stars: ${data.stars || 0}</span>
        <span>🍴 Forks: ${data.forks || 0}</span>
        <span>🌿 Default: ${data.default_branch || 'main'}</span>
        <span>🐛 Issues: ${data.open_issues || 0}</span>
      </div>
    </div>
  `;
}

/* ========================================================================= */
/* PRESETS MODULE                                                            */
/* ========================================================================= */

let cachedPresets = {};

async function initPresetsModule() {
  try {
    const resp = await fetch('/api/presets');
    const data = await resp.json();
    if (data.success) {
      cachedPresets = data.presets;
      renderPresetsGrid(cachedPresets);
    }
  } catch (err) {
    console.error('Failed to load presets:', err);
  }
}

function renderPresetsGrid(presets) {
  const container = document.getElementById('presets-grid-container');
  if (!container) return;

  container.innerHTML = Object.values(presets).map(p => `
    <div class="preset-card" onclick="triggerPreset('${p.id}')">
      <div>
        <div class="preset-category">${p.category}</div>
        <div class="preset-title">${p.title}</div>
        <div class="preset-desc">${p.description}</div>
      </div>
      <button class="btn btn-secondary btn-sm" style="align-self: flex-start;">
        Load Scenario →
      </button>
    </div>
  `).join('');
}

window.triggerPreset = function(presetId) {
  const preset = cachedPresets[presetId];
  if (!preset) return;

  if (preset.category === 'Memory') {
    activateTab('tab-memory');
    const editor = document.getElementById('mem-code-editor');
    if (editor) {
      editor.value = preset.code;
      showToast(`Loaded preset: ${preset.title}`);
      // Trigger scan automatically
      document.getElementById('btn-mem-scan').click();
    }
  } else if (preset.category === 'Documentation') {
    activateTab('tab-docs');
    const editor = document.getElementById('docs-code-editor');
    if (editor) {
      editor.value = preset.code;
      showToast(`Loaded preset: ${preset.title}`);
      document.getElementById('btn-gen-docs').click();
    }
  } else if (preset.category === 'Git') {
    activateTab('tab-git');
    const diffInput = document.getElementById('git-diff-input');
    if (diffInput) {
      diffInput.value = preset.diff;
      showToast(`Loaded preset: ${preset.title}`);
      document.getElementById('btn-diff-to-pr').click();
    }
  } else if (preset.category === 'Boilerplate') {
    activateTab('tab-docs');
    const schemaInput = document.getElementById('model-schema-input');
    if (schemaInput) {
      schemaInput.value = preset.json;
      showToast(`Loaded preset: ${preset.title}`);
      document.getElementById('btn-gen-models').click();
    }
  }
};

function loadPresetById(presetId, targetEditorId) {
  const preset = cachedPresets[presetId];
  if (!preset) return;
  const target = document.getElementById(targetEditorId);
  if (target && preset.code) {
    target.value = preset.code;
    showToast(`Loaded preset: ${preset.title}`);
  }
}

function loadDefaultPreset() {
  setTimeout(() => {
    if (cachedPresets['memory_streaming']) {
      const editor = document.getElementById('mem-code-editor');
      if (editor && !editor.value.trim()) {
        editor.value = cachedPresets['memory_streaming'].code;
        document.getElementById('btn-mem-scan').click();
      }
    }
    if (cachedPresets['docs_api_pipeline']) {
      const docsEditor = document.getElementById('docs-code-editor');
      if (docsEditor && !docsEditor.value.trim()) {
        docsEditor.value = cachedPresets['docs_api_pipeline'].code;
      }
    }
    if (cachedPresets['sample_git_diff']) {
      const diffInput = document.getElementById('git-diff-input');
      if (diffInput && !diffInput.value.trim()) {
        diffInput.value = cachedPresets['sample_git_diff'].diff;
      }
    }
    if (cachedPresets['sample_schema_json']) {
      const schemaInput = document.getElementById('model-schema-input');
      if (schemaInput && !schemaInput.value.trim()) {
        schemaInput.value = cachedPresets['sample_schema_json'].json;
      }
    }
  }, 400);
}
