"""
Tests for Demo Mode Security
Ensures demo server only runs when enabled and requires authentication
"""

import os
import subprocess
import pytest
from pathlib import Path


def test_demo_mode_disabled_by_default():
    """Ensure demo server doesn't start when DEMO_MODE=false"""
    env = os.environ.copy()
    env['DEMO_MODE'] = 'false'
    
    # Run demo_server.py - should exit immediately
    result = subprocess.run(
        ['python3', 'demo_server.py'],
        env=env,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    # Should exit with code 0 and print disabled message
    assert result.returncode == 0
    assert 'DEMO_MODE=false' in result.stdout or 'Demo server disabled' in result.stdout


def test_ngrok_script_fails_without_token():
    """Ensure script aborts if NGROK_AUTHTOKEN missing"""
    env = os.environ.copy()
    env['NGROK_AUTHTOKEN'] = ''
    env['DEMO_USER'] = 'test'
    env['DEMO_PASS'] = 'test'
    
    result = subprocess.run(
        ['bash', 'scripts/start_ngrok_demo.sh'],
        env=env,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    # Should fail with non-zero exit code
    assert result.returncode != 0
    # Should mention missing token
    output = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
    output += result.stdout.decode() if isinstance(result.stdout, bytes) else result.stdout
    assert 'NGROK_AUTHTOKEN' in output


def test_ngrok_script_fails_without_credentials():
    """Ensure script aborts if DEMO_USER or DEMO_PASS missing"""
    env = os.environ.copy()
    env['NGROK_AUTHTOKEN'] = 'test_token'
    env['DEMO_USER'] = ''
    env['DEMO_PASS'] = ''
    
    result = subprocess.run(
        ['bash', 'scripts/start_ngrok_demo.sh'],
        env=env,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    # Should fail with non-zero exit code
    assert result.returncode != 0
    # Should mention missing credentials
    output = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
    output += result.stdout.decode() if isinstance(result.stdout, bytes) else result.stdout
    assert 'DEMO_USER' in output or 'DEMO_PASS' in output


def test_env_example_has_demo_variables():
    """Ensure .env.example contains all required demo variables"""
    env_example = Path('.env.example')
    assert env_example.exists(), ".env.example file must exist"
    
    content = env_example.read_text()
    
    # Check for required variables
    required_vars = [
        'DEMO_MODE',
        'DEMO_USER',
        'DEMO_PASS',
        'DEMO_CIDR_ALLOW',
        'DEMO_TTL_SECONDS',
        'NGROK_AUTHTOKEN'
    ]
    
    for var in required_vars:
        assert var in content, f"{var} must be in .env.example"
    
    # Ensure DEMO_MODE defaults to false
    assert 'DEMO_MODE=false' in content, "DEMO_MODE must default to false"
    
    # Ensure TTL is 3 hours (10800 seconds)
    assert 'DEMO_TTL_SECONDS=10800' in content, "DEMO_TTL_SECONDS must default to 10800 (3 hours)"


def test_demo_server_file_exists():
    """Ensure demo_server.py exists and has security features"""
    demo_server = Path('demo_server.py')
    assert demo_server.exists(), "demo_server.py must exist"
    
    # Check for security features in code
    content = demo_server.read_text()
    assert 'HTTPBasic' in content, "Must use HTTP Basic Auth"
    assert 'verify_credentials' in content, "Must have credential verification"
    assert 'auto_shutdown' in content, "Must have TTL auto-shutdown"
    assert 'check_cidr_allowlist' in content, "Must have CIDR check function"


def test_ngrok_script_exists_and_executable():
    """Ensure ngrok launch script exists and is executable"""
    script = Path('scripts/start_ngrok_demo.sh')
    assert script.exists(), "start_ngrok_demo.sh must exist"
    
    # Check if executable
    assert os.access(script, os.X_OK), "Script must be executable"
    
    # Check for security validations in script
    content = script.read_text()
    assert 'NGROK_AUTHTOKEN' in content, "Must validate NGROK_AUTHTOKEN"
    assert 'DEMO_USER' in content, "Must validate DEMO_USER"
    assert 'DEMO_PASS' in content, "Must validate DEMO_PASS"


def test_docker_compose_demo_exists():
    """Ensure docker-compose.demo.yml exists with correct config"""
    compose_demo = Path('docker-compose.demo.yml')
    assert compose_demo.exists(), "docker-compose.demo.yml must exist"
    
    content = compose_demo.read_text()
    assert 'DEMO_MODE=true' in content, "Must set DEMO_MODE=true"
    assert 'demo_server.py' in content, "Must run demo_server.py"
    assert 'restart: "no"' in content or 'restart: no' in content, "Must not auto-restart"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
