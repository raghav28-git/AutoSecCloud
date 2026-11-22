import os
import zipfile
import shutil
import tempfile
import uuid
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.file_manager import create_job_workspace, safe_extract_zip, cleanup_workspace
from backend.security_gate import run_security_scan
from backend.container_engine import detect_language_and_entrypoint, generate_dockerfile, build_container_image

app = FastAPI(
    title="AutoSec Cloud DevSecOps Engine",
    description="Intent-Driven DevSecOps Engine with DPDP Compliance-as-Code and FinOps Cost Control",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
TEST_REPOS_DIR = os.path.join(BASE_DIR, "test_repos")

@app.post("/api/deploy")
async def deploy(
    file: UploadFile = File(...),
    budget_tier: str = Form("medium"),
    security_tier: str = Form("standard"),
    dpdp_enabled: bool = Form(False)
):
    """
    Main deployment pipeline endpoint.
    Processes multipart upload -> Zip-Slip validation -> Security Gate -> Auto-Dockerfile -> Local Container Build.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip project archives are supported.")

    base_dir, extract_dir = create_job_workspace()
    zip_path = os.path.join(base_dir, "uploaded_codebase.zip")

    try:
        # Save uploaded zip file
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Zip-Slip Protected Extraction
        try:
            extracted_file_count = safe_extract_zip(zip_path, extract_dir)
        except ValueError as e:
            cleanup_workspace(base_dir)
            return JSONResponse(
                status_code=400,
                content={
                    "status": "BLOCKED",
                    "error_type": "Zip-Slip Path Traversal Security Block",
                    "message": str(e)
                }
            )

        # Handle nested single directory extraction if present
        sub_items = os.listdir(extract_dir)
        target_dir = extract_dir
        if len(sub_items) == 1 and os.path.isdir(os.path.join(extract_dir, sub_items[0])):
            target_dir = os.path.join(extract_dir, sub_items[0])

        # 2. Shift-Left Security Gate (Trivy + Semgrep + Fallback Scanner)
        scan_results = run_security_scan(target_dir, security_tier=security_tier)

        intent_summary = {
            "budget_tier": budget_tier,
            "security_tier": security_tier,
            "dpdp_enabled": dpdp_enabled,
            "filename": file.filename,
            "files_extracted": extracted_file_count
        }

        # If Security Gate Fails (CRITICAL or HIGH vulnerabilities present) -> HALT PIPELINE
        if not scan_results["passed"]:
            return {
                "status": "BLOCKED",
                "passed": False,
                "verdict": scan_results["verdict"],
                "message": f"Deployment HALTED: Security gate detected {scan_results['blocking_count']} blocking vulnerability finding(s). No container or cloud resources were provisioned.",
                "intent": intent_summary,
                "scan_results": scan_results
            }

        # 3. Language & Entrypoint Detection
        try:
            lang_info = detect_language_and_entrypoint(target_dir)
        except ValueError as ve:
            return JSONResponse(
                status_code=422,
                content={
                    "status": "BLOCKED",
                    "passed": False,
                    "message": str(ve),
                    "intent": intent_summary,
                    "scan_results": scan_results
                }
            )

        # 4. Auto-Generate Dockerfile
        dockerfile_content = generate_dockerfile(target_dir, lang_info)

        # 5. Build Container Image
        image_tag = f"autosec-{uuid.uuid4().hex[:8]}"
        build_result = build_container_image(target_dir, image_tag, lang_info)

        # 6. Metadata Simulation for DPDP & FinOps
        dpdp_metadata = {
            "enabled": dpdp_enabled,
            "region": "ap-south-1 (Mumbai)" if dpdp_enabled else "us-east-1 (N. Virginia - Default)",
            "encryption": "AWS KMS Customer-Managed Key (AES-256 at Rest)" if dpdp_enabled else "AWS Managed Default Key",
            "kms_key_arn": f"arn:aws:kms:ap-south-1:123456789012:key/dpdp-autosec-{image_tag}" if dpdp_enabled else "None",
            "compliance_tag": "compliance: dpdp-ready" if dpdp_enabled else "compliance: standard",
            "statutory_basis": "DPDP Act 2023 Sec 8(4), Sec 8(5) Data Safeguards" if dpdp_enabled else "Standard Deployment"
        }

        finops_metadata = {
            "tier": budget_tier,
            "monthly_cap": "$5/mo max" if budget_tier == "low" else ("$20/mo max" if budget_tier == "medium" else "$50/mo max"),
            "max_instances": 1 if budget_tier == "low" else (2 if budget_tier == "medium" else 5),
            "idle_auto_pause": "Active (CloudWatch Alarm -> Lambda Pause trigger after 15m idle)",
            "cost_status": "Budget Enforced"
        }

        return {
            "status": "SUCCESS",
            "passed": True,
            "verdict": scan_results["verdict"],
            "message": "Security scan PASSED cleanly! Container image built locally.",
            "intent": intent_summary,
            "language_detected": lang_info,
            "dockerfile": dockerfile_content,
            "container_build": build_result,
            "scan_results": scan_results,
            "dpdp_compliance": dpdp_metadata,
            "finops_governance": finops_metadata,
            "local_endpoint": f"http://localhost:{lang_info['default_port']}"
        }

    finally:
        cleanup_workspace(base_dir)

@app.get("/api/sample-repos")
def get_sample_repos():
    """Returns metadata for pre-bundled test sample repositories."""
    return [
        {
            "id": "vulnerable_python",
            "name": "Vulnerable Python App",
            "type": "Python",
            "description": "Seeded with hardcoded AWS Access Keys & vulnerable dependencies (Flask 0.12). Expected verdict: BLOCKED.",
            "expected_verdict": "BLOCKED"
        },
        {
            "id": "vulnerable_node",
            "name": "Vulnerable Node.js App",
            "type": "Node.js",
            "description": "Seeded with dangerous eval() calls, hardcoded JWT secrets & vulnerable lodash. Expected verdict: BLOCKED.",
            "expected_verdict": "BLOCKED"
        },
        {
            "id": "clean_python",
            "name": "Clean Python App",
            "type": "Python",
            "description": "Clean FastAPI microservice using environment variables. Expected verdict: SUCCESS.",
            "expected_verdict": "SUCCESS"
        },
        {
            "id": "clean_node",
            "name": "Clean Node.js App",
            "type": "Node.js",
            "description": "Clean Express.js microservice with helmet security headers. Expected verdict: SUCCESS.",
            "expected_verdict": "SUCCESS"
        }
    ]

@app.post("/api/deploy-sample/{sample_id}")
async def deploy_sample(
    sample_id: str,
    budget_tier: str = Form("medium"),
    security_tier: str = Form("standard"),
    dpdp_enabled: bool = Form(False)
):
    """Triggers deployment for one of the pre-bundled test sample repositories."""
    sample_path = os.path.join(TEST_REPOS_DIR, sample_id)
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail=f"Sample repo '{sample_id}' not found.")

    # Create temporary zip archive of the sample repo
    temp_zip_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_zip_dir, f"{sample_id}.zip")

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(sample_path):
                for file in files:
                    abs_file = os.path.join(root, file)
                    rel_file = os.path.relpath(abs_file, sample_path)
                    zf.write(abs_file, rel_file)

        # Open temporary zip file as an UploadFile equivalent and pass to deploy logic
        with open(zip_path, "rb") as f:
            upload_file = UploadFile(filename=f"{sample_id}.zip", file=f)
            return await deploy(
                file=upload_file,
                budget_tier=budget_tier,
                security_tier=security_tier,
                dpdp_enabled=dpdp_enabled
            )

    finally:
        shutil.rmtree(temp_zip_dir, ignore_errors=True)

# Serve Static Assets & Logo
LOGO_DIR = os.path.join(BASE_DIR, "logo")
if os.path.exists(LOGO_DIR):
    app.mount("/logo", StaticFiles(directory=LOGO_DIR), name="logo")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def read_root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    @app.get("/project")
    def read_project():
        return FileResponse(os.path.join(FRONTEND_DIR, "project.html"))
