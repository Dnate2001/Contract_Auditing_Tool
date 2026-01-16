#!/usr/bin/env python3
"""
Secure Demo Server for Contract Auditing Tool
OPTIONAL - Only runs when DEMO_MODE=true

Security Features:
- HTTP Basic Auth on all endpoints
- Optional CIDR IP allow-list
- TTL-based auto-shutdown
- Isolated artifacts directory
- Warning banners
"""

import os
import sys
import json
import tempfile
import subprocess
import threading
import time
import ipaddress
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
import uvicorn
import secrets

# Configuration from environment
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
DEMO_USER = os.getenv("DEMO_USER", "demo_user")
DEMO_PASS = os.getenv("DEMO_PASS", "change_me_strong_password")
DEMO_CIDR_ALLOW = os.getenv("DEMO_CIDR_ALLOW", "")
DEMO_TTL_SECONDS = int(os.getenv("DEMO_TTL_SECONDS", "10800"))
PORT = int(os.getenv("PORT", "8080"))

# Exit immediately if demo mode not enabled
if not DEMO_MODE:
    print("ℹ️  DEMO_MODE=false - Demo server disabled")
    print("   To enable: Set DEMO_MODE=true in .env")
    sys.exit(0)

# Validate credentials are not defaults
if DEMO_PASS == "change_me_strong_password":
    print("⚠️  WARNING: Using default DEMO_PASS")
    print("   Please set a strong password in .env before sharing the demo")

# Create isolated artifacts directory
DEMO_ARTIFACTS_DIR = Path(f"/tmp/artifacts_demo/{datetime.now().strftime('%Y%m%d_%H%M%S')}")
DEMO_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Security
security = HTTPBasic()

# FastAPI app
app = FastAPI(
    title="Contract Auditor Demo API",
    description="Temporary demo server with HTTP Basic Auth",
    version="1.0.0-demo"
)


def print_warning_banner():
    """Print security warning banner"""
    print("\n" + "="*70)
    print("⚠️  DEMO MODE ENABLED - TUNNEL IS PUBLIC")
    print("="*70)
    print("Security Controls Active:")
    print(f"  ✅ HTTP Basic Auth: {DEMO_USER}:{'*' * len(DEMO_PASS)}")
    print(f"  ✅ CIDR Allow-list: {DEMO_CIDR_ALLOW if DEMO_CIDR_ALLOW else 'DISABLED (all IPs allowed)'}")
    print(f"  ✅ Auto-shutdown: {DEMO_TTL_SECONDS}s ({DEMO_TTL_SECONDS//60} minutes)")
    print(f"  ✅ Isolated artifacts: {DEMO_ARTIFACTS_DIR}")
    print("\n⚠️  DO NOT USE REAL API KEYS IN DEMO MODE")
    print("⚠️  DEMO IS FOR TEMPORARY REVIEW ONLY")
    print("="*70 + "\n")


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify HTTP Basic Auth credentials"""
    correct_username = secrets.compare_digest(credentials.username, DEMO_USER)
    correct_password = secrets.compare_digest(credentials.password, DEMO_PASS)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def check_cidr_allowlist(request: Request):
    """Check if client IP is in CIDR allow-list"""
    if not DEMO_CIDR_ALLOW:
        return  # No restrictions if not configured
    
    client_ip = request.client.host
    allowed_cidrs = [cidr.strip() for cidr in DEMO_CIDR_ALLOW.split(",")]
    
    try:
        client_addr = ipaddress.ip_address(client_ip)
        for cidr in allowed_cidrs:
            if client_addr in ipaddress.ip_network(cidr, strict=False):
                return  # IP is allowed
        
        # IP not in any allowed CIDR
        raise HTTPException(
            status_code=403,
            detail=f"IP {client_ip} not in allowed CIDR ranges"
        )
    except ValueError as e:
        print(f"⚠️  CIDR check error: {e}")
        raise HTTPException(status_code=403, detail="Invalid IP configuration")


def auto_shutdown():
    """Auto-shutdown server after TTL expires"""
    print(f"⏰ Auto-shutdown timer started: {DEMO_TTL_SECONDS}s")
    time.sleep(DEMO_TTL_SECONDS)
    print("\n" + "="*70)
    print("⏰ TTL EXPIRED - SHUTTING DOWN DEMO SERVER")
    print("="*70)
    os._exit(0)


class AuditResponse(BaseModel):
    """Response model for audit endpoint"""
    run_id: str
    status: str
    message: str
    artifacts_path: str
    execution_time: float


@app.on_event("startup")
async def startup_event():
    """Print warning banner and start auto-shutdown timer"""
    print_warning_banner()
    
    # Start auto-shutdown timer in background
    shutdown_thread = threading.Thread(target=auto_shutdown, daemon=True)
    shutdown_thread.start()


@app.get("/health")
async def health_check(
    request: Request,
    username: str = Depends(verify_credentials)
):
    """Health check endpoint with security info"""
    check_cidr_allowlist(request)
    
    return {
        "status": "healthy",
        "mode": "DEMO",
        "authenticated_user": username,
        "client_ip": request.client.host,
        "ttl_remaining": "check server logs",
        "artifacts_dir": str(DEMO_ARTIFACTS_DIR),
        "security": {
            "basic_auth": "enabled",
            "cidr_allowlist": "enabled" if DEMO_CIDR_ALLOW else "disabled",
            "auto_shutdown": f"{DEMO_TTL_SECONDS}s"
        },
        "warning": "DEMO MODE - DO NOT USE REAL API KEYS"
    }


@app.post("/audit", response_model=AuditResponse)
async def audit_contract(
    request: Request,
    file: UploadFile = File(...),
    username: str = Depends(verify_credentials)
):
    """
    Audit a Solidity contract (DEMO MODE)
    
    Accepts .sol file and runs security audit
    """
    check_cidr_allowlist(request)
    
    start_time = time.time()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Validate file
    if not file.filename.endswith('.sol'):
        raise HTTPException(status_code=400, detail="Only .sol files supported")
    
    # Create run directory
    run_dir = DEMO_ARTIFACTS_DIR / run_id
    run_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    contract_path = run_dir / file.filename
    with open(contract_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    print(f"📝 Audit request from {username} ({request.client.host}): {file.filename}")
    
    try:
        # Run audit (simulation mode for demo)
        result = subprocess.run(
            ["python3", "auditor_ai.py", "10"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "ARTIFACTS_DIR": str(run_dir)}
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            return AuditResponse(
                run_id=run_id,
                status="completed",
                message="Audit completed successfully (DEMO MODE)",
                artifacts_path=str(run_dir),
                execution_time=execution_time
            )
        else:
            return AuditResponse(
                run_id=run_id,
                status="failed",
                message=f"Audit failed: {result.stderr[:200]}",
                artifacts_path=str(run_dir),
                execution_time=execution_time
            )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Audit timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit error: {str(e)}")


@app.post("/audit-cli")
async def audit_contract_cli(
    request: Request,
    file: UploadFile = File(...),
    username: str = Depends(verify_credentials)
):
    """
    Audit a Solidity contract and return CLI-formatted output
    
    Returns the full CLI experience with ASCII art, tables, and colors
    """
    check_cidr_allowlist(request)
    
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Validate file
    if not file.filename.endswith('.sol'):
        raise HTTPException(status_code=400, detail="Only .sol files supported")
    
    # Create run directory
    run_dir = DEMO_ARTIFACTS_DIR / run_id
    run_dir.mkdir(exist_ok=True)
    
    # Save uploaded file to contracts directory
    contracts_dir = Path("contracts")
    contracts_dir.mkdir(exist_ok=True)
    contract_path = contracts_dir / file.filename
    with open(contract_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    print(f"📝 CLI Audit request from {username} ({request.client.host}): {file.filename}")
    
    try:
        # Run audit and capture full CLI output
        result = subprocess.run(
            ["python3", "auditor_ai.py", "10"],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "ARTIFACTS_DIR": str(run_dir)}
        )
        
        # Return the full CLI output as plain text
        from fastapi.responses import PlainTextResponse
        
        output = result.stdout if result.stdout else result.stderr
        return PlainTextResponse(
            content=output,
            media_type="text/plain; charset=utf-8"
        )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Audit timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit error: {str(e)}")


@app.get("/shutdown")
async def manual_shutdown(
    request: Request,
    username: str = Depends(verify_credentials)
):
    """Manual shutdown endpoint (requires auth)"""
    check_cidr_allowlist(request)
    
    print(f"🛑 Manual shutdown requested by {username}")
    
    # Shutdown in background to allow response
    def delayed_shutdown():
        time.sleep(1)
        os._exit(0)
    
    threading.Thread(target=delayed_shutdown, daemon=True).start()
    
    return {"message": "Server shutting down..."}


if __name__ == "__main__":
    uvicorn.run(
        "demo_server:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
