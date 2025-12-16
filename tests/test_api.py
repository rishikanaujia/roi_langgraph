"""
Tests for Phase 1 Rankings REST API

Tests all endpoints with various scenarios.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    print("\n" + "=" * 70)
    print("TEST: Health Check")
    print("=" * 70)

    response = client.get("/api/v1/health")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data

    print("✅ Health check: PASSED")


def test_create_ranking_job():
    """Test creating a ranking job."""
    print("\n" + "=" * 70)
    print("TEST: Create Ranking Job")
    print("=" * 70)

    request = {
        "countries": ["USA", "India", "China"],
        "num_peer_rankers": 3
    }

    response = client.post("/api/v1/rankings", json=request)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert "estimated_duration_seconds" in data

    print(f"✅ Job created: {data['job_id']}")
    print(f"   Estimated duration: {data['estimated_duration_seconds']}s")
    print("✅ Create ranking job: PASSED")

    return data["job_id"]


def test_get_job_status(job_id: str):
    """Test getting job status."""
    print("\n" + "=" * 70)
    print("TEST: Get Job Status")
    print("=" * 70)

    response = client.get(f"/api/v1/rankings/{job_id}/status")

    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Job Status: {data['status']}")
    print(f"Progress: {data['progress']}")

    assert response.status_code == 200
    assert data["job_id"] == job_id
    assert "status" in data
    assert "progress" in data

    print("✅ Get job status: PASSED")

    return data["status"]


def test_invalid_request():
    """Test invalid request handling."""
    print("\n" + "=" * 70)
    print("TEST: Invalid Request Handling")
    print("=" * 70)

    # Test with only 1 country (minimum is 2)
    request = {
        "countries": ["USA"],
        "num_peer_rankers": 3
    }

    response = client.post("/api/v1/rankings", json=request)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 422  # Validation error

    print("✅ Invalid request handling: PASSED")


def test_nonexistent_job():
    """Test accessing nonexistent job."""
    print("\n" + "=" * 70)
    print("TEST: Nonexistent Job Handling")
    print("=" * 70)

    fake_job_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/rankings/{fake_job_id}/status")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    assert response.status_code == 404

    print("✅ Nonexistent job handling: PASSED")


def test_full_workflow():
    """Test full workflow: create, wait, get results, download report."""
    print("\n" + "=" * 70)
    print("TEST: Full Workflow")
    print("=" * 70)
    print("⚠️  This test will take ~20-30 seconds")
    print("⚠️  Will make real API calls to OpenAI")

    # Step 1: Create job
    request = {
        "countries": ["USA", "IND", "CHN"],  # Changed from "India", "China"
        "num_peer_rankers": 3
    }

    response = client.post("/api/v1/rankings", json=request)
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    print(f"\n✅ Step 1: Job created ({job_id})")

    # Step 2: Poll status until complete
    print("\n⏳ Step 2: Waiting for completion...")
    max_wait = 60  # 60 seconds timeout
    start_time = time.time()

    while time.time() - start_time < max_wait:
        response = client.get(f"/api/v1/rankings/{job_id}/status")
        assert response.status_code == 200

        data = response.json()
        status = data["status"]

        print(f"   Status: {status}, Progress: {data['progress']}")

        if status == "completed":
            print(f"\n✅ Step 2: Job completed in {data['duration_seconds']}s")
            break
        elif status == "failed":
            print(f"\n❌ Job failed: {data.get('error')}")
            assert False, "Job failed"

        time.sleep(2)  # Poll every 2 seconds
    else:
        assert False, "Job did not complete within timeout"

    # Step 3: Get results
    response = client.get(f"/api/v1/rankings/{job_id}")
    assert response.status_code == 200

    data = response.json()
    print(f"\n✅ Step 3: Results retrieved")
    print(f"   Countries analyzed: {data['countries_analyzed']}")
    print(f"   Top ranked: {data['rankings'][0]['country_code']} ({data['rankings'][0]['consensus_score']}/10)")

    # Step 4: Preview report
    response = client.get(f"/api/v1/rankings/{job_id}/report/preview")
    assert response.status_code == 200

    preview = response.text
    print(f"\n✅ Step 4: Report preview retrieved ({len(preview)} chars)")
    print(f"   Preview: {preview[:200]}...")

    # Step 5: Download report (FIXED)
    response = client.get(f"/api/v1/rankings/{job_id}/report")
    assert response.status_code == 200

    # Check content type (be flexible with case)
    content_type = response.headers.get("content-type") or response.headers.get("Content-Type")
    assert content_type == "text/markdown", f"Expected text/markdown, got {content_type}"

    report_content = response.text
    print(f"\n✅ Step 5: Report downloaded ({len(report_content)} chars)")

    # Verify report has key sections
    assert "# Renewable Energy Investment Analysis" in report_content
    assert "## Executive Summary" in report_content
    assert "## Final Rankings" in report_content
    assert "USA" in report_content

    print("\n✅ Full workflow: PASSED")


def run_all_tests():
    """Run all API tests."""
    print("\n" + "=" * 70)
    print("RUNNING ALL API TESTS")
    print("=" * 70)

    passed = 0
    failed = 0

    tests = [
        test_health_check,
        test_invalid_request,
        test_nonexistent_job,
        test_create_ranking_job,
        test_full_workflow  # This one takes ~20-30s
    ]

    for test_func in tests:
        try:
            if test_func == test_create_ranking_job:
                # Create job and store job_id for status test
                job_id = test_func()
                # Test status immediately after
                test_get_job_status(job_id)
            else:
                test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ {test_func.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ {test_func.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 ALL API TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)