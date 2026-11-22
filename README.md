# AutoSec Cloud 🛡️

**An Intent-Driven DevSecOps Engine with DPDP Compliance-as-Code and Automated FinOps Cost Control**

*Department of Computer Science and Engineering (Cyber Security), Sri Krishna College of Engineering and Technology*

---

## 📌 Executive Summary

**AutoSec Cloud** is a self-service DevSecOps orchestration platform. Developers deploy secure, budget-capped, DPDP-compliant web applications simply by uploading a `.zip` codebase archive and providing a 3-question **Intent Form** (Budget Tier, Security Tier, DPDP Toggle).

The platform automatically:
1. Validates zip extraction paths against **Zip-Slip vulnerability (CWE-22)**.
2. Executes a **Shift-Left Security Gate** (Trivy + Semgrep + Built-in SAST/Secret scanner) to block deployment if `CRITICAL` or `HIGH` severity vulnerabilities are detected.
3. Performs **zero-touch containerization**, auto-detecting application runtime (Python or Node.js) and generating dynamic Dockerfiles.
4. Enforces **DPDP Compliance-as-Code** (forcing `ap-south-1` Mumbai region lock, customer-managed KMS AES-256 keys, and audit tags).
5. Controls cloud spend via **FinOps Auto-Pause** monitoring.

---

## 🏗️ Project Architecture (Semester 1 Local Pipeline)

```text
capstone-full/
├── frontend/
│   ├── index.html        # Glassmorphic Intent Dashboard UI
│   ├── style.css         # Custom theme styling & severity badges
│   └── app.js            # Multipart upload & interactive visualizer logic
├── backend/
│   ├── main.py           # FastAPI application & REST endpoints
│   ├── file_manager.py   # Zip-Slip path traversal guard (CWE-22)
│   ├── security_gate.py  # Trivy + Semgrep + Fallback SAST/CVE engine
│   └── container_engine.py # Auto language detector & Docker build simulator
├── test_repos/
│   ├── vulnerable_python/# Sample repo with hardcoded AWS keys & vulnerable requirements
│   ├── vulnerable_node/  # Sample repo with dangerous eval/exec calls & lodash
│   ├── clean_python/     # Clean Python FastAPI sample project
│   └── clean_node/       # Clean Express.js sample project
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

---

## 🚀 Running the Project Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the FastAPI Server
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

### 3. Access the Intent Dashboard
Open your browser and navigate to:
```text
http://localhost:8000
```

---

## 🧪 Testing with Bundled Sample Repositories

The Intent Dashboard features **1-Click Quick Test Buttons**:

| Sample Repository | Language | Seeded Flaws | Expected Verdict |
| :--- | :--- | :--- | :--- |
| `vulnerable_python` | Python | Hardcoded AWS Access Key (`AKIA...`), `eval()` call, outdated Flask | ⛔ **BLOCKED** |
| `vulnerable_node` | Node.js | Hardcoded JWT Secret, `child_process.exec()`, outdated lodash | ⛔ **BLOCKED** |
| `clean_python` | Python | Environment variable config, clean FastAPI routes | ✅ **PASSED** |
| `clean_node` | Node.js | Express app with security headers & clean dependencies | ✅ **PASSED** |

---

## 🇮🇳 Digital Personal Data Protection (DPDP) Act 2023 Statutory Mapping

| DPDP Obligation | Statutory Basis | AutoSec Cloud Feature |
| :--- | :--- | :--- |
| **Reasonable Security Safeguards** | Sec. 8(5) | Pre-deployment Shift-Left Security Gate & Customer-Managed KMS Key (AES-256) |
| **Technical Observance Measures** | Sec. 8(4) | Mandatory Trivy & Semgrep SAST blocking gate |
| **Data Residency Scoping** | Policy Intent | Automatic region-lock to `ap-south-1` (Mumbai) under DPDP toggle |
| **Audit Compliance** | Sec. 8(4) | Automated `compliance: dpdp-ready` audit resource tagging |
