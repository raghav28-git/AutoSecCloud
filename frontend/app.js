// Procedural WebGL / Canvas Data-Stream Flow Field Renderer
(function initCanvasBackground() {
    const canvas = document.getElementById('dataStreamCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const particleCount = 45;

    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.8,
            vy: (Math.random() - 0.5) * 0.8,
            radius: Math.random() * 2 + 1,
            color: Math.random() > 0.5 ? 'rgba(0, 245, 255, ' : 'rgba(139, 92, 246, ',
            alpha: Math.random() * 0.5 + 0.2
        });
    }

    function renderFrame() {
        ctx.clearRect(0, 0, width, height);

        // Draw connecting lines between close particles
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 140) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(0, 245, 255, ${0.15 * (1 - dist / 140)})`;
                    ctx.lineWidth = 0.8;
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.stroke();
                }
            }
        }

        // Draw and move particles
        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fillStyle = p.color + p.alpha + ')';
            ctx.shadowBlur = 10;
            ctx.shadowColor = '#00F5FF';
            ctx.fill();
            ctx.shadowBlur = 0;
        });

        requestAnimationFrame(renderFrame);
    }

    renderFrame();
})();

// DOM Interactions & Deployment Logic
document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("dropZone");
    const codeZipInput = document.getElementById("codeZip");
    const selectedFileInfo = document.getElementById("selectedFileInfo");
    const fileNameText = document.getElementById("fileNameText");
    const btnClearFile = document.getElementById("btnClearFile");
    const deployForm = document.getElementById("deployForm");

    // Tier Selector Radio Handling
    const tierBoxes = document.querySelectorAll(".tier-box");
    tierBoxes.forEach(box => {
        box.addEventListener("click", () => {
            tierBoxes.forEach(b => b.classList.remove("active-cyan"));
            box.classList.add("active-cyan");
            const radio = box.querySelector("input[type='radio']");
            if (radio) radio.checked = true;
        });
    });

    // Drag & Drop
    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            codeZipInput.files = files;
            updateFileInfo();
        }
    });

    codeZipInput.addEventListener('change', updateFileInfo);

    btnClearFile.addEventListener('click', (e) => {
        e.stopPropagation();
        codeZipInput.value = "";
        selectedFileInfo.classList.add("hidden");
    });

    function updateFileInfo() {
        if (codeZipInput.files.length > 0) {
            const f = codeZipInput.files[0];
            fileNameText.textContent = `${f.name} (${(f.size / 1024).toFixed(1)} KB)`;
            selectedFileInfo.classList.remove("hidden");
        }
    }

    // Form Submit
    deployForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (codeZipInput.files.length === 0) {
            alert("Please select a .zip codebase archive or click one of the 1-Click Quick Test Repositories.");
            return;
        }

        const selectedRadio = document.querySelector("input[name='budget_tier_radio']:checked");
        const budgetTier = selectedRadio ? selectedRadio.value : "medium";

        const formData = new FormData();
        formData.append("file", codeZipInput.files[0]);
        formData.append("budget_tier", budgetTier);
        formData.append("security_tier", document.getElementById("securityTier").value);
        formData.append("dpdp_enabled", document.getElementById("dpdpToggle").checked);

        await executePipeline("/api/deploy", formData);
    });
});

// Tab Switching
function switchTab(tabId) {
    document.querySelectorAll(".feed-tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));

    const targetPanel = document.getElementById(tabId);
    if (targetPanel) targetPanel.classList.add("active");

    const activeBtn = Array.from(document.querySelectorAll(".feed-tab-btn")).find(b => b.getAttribute("onclick").includes(tabId));
    if (activeBtn) activeBtn.classList.add("active");
}

// 1-Click Sample Repository Trigger
async function deploySample(sampleId) {
    const selectedRadio = document.querySelector("input[name='budget_tier_radio']:checked");
    const budgetTier = selectedRadio ? selectedRadio.value : "medium";

    const formData = new FormData();
    formData.append("budget_tier", budgetTier);
    formData.append("security_tier", document.getElementById("securityTier").value);
    formData.append("dpdp_enabled", document.getElementById("dpdpToggle").checked);

    await executePipeline(`/api/deploy-sample/${sampleId}`, formData);
}

// Multi-Step Pipeline Visualizer with Glowing Neon Connectors
async function executePipeline(url, formData) {
    const idleView = document.getElementById("idleView");
    const pipelineProgress = document.getElementById("pipelineProgress");
    const resultsContainer = document.getElementById("resultsContainer");
    const deployBtn = document.getElementById("deployBtn");
    const stateBadge = document.getElementById("pipelineStateBadge");

    idleView.classList.add("hidden");
    resultsContainer.classList.add("hidden");
    pipelineProgress.classList.remove("hidden");
    deployBtn.disabled = true;

    stateBadge.textContent = "Scanning...";
    stateBadge.style.color = "#00F5FF";

    resetFlowStepper();

    // Step 1: Intake & Zip-Slip Protection Check
    setFlowStep("step1", "active");
    await sleep(400);
    setFlowStep("step1", "completed");
    setConnector("conn1", "active");

    // Step 2: SAST Gate
    setFlowStep("step2", "active");

    try {
        const response = await fetch(url, {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (result.status === "BLOCKED" || result.passed === false) {
            setFlowStep("step2", "failed");
            setConnector("conn2", "failed");
            stateBadge.textContent = "BLOCKED";
            stateBadge.style.color = "#EF4444";
            renderThreatFeed(result);
        } else {
            setFlowStep("step2", "completed");
            setConnector("conn2", "active");

            // Step 3: Container Build
            setFlowStep("step3", "active");
            await sleep(400);
            setFlowStep("step3", "completed");
            setConnector("conn3", "active");

            // Step 4: Governance Verification
            setFlowStep("step4", "active");
            await sleep(300);
            setFlowStep("step4", "completed");

            stateBadge.textContent = "PASSED";
            stateBadge.style.color = "#10B981";
            renderSuccessFeed(result);
        }

    } catch (err) {
        setFlowStep("step2", "failed");
        stateBadge.textContent = "ERROR";
        stateBadge.style.color = "#EF4444";
        renderErrorFeed(err.message);
    } finally {
        deployBtn.disabled = false;
        resultsContainer.classList.remove("hidden");
        switchTab("auditTab");
    }
}

function resetFlowStepper() {
    ['step1', 'step2', 'step3', 'step4'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = "flow-step";
    });
    ['conn1', 'conn2', 'conn3'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = "flow-connector";
    });
}

function setFlowStep(id, state) {
    const el = document.getElementById(id);
    if (el) el.className = `flow-step ${state}`;
}

function setConnector(id, state) {
    const el = document.getElementById(id);
    if (el) el.className = `flow-connector ${state}`;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Render Threat Feed for Blocked Verdict
function renderThreatFeed(result) {
    const scan = result.scan_results || {};
    const findings = scan.findings || [];
    const summary = scan.summary || { critical: 0, high: 0, medium: 0, low: 0 };

    // Tab 1: Threat Feed Cards with High-Intensity Red Glow
    let auditHtml = `
        <div class="threat-card" style="border-color: rgba(239, 68, 68, 0.8); margin-bottom: 1.25rem;">
            <div class="threat-head">
                <span class="threat-title" style="color: #FCA5A5;">⛔ DEPLOYMENT HALTED BY SHIFT-LEFT GATE</span>
                <span class="severity-badge sev-critical">BLOCKED</span>
            </div>
            <p style="font-size: 0.85rem; color: #CBD5E1;">
                ${escapeHtml(result.message)}
            </p>
        </div>

        <h3 style="font-size: 1rem; margin-bottom: 0.8rem; font-weight: 800;">🚨 Critical Vulnerability Threat Feed (${findings.length})</h3>
        <div class="threat-feed-container">
    `;

    if (findings.length > 0) {
        findings.forEach(f => {
            auditHtml += `
                <div class="threat-card ${f.severity}">
                    <div class="threat-head">
                        <span class="threat-title">${escapeHtml(f.title)}</span>
                        <span class="severity-badge sev-${f.severity.toLowerCase()}">${f.severity}</span>
                    </div>
                    <div class="threat-meta">
                        Tool: ${f.tool} &bull; File: <strong>${escapeHtml(f.file)}:L${f.line}</strong> &bull; ${f.cwe || 'CWE-798'}
                    </div>
                    <p style="font-size: 0.82rem; color: #CBD5E1; margin-bottom: 0.6rem;">${escapeHtml(f.description)}</p>
                    ${f.snippet ? `<div class="threat-code-block">Line ${f.line}: ${escapeHtml(f.snippet)}</div>` : ''}
                </div>
            `;
        });
    } else {
        auditHtml += `<p class="text-muted">Zip-Slip path traversal or invalid payload detected.</p>`;
    }
    auditHtml += `</div>`;

    document.getElementById("auditTab").innerHTML = auditHtml;

    // Tab 2: Terminal Output
    document.getElementById("terminalTab").innerHTML = `
        <div class="cyber-terminal">
            <div class="terminal-header">
                <span>AutoSec Engine Execution Trace</span>
                <span style="color: #EF4444;">● HALTED</span>
            </div>
            <div class="terminal-body" style="color: #F43F5E;">
[AutoSec Shift-Left Security Gate] Starting filesystem vulnerability scan...
[Trivy & Semgrep Engine] Inspecting source files and package manifests...
[GATE VERDICT] FAIL (CRITICAL/HIGH > 0)
[DEPLOYMENT BLOCKED] Zero cloud or container resources provisioned.
[REMEDIATION] Remove exposed AWS keys or vulnerable dependencies listed in Threat Feed.
            </div>
        </div>
    `;

    // Tab 3: Governance
    document.getElementById("complianceTab").innerHTML = `
        <div class="governance-grid">
            <div class="gov-card">
                <h4>🇮🇳 DPDP Safeguard Enforced</h4>
                <div class="gov-item"><strong>Status:</strong> Active Security Safeguard</div>
                <div class="gov-item"><strong>Statutory Basis:</strong> DPDP Act 2023 Sec 8(4) & Sec 8(5)</div>
                <div class="gov-item"><strong>Outcome:</strong> Prevented vulnerable payload from reaching infrastructure</div>
            </div>
            <div class="gov-card">
                <h4>💰 FinOps Cost Control</h4>
                <div class="gov-item"><strong>Prevented Cloud Spend:</strong> $0.00 (Zero resources provisioned)</div>
                <div class="gov-item"><strong>Cost Status:</strong> Protected by Shift-Left Gate</div>
            </div>
        </div>
    `;
}

// Render Success Feed for Clean Code
function renderSuccessFeed(result) {
    const lang = result.language_detected || {};
    const build = result.container_build || {};
    const dpdp = result.dpdp_compliance || {};
    const finops = result.finops_governance || {};
    const buildLogs = (build.logs || []).join("\n");

    // Tab 1: Passed Banner & Overview
    document.getElementById("auditTab").innerHTML = `
        <div class="threat-card" style="border-color: rgba(16, 185, 129, 0.8); border-left-color: #10B981; box-shadow: 0 0 25px rgba(16, 185, 129, 0.3); margin-bottom: 1.25rem;">
            <div class="threat-head">
                <span class="threat-title" style="color: #6EE7B7;">✅ SECURITY SCAN PASSED & CONTAINER BUILT</span>
                <span class="severity-badge" style="background: rgba(16, 185, 129, 0.2); color: #6EE7B7;">${(lang.language || 'APP').toUpperCase()}</span>
            </div>
            <p style="font-size: 0.85rem; color: #CBD5E1;">
                Zero CRITICAL or HIGH vulnerabilities detected. Local container image generated successfully!
            </p>
        </div>

        <div class="governance-grid">
            <div class="gov-card">
                <h4>📦 Application Runtime</h4>
                <div class="gov-item"><strong>Language:</strong> ${lang.language}</div>
                <div class="gov-item"><strong>Framework:</strong> ${lang.framework}</div>
                <div class="gov-item"><strong>Base Image:</strong> <code>${lang.base_image}</code></div>
                <div class="gov-item"><strong>Exposed Port:</strong> ${lang.default_port}</div>
            </div>
            <div class="gov-card">
                <h4>🐳 Local Container Metadata</h4>
                <div class="gov-item"><strong>Engine:</strong> ${build.engine}</div>
                <div class="gov-item"><strong>Image Tag:</strong> <code>${build.image_tag}</code></div>
                <div class="gov-item"><strong>Dockerfile:</strong> Generated automatically</div>
            </div>
        </div>
    `;

    // Tab 2: Terminal Logs View
    document.getElementById("terminalTab").innerHTML = `
        <div class="cyber-terminal">
            <div class="terminal-header">
                <span>Docker Engine Terminal Log (${build.image_tag})</span>
                <span style="color: #10B981;">● BUILT</span>
            </div>
            <div class="terminal-body">${escapeHtml(buildLogs)}</div>
        </div>
    `;

    // Tab 3: Governance
    document.getElementById("complianceTab").innerHTML = `
        <div class="governance-grid">
            <div class="gov-card">
                <h4>🇮🇳 DPDP Compliance-as-Code</h4>
                <div class="gov-item"><strong>Status:</strong> ${dpdp.enabled ? 'ACTIVE (Sec 8 Safeguards Enforced)' : 'Disabled'}</div>
                <div class="gov-item"><strong>Region:</strong> ${dpdp.region}</div>
                <div class="gov-item"><strong>AES-256 Key:</strong> ${dpdp.encryption}</div>
                <div class="gov-item"><strong>KMS Key ARN:</strong> <code>${dpdp.kms_key_arn}</code></div>
                <div class="gov-item"><strong>Audit Tag:</strong> <code>${dpdp.compliance_tag}</code></div>
            </div>

            <div class="gov-card">
                <h4>💰 FinOps Cost Control</h4>
                <div class="gov-item"><strong>Budget Tier:</strong> ${finops.tier ? finops.tier.toUpperCase() : 'MEDIUM'} (${finops.monthly_cap})</div>
                <div class="gov-item"><strong>Max Instances:</strong> ${finops.max_instances} Service Cap</div>
                <div class="gov-item"><strong>Auto-Pause Monitor:</strong> ${finops.idle_auto_pause}</div>
                <div class="gov-item"><strong>Cost Governance:</strong> ${finops.cost_status}</div>
            </div>
        </div>
    `;
}

function renderErrorFeed(errMsg) {
    document.getElementById("auditTab").innerHTML = `
        <div class="threat-card" style="border-color: rgba(239, 68, 68, 0.8);">
            <div class="threat-head">
                <span class="threat-title" style="color: #FCA5A5;">❌ PIPELINE ERROR</span>
            </div>
            <p style="font-size: 0.85rem; color: #CBD5E1;">${escapeHtml(errMsg)}</p>
        </div>
    `;
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
