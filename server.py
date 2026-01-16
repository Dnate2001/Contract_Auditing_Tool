#!/usr/bin/env python3
"""
FastAPI Service Mode for Smart Contract Security Auditor
Provides HTTP API for contract auditing with stateless design
"""

import os
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configuration
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
ARTIFACTS_DIR = DATA_DIR / "artifacts"
MODE = os.getenv("MODE", "simulation")
MEDUSA_TIMEOUT = int(os.getenv("MEDUSA_TIMEOUT", "60"))

# Ensure directories exist
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Smart Contract Security Auditor API",
    description="AI-powered vulnerability detection for Solidity contracts",
    version="1.0.0"
)


class AuditResponse(BaseModel):
    """Response model for audit endpoint"""
    run_id: str
    status: str
    vulnerabilities_found: int
    report_path: str
    sarif_path: Optional[str] = None
    execution_time: float
    mode: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": MODE,
        "medusa_available": check_medusa(),
        "solc_available": check_solc(),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/audit", response_model=AuditResponse)
async def audit_contract(file: UploadFile = File(...)):
    """
    Audit a Solidity contract
    
    Args:
        file: Uploaded .sol file
    
    Returns:
        AuditResponse with findings and artifact paths
    """
    start_time = datetime.utcnow()
    run_id = start_time.strftime("%Y%m%d_%H%M%S")
    
    # Validate file
    if not file.filename.endswith('.sol'):
        raise HTTPException(status_code=400, detail="Only .sol files are supported")
    
    # Create temporary contract file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as tmp:
        content = await file.read()
        tmp.write(content.decode('utf-8'))
        tmp_path = tmp.name
    
    try:
        # Run audit
        result = run_audit(tmp_path, run_id)
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Read results
        report_path = ARTIFACTS_DIR / run_id / "report.json"
        sarif_path = ARTIFACTS_DIR / run_id / "report.sarif.json"
        
        vulnerabilities_count = 0
        if report_path.exists():
            with open(report_path) as f:
                data = json.load(f)
                vulnerabilities_count = len(data.get('vulnerabilities', []))
        
        return AuditResponse(
            run_id=run_id,
            status="completed",
            vulnerabilities_found=vulnerabilities_count,
            report_path=str(report_path),
            sarif_path=str(sarif_path) if sarif_path.exists() else None,
            execution_time=execution_time,
            mode=MODE
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")
    
    finally:
        # Cleanup temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def run_audit(contract_path: str, run_id: str) -> dict:
    """
    Run the audit pipeline
    
    Args:
        contract_path: Path to contract file
        run_id: Unique run identifier
    
    Returns:
        dict with audit results
    """
    # Create run-specific artifact directory
    run_artifacts = ARTIFACTS_DIR / run_id
    run_artifacts.mkdir(parents=True, exist_ok=True)
    
    # Set environment variables
    env = os.environ.copy()
    env['RUN_ID'] = run_id
    env['ARTIFACTS_DIR'] = str(run_artifacts)
    
    # Run auditor
    cmd = [
        'python3', 'auditor_ai.py',
        str(MEDUSA_TIMEOUT)
    ]
    
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=MEDUSA_TIMEOUT + 30  # Extra buffer
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Audit failed: {result.stderr}")
    
    return {"stdout": result.stdout, "stderr": result.stderr}


def check_medusa() -> bool:
    """Check if Medusa is available"""
    try:
        subprocess.run(['medusa', '--version'], capture_output=True, check=True)
        return True
    except:
        return False


def check_solc() -> bool:
    """Check if solc is available"""
    try:
        subprocess.run(['solc', '--version'], capture_output=True, check=True)
        return True
    except:
        return False


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
