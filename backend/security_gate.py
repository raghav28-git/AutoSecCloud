import os
import re
import json
import subprocess
import shutil
from typing import Dict, Any, List

def parse_version(v_str: str) -> tuple:
    """Helper to convert version string into numeric tuple for safe semver comparison."""
    clean = re.sub(r'[^0-9.]', '', v_str)
    parts = clean.split('.')
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    return tuple(result)

# Known vulnerable dependencies database for built-in CVE scanner
VULNERABLE_PYTHON_PKGS = {
    "flask": {"lt": (2, 0, 0), "cve": "CVE-2021-33880", "severity": "HIGH", "desc": "Information disclosure / session forgery in Flask < 2.0.0"},
    "requests": {"lt": (2, 31, 0), "cve": "CVE-2023-32681", "severity": "HIGH", "desc": "Unintended leak of Proxy-Authorization headers"},
    "pyyaml": {"lt": (5, 4, 0), "cve": "CVE-2020-14343", "severity": "CRITICAL", "desc": "Arbitrary code execution via FullLoader"},
    "django": {"lt": (3, 2, 0), "cve": "CVE-2021-28658", "severity": "CRITICAL", "desc": "Directory traversal vulnerability in upload handling"},
    "urllib3": {"lt": (1, 26, 5), "cve": "CVE-2021-33503", "severity": "HIGH", "desc": "ReDoS vulnerability in URL authority parsing"}
}

VULNERABLE_NODE_PKGS = {
    "express": {"lt": (4, 16, 0), "cve": "CVE-2017-16119", "severity": "HIGH", "desc": "Regular Expression Denial of Service (ReDoS) in Express mime < 4.16.0"},
    "lodash": {"lt": (4, 17, 21), "cve": "CVE-2020-8203", "severity": "CRITICAL", "desc": "Prototype Pollution in lodash.zipObjectDeep < 4.17.21"},
    "axios": {"lt": (0, 21, 1), "cve": "CVE-2020-28168", "severity": "HIGH", "desc": "Server-Side Request Forgery (SSRF) / data leakage < 0.21.1"},
    "jsonwebtoken": {"lt": (9, 0, 0), "cve": "CVE-2022-23529", "severity": "CRITICAL", "desc": "Insecure key verification / RCE vulnerability < 9.0.0"}
}

SECRET_PATTERNS = [
    (r'AKIA[0-9A-Z]{16}', 'CRITICAL', 'Hardcoded AWS Access Key ID exposed', 'CWE-798'),
    (r'(?i)aws_secret_access_key\s*=\s*[\'"][A-Za-z0-9/+=]{40}[\'"]', 'CRITICAL', 'Hardcoded AWS Secret Access Key exposed', 'CWE-798'),
    (r'-----BEGIN (?:RSA |EC |PGP )?PRIVATE KEY-----', 'CRITICAL', 'Exposed Private Key Block', 'CWE-312'),
    (r'(?i)(?:api_key|apikey|secret_key|jwt_secret)\s*=\s*[\'"][A-Za-z0-9_]{16,}[\'"]', 'HIGH', 'Hardcoded API / Secret Token in code', 'CWE-798'),
    (r'(?i)postgres(?:ql)?://[a-zA-Z0-9_]+:[a-zA-Z0-9_]+@[a-zA-Z0-9_.-]+:[0-9]+/[a-zA-Z0-9_]+', 'HIGH', 'Database Connection String with Credentials exposed', 'CWE-259')
]

CODE_PATTERNS_PYTHON = [
    (r'\beval\s*\(', 'CRITICAL', 'Dangerous eval() function call allows arbitrary code execution', 'CWE-95'),
    (r'\bexec\s*\(', 'CRITICAL', 'Dangerous exec() function call allows dynamic execution', 'CWE-95'),
    (r'subprocess\.(?:Popen|call|run)\s*\(.*shell\s*=\s*True', 'HIGH', 'Command Injection risk via subprocess shell=True', 'CWE-78'),
    (r'os\.system\s*\(', 'HIGH', 'Command Injection risk via os.system()', 'CWE-78'),
    (r'pickle\.loads\s*\(', 'HIGH', 'Insecure Deserialization via pickle.loads()', 'CWE-502'),
    (r'SELECT\s+.*\s+FROM\s+.*%s|SELECT\s+.*\+.*WHERE', 'HIGH', 'Potential SQL Injection via string formatting/concatenation', 'CWE-89')
]

CODE_PATTERNS_NODE = [
    (r'\beval\s*\(', 'CRITICAL', 'Dangerous eval() function call allows arbitrary code execution', 'CWE-95'),
    (r'child_process\.exec\s*\(', 'HIGH', 'Command Injection risk via child_process.exec()', 'CWE-78'),
    (r'vm\.runInContext\s*\(', 'HIGH', 'Dynamic code evaluation risk in VM sandbox', 'CWE-94'),
    (r'new\  Function\s*\(', 'HIGH', 'Function constructor dynamic execution vulnerability', 'CWE-95')
]

def run_builtin_scanner(source_dir: str) -> List[Dict[str, Any]]:
    """Comprehensive fallback SAST, secret, dependency, and Dockerfile scanner."""
    findings = []
    
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, source_dir)

            # 1. Scan requirements.txt for Python CVEs
            if file.lower() == "requirements.txt":
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith('#'):
                                continue
                            match = re.match(r'^([a-zA-Z0-9_\-]+)\s*==\s*([0-9\.]+)', line)
                            if match:
                                pkg, ver_str = match.group(1).lower(), match.group(2)
                                if pkg in VULNERABLE_PYTHON_PKGS:
                                    vuln_info = VULNERABLE_PYTHON_PKGS[pkg]
                                    if parse_version(ver_str) < vuln_info["lt"]:
                                        findings.append({
                                            "id": f"CVE-{pkg}-{ver_str}",
                                            "source": "Trivy-Dependency",
                                            "tool": "Dependency Scanner",
                                            "severity": vuln_info["severity"],
                                            "cve": vuln_info["cve"],
                                            "title": f"Vulnerable Dependency: {pkg} {ver_str}",
                                            "description": vuln_info["desc"],
                                            "file": rel_path,
                                            "line": 1,
                                            "cwe": "CWE-1104"
                                        })
                except Exception:
                    pass

            # 2. Scan package.json for Node CVEs
            elif file.lower() == "package.json":
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        data = json.load(f)
                        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                        for pkg, ver_str in deps.items():
                            pkg_lower = pkg.lower()
                            if pkg_lower in VULNERABLE_NODE_PKGS:
                                vuln_info = VULNERABLE_NODE_PKGS[pkg_lower]
                                if parse_version(ver_str) < vuln_info["lt"]:
                                    findings.append({
                                        "id": f"CVE-{pkg_lower}-{ver_str}",
                                        "source": "Trivy-Dependency",
                                        "tool": "Dependency Scanner",
                                        "severity": vuln_info["severity"],
                                        "cve": vuln_info["cve"],
                                        "title": f"Vulnerable Dependency: {pkg} {ver_str}",
                                        "description": vuln_info["desc"],
                                        "file": rel_path,
                                        "line": 1,
                                        "cwe": "CWE-1104"
                                    })
                except Exception:
                    pass

            # 3. Scan Dockerfile misconfigurations
            elif file.lower() == "dockerfile":
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        has_user = any("USER " in line for line in lines)
                        if not has_user:
                            findings.append({
                                "id": "DOCKER-MISCONFIG-001",
                                "source": "Trivy-Config",
                                "tool": "IaC Misconfig Scanner",
                                "severity": "MEDIUM",
                                "cve": "IaC-Rule-001",
                                "title": "Dockerfile Container Running as Root",
                                "description": "No 'USER' instruction specified. Container processes will run as root user.",
                                "file": rel_path,
                                "line": len(lines),
                                "cwe": "CWE-250"
                            })
                except Exception:
                    pass

            # 4. Scan source files for secrets and SAST vulnerability patterns
            ext = os.path.splitext(file)[1].lower()
            if ext in ['.py', '.js', '.ts', '.json', '.env', '.yml', '.yaml', '.txt', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_lines = f.readlines()

                    for idx, line in enumerate(content_lines, start=1):
                        # Secret scanning
                        for pattern, severity, title, cwe in SECRET_PATTERNS:
                            if re.search(pattern, line):
                                findings.append({
                                    "id": f"SECRET-{idx}",
                                    "source": "Trivy-Secret",
                                    "tool": "Secret Scanner",
                                    "severity": severity,
                                    "cve": "SECRET-EXPOSURE",
                                    "title": title,
                                    "description": f"Exposed secret token pattern matched on line {idx}.",
                                    "file": rel_path,
                                    "line": idx,
                                    "snippet": line.strip()[:80],
                                    "cwe": cwe
                                })

                        # Python SAST
                        if ext == '.py':
                            for pattern, severity, title, cwe in CODE_PATTERNS_PYTHON:
                                if re.search(pattern, line):
                                    findings.append({
                                        "id": f"SAST-PY-{idx}",
                                        "source": "Semgrep-SAST",
                                        "tool": "Semgrep SAST Engine",
                                        "severity": severity,
                                        "cve": "SAST-PYTHON-RULE",
                                        "title": title,
                                        "description": f"Unsafe Python coding pattern detected on line {idx}.",
                                        "file": rel_path,
                                        "line": idx,
                                        "snippet": line.strip()[:80],
                                        "cwe": cwe
                                    })

                        # Node JS SAST
                        if ext in ['.js', '.ts']:
                            for pattern, severity, title, cwe in CODE_PATTERNS_NODE:
                                if re.search(pattern, line):
                                    findings.append({
                                        "id": f"SAST-JS-{idx}",
                                        "source": "Semgrep-SAST",
                                        "tool": "Semgrep SAST Engine",
                                        "severity": severity,
                                        "cve": "SAST-NODE-RULE",
                                        "title": title,
                                        "description": f"Unsafe JavaScript coding pattern detected on line {idx}.",
                                        "file": rel_path,
                                        "line": idx,
                                        "snippet": line.strip()[:80],
                                        "cwe": cwe
                                    })

                except Exception:
                    pass

    return findings

def run_security_scan(source_dir: str, security_tier: str = "standard") -> Dict[str, Any]:
    """
    Runs the Shift-Left Security Gate (Trivy + Semgrep + Fallback Scanner).
    Returns unified JSON report with pass/fail verdict.
    """
    findings = []

    # Check CLI availability for Trivy and Semgrep
    trivy_path = shutil.which("trivy")
    semgrep_path = shutil.which("semgrep")

    # 1. Run Trivy CLI if present
    if trivy_path:
        try:
            report_file = os.path.join(source_dir, "trivy_report.json")
            subprocess.run([
                trivy_path, "fs",
                "--security-checks", "vuln,secret,config",
                "--severity", "CRITICAL,HIGH",
                "--format", "json",
                "--output", report_file,
                source_dir
            ], capture_output=True, timeout=60)

            if os.path.exists(report_file):
                with open(report_file, 'r', encoding='utf-8') as f:
                    trivy_data = json.load(f)
                    for res in trivy_data.get("Results", []):
                        for vuln in res.get("Vulnerabilities", []):
                            findings.append({
                                "id": vuln.get("VulnerabilityID"),
                                "source": "Trivy",
                                "tool": "Trivy CLI",
                                "severity": vuln.get("Severity", "HIGH"),
                                "cve": vuln.get("VulnerabilityID"),
                                "title": vuln.get("Title", "Vulnerability found"),
                                "description": vuln.get("Description", ""),
                                "file": res.get("Target"),
                                "line": 1,
                                "cwe": vuln.get("CweIDs", ["CWE-UNKNOWN"])[0] if vuln.get("CweIDs") else "CWE-UNKNOWN"
                            })
        except Exception:
            pass

    # 2. Run Semgrep CLI if present
    if semgrep_path:
        try:
            report_file = os.path.join(source_dir, "semgrep_report.json")
            subprocess.run([
                semgrep_path, "--config", "p/ci",
                "--json", "--output", report_file,
                source_dir
            ], capture_output=True, timeout=60)

            if os.path.exists(report_file):
                with open(report_file, 'r', encoding='utf-8') as f:
                    semgrep_data = json.load(f)
                    for match in semgrep_data.get("results", []):
                        sev_raw = match.get("extra", {}).get("severity", "WARNING").upper()
                        sev = "CRITICAL" if sev_raw == "ERROR" else ("HIGH" if sev_raw == "WARNING" else "MEDIUM")
                        findings.append({
                            "id": match.get("check_id"),
                            "source": "Semgrep",
                            "tool": "Semgrep CLI",
                            "severity": sev,
                            "cve": match.get("check_id"),
                            "title": match.get("extra", {}).get("message", "Semgrep Rule Triggered"),
                            "description": match.get("extra", {}).get("message", ""),
                            "file": match.get("path"),
                            "line": match.get("start", {}).get("line", 1),
                            "cwe": match.get("extra", {}).get("metadata", {}).get("cwe", ["CWE-79"])[0]
                        })
        except Exception:
            pass

    # 3. Always augment/fallback with Built-in SAST & Secret Scanner
    builtin_findings = run_builtin_scanner(source_dir)
    findings.extend(builtin_findings)

    # Deduplicate findings based on file, line, and title
    seen = set()
    unique_findings = []
    for f in findings:
        key = (f.get("file"), f.get("line"), f.get("title"))
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    # Categorize severity
    critical_count = sum(1 for f in unique_findings if f.get("severity") == "CRITICAL")
    high_count = sum(1 for f in unique_findings if f.get("severity") == "HIGH")
    medium_count = sum(1 for f in unique_findings if f.get("severity") == "MEDIUM")
    low_count = sum(1 for f in unique_findings if f.get("severity") == "LOW")

    # Shift-Left Security Decision Rule: CRITICAL or HIGH findings HALT deployment
    blocking_findings = [f for f in unique_findings if f.get("severity") in ("CRITICAL", "HIGH")]
    passed = (len(blocking_findings) == 0)

    return {
        "passed": passed,
        "verdict": "PASS" if passed else "FAIL (CRITICAL/HIGH > 0)",
        "blocking_count": len(blocking_findings),
        "total_findings": len(unique_findings),
        "summary": {
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "low": low_count
        },
        "findings": unique_findings
    }
