#!/usr/bin/env python3
"""
Unit tests for check_retro_auth.py
"""

import json
import os
import subprocess
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "check_retro_auth.py")

# Import the function directly for unit tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from check_retro_auth import check_retro_auth


def write_feature_list(tmp_path, data):
    """Write a feature-list.json and return its path."""
    fl_path = tmp_path / "feature-list.json"
    fl_path.write_text(json.dumps(data), encoding="utf-8")
    return str(fl_path)


def base_data(**extra):
    """Return a minimal feature-list.json dict with optional extra root fields."""
    d = {
        "project": "test",
        "tech_stack": {"language": "python", "test_framework": "pytest",
                       "coverage_tool": "pytest-cov"},
        "quality_gates": {"line_coverage_min": 90, "branch_coverage_min": 80},
        "features": [],
    }
    d.update(extra)
    return d


def run_checker(fl_path, env=None):
    """Run check_retro_auth.py and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, SCRIPT_PATH, fl_path],
        capture_output=True, text=True, env=env
    )
    return result.returncode, result.stdout, result.stderr


# --- Unit tests using check_retro_auth() directly ---

def test_no_endpoint_configured(tmp_path, monkeypatch):
    """No endpoint in JSON and no env var → status=disabled."""
    monkeypatch.delenv("RETRO_API_ENDPOINT", raising=False)
    fl_path = write_feature_list(tmp_path, base_data())
    result = check_retro_auth(fl_path)
    assert result["status"] == "disabled"
    assert result["endpoint"] is None
    assert result["error"] is None


def test_endpoint_in_feature_list_reachable(tmp_path, monkeypatch):
    """Endpoint in feature-list.json and reachable → status=ready."""
    monkeypatch.delenv("RETRO_API_ENDPOINT", raising=False)
    endpoint = "http://localhost:9999/retro"
    fl_path = write_feature_list(tmp_path, base_data(retro_api_endpoint=endpoint))

    mock_response = MagicMock()
    mock_response.status = 200
    with patch("check_retro_auth.urllib.request.urlopen", return_value=mock_response):
        result = check_retro_auth(fl_path)

    assert result["status"] == "ready"
    assert result["endpoint"] == endpoint
    assert result["error"] is None


def test_endpoint_in_feature_list_unreachable(tmp_path, monkeypatch):
    """Endpoint in feature-list.json but unreachable → status=unavailable."""
    monkeypatch.delenv("RETRO_API_ENDPOINT", raising=False)
    endpoint = "http://localhost:9999/retro"
    fl_path = write_feature_list(tmp_path, base_data(retro_api_endpoint=endpoint))

    with patch("check_retro_auth.urllib.request.urlopen",
               side_effect=ConnectionError("Connection refused")):
        result = check_retro_auth(fl_path)

    assert result["status"] == "unavailable"
    assert result["endpoint"] == endpoint
    assert result["error"] is not None
    assert "Connection refused" in result["error"]


def test_endpoint_from_env_var(tmp_path, monkeypatch):
    """No endpoint in JSON but RETRO_API_ENDPOINT env var set → picks up env var."""
    endpoint = "http://retro.example.com/api"
    monkeypatch.setenv("RETRO_API_ENDPOINT", endpoint)
    fl_path = write_feature_list(tmp_path, base_data())

    mock_response = MagicMock()
    mock_response.status = 200
    with patch("check_retro_auth.urllib.request.urlopen", return_value=mock_response):
        result = check_retro_auth(fl_path)

    assert result["status"] == "ready"
    assert result["endpoint"] == endpoint


def test_json_field_takes_priority_over_env_var(tmp_path, monkeypatch):
    """feature-list.json field takes priority over env var."""
    json_endpoint = "http://json-endpoint.example.com/retro"
    env_endpoint = "http://env-endpoint.example.com/retro"
    monkeypatch.setenv("RETRO_API_ENDPOINT", env_endpoint)
    fl_path = write_feature_list(tmp_path, base_data(retro_api_endpoint=json_endpoint))

    mock_response = MagicMock()
    mock_response.status = 200
    with patch("check_retro_auth.urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        result = check_retro_auth(fl_path)

    assert result["endpoint"] == json_endpoint
    # Verify the request was made to the JSON endpoint, not the env var one
    call_args = mock_urlopen.call_args
    req = call_args[0][0]
    assert req.full_url == json_endpoint


def test_invalid_json(tmp_path, monkeypatch):
    """Invalid JSON → raises exception."""
    monkeypatch.delenv("RETRO_API_ENDPOINT", raising=False)
    fl_path = tmp_path / "feature-list.json"
    fl_path.write_text("not valid json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        check_retro_auth(str(fl_path))


def test_file_not_found(monkeypatch):
    """File not found → raises exception."""
    monkeypatch.delenv("RETRO_API_ENDPOINT", raising=False)
    with pytest.raises(FileNotFoundError):
        check_retro_auth("/nonexistent/feature-list.json")


def test_head_timeout(tmp_path, monkeypatch):
    """HTTP HEAD timeout → status=unavailable."""
    monkeypatch.delenv("RETRO_API_ENDPOINT", raising=False)
    endpoint = "http://localhost:9999/retro"
    fl_path = write_feature_list(tmp_path, base_data(retro_api_endpoint=endpoint))

    import urllib.error
    with patch("check_retro_auth.urllib.request.urlopen",
               side_effect=TimeoutError("timed out")):
        result = check_retro_auth(fl_path)

    assert result["status"] == "unavailable"
    assert "timed out" in result["error"]


def test_head_http_error(tmp_path, monkeypatch):
    """HTTP HEAD returns 4xx/5xx → status=unavailable."""
    monkeypatch.delenv("RETRO_API_ENDPOINT", raising=False)
    endpoint = "http://localhost:9999/retro"
    fl_path = write_feature_list(tmp_path, base_data(retro_api_endpoint=endpoint))

    import urllib.error
    with patch("check_retro_auth.urllib.request.urlopen",
               side_effect=urllib.error.HTTPError(endpoint, 403, "Forbidden", {}, None)):
        result = check_retro_auth(fl_path)

    assert result["status"] == "unavailable"
    assert result["error"] is not None


# --- CLI integration tests ---

def test_cli_disabled(tmp_path, monkeypatch):
    """CLI: no endpoint → exit 2, prints 'disabled'."""
    monkeypatch.delenv("RETRO_API_ENDPOINT", raising=False)
    fl_path = write_feature_list(tmp_path, base_data())
    env = os.environ.copy()
    env.pop("RETRO_API_ENDPOINT", None)
    code, stdout, _ = run_checker(str(fl_path), env=env)
    assert code == 2
    assert "disabled" in stdout


def test_cli_invalid_json(tmp_path):
    """CLI: invalid JSON → exit 1, prints ERROR."""
    fl_path = tmp_path / "feature-list.json"
    fl_path.write_text("not json", encoding="utf-8")
    code, stdout, _ = run_checker(str(fl_path))
    assert code == 1
    assert "ERROR" in stdout


def test_cli_file_not_found():
    """CLI: non-existent file → exit 1, prints ERROR."""
    code, stdout, _ = run_checker("/nonexistent/feature-list.json")
    assert code == 1
    assert "ERROR" in stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
