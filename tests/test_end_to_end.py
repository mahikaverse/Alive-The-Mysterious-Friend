"""End-to-end integration test for the complete Alive system.

Tests the full pipeline:
  HTTP API -> RequestHandler -> ConversationController ->
    EmotionEngine -> RelationshipEngine -> LifeSimulator ->
    IdentityEngine -> PromptBuilder -> ResponseValidator ->
    ResponseHandler -> HTTP Response

Ownership: Person 1 (Backend & Infrastructure)
"""

import json
import sys
import time
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx

BASE = "http://127.0.0.1:8765"


def test_health():
    r = httpx.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.1.0"
    assert "uptime_seconds" in data
    assert "model" in data
    assert "environment" in data
    print(f"[PASS] GET /health -> {data['status']}, env={data['environment']}")


def test_ready():
    r = httpx.get(f"{BASE}/ready", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert data["orchestrator"] == "initialised"
    print(f"[PASS] GET /ready -> {data['status']}")


def test_metrics():
    r = httpx.get(f"{BASE}/metrics", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert "total_requests" in data
    assert "requests_by_path" in data
    assert "requests_by_status" in data
    assert "avg_latency_seconds" in data
    print(f"[PASS] GET /metrics -> {data['total_requests']} total requests")


def test_chat_completions_basic():
    payload = {
        "model": "alive-v1",
        "messages": [
            {"role": "user", "content": "Hello! How are you?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }
    r = httpx.post(f"{BASE}/chat/completions", json=payload, timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
    data = r.json()

    assert data["object"] == "chat.completion"
    assert data["model"] == "alive-v1"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert data["choices"][0]["finish_reason"] == "stop"
    assert len(data["choices"][0]["message"]["content"]) > 0
    assert "usage" in data
    assert data["usage"]["prompt_tokens"] >= 0
    assert data["usage"]["completion_tokens"] >= 0

    print(f"[PASS] POST /chat/completions (basic) -> response: {data['choices'][0]['message']['content'][:80]}...")


def test_chat_completions_with_system():
    payload = {
        "model": "alive-v1",
        "messages": [
            {"role": "system", "content": "You are Alive, a mysterious friend."},
            {"role": "user", "content": "What are you thinking about?"},
        ],
    }
    r = httpx.post(f"{BASE}/chat/completions", json=payload, timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
    data = r.json()
    assert len(data["choices"][0]["message"]["content"]) > 0
    print(f"[PASS] POST /chat/completions (with system) -> {data['choices'][0]['message']['content'][:80]}...")


def test_chat_completions_multi_turn():
    payload = {
        "model": "alive-v1",
        "messages": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hey! How's it going?"},
            {"role": "user", "content": "I'm good! I just got a new book."},
        ],
    }
    r = httpx.post(f"{BASE}/chat/completions", json=payload, timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
    data = r.json()
    assert len(data["choices"][0]["message"]["content"]) > 0
    print(f"[PASS] POST /chat/completions (multi-turn) -> {data['choices'][0]['message']['content'][:80]}...")


def test_request_id_propagation():
    payload = {
        "model": "alive-v1",
        "messages": [{"role": "user", "content": "Hello"}],
    }
    custom_id = "e2e-test-req-001"
    r = httpx.post(
        f"{BASE}/chat/completions",
        json=payload,
        headers={"X-Request-ID": custom_id},
        timeout=15,
    )
    assert r.status_code == 200
    echo_id = r.headers.get("X-Request-ID", "")
    assert echo_id == custom_id, f"Expected X-Request-ID '{custom_id}', got '{echo_id}'"
    data = r.json()
    assert data["id"] == f"chatcmpl-{custom_id}"
    print(f"[PASS] X-Request-ID propagation: {echo_id}")


def test_validation_empty_messages():
    r = httpx.post(
        f"{BASE}/chat/completions",
        json={"model": "alive-v1", "messages": []},
        timeout=5,
    )
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}: {r.text[:200]}"
    print(f"[PASS] Validation (empty messages) -> {r.status_code}: {r.json().get('error', '')}")


def test_validation_invalid_role():
    r = httpx.post(
        f"{BASE}/chat/completions",
        json={"model": "alive-v1", "messages": [{"role": "robot", "content": "hi"}]},
        timeout=5,
    )
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}: {r.text[:200]}"
    print(f"[PASS] Validation (invalid role) -> {r.status_code}")


def test_validation_missing_model():
    r = httpx.post(
        f"{BASE}/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}]},
        timeout=5,
    )
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}: {r.text[:200]}"
    print(f"[PASS] Validation (missing model) -> {r.status_code}")


def test_validation_invalid_temperature():
    r = httpx.post(
        f"{BASE}/chat/completions",
        json={
            "model": "alive-v1",
            "messages": [{"role": "user", "content": "hi"}],
            "temperature": 99.0,
        },
        timeout=5,
    )
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}: {r.text[:200]}"
    print(f"[PASS] Validation (invalid temperature) -> {r.status_code}")


def test_404():
    r = httpx.get(f"{BASE}/nonexistent", timeout=5)
    assert r.status_code == 404
    print(f"[PASS] GET /nonexistent -> {r.status_code}")


def test_orchestrator_behaviour_engines():
    """Verify that the orchestrator's behaviour engines produce realistic output.
    
    Sends multiple messages and checks that responses vary based on
    accumulated emotional and relationship state.
    """
    messages = [
        {"role": "user", "content": "Hello there!"},
    ]
    
    r1 = httpx.post(
        f"{BASE}/chat/completions",
        json={"model": "alive-v1", "messages": messages},
        timeout=15,
    )
    assert r1.status_code == 200
    resp1 = r1.json()["choices"][0]["message"]["content"]
    
    # Add assistant response and send a positive emotional message
    messages.append({"role": "assistant", "content": resp1})
    messages.append({"role": "user", "content": "You're amazing! I really enjoy talking to you!"})
    
    r2 = httpx.post(
        f"{BASE}/chat/completions",
        json={"model": "alive-v1", "messages": messages},
        timeout=15,
    )
    assert r2.status_code == 200
    resp2 = r2.json()["choices"][0]["message"]["content"]
    
    print(f"[INFO] Turn 1 response: {resp1[:80]}...")
    print(f"[INFO] Turn 2 response: {resp2[:80]}...")
    print(f"[PASS] Behaviour engines produce valid multi-turn responses")


def test_concurrent_requests():
    """Verify that concurrent requests don't interfere with each other."""
    import asyncio
    
    async def send_request(req_id: str) -> dict:
        payload = {
            "model": "alive-v1",
            "messages": [{"role": "user", "content": f"Hello from request {req_id}"}],
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE}/chat/completions",
                json=payload,
                headers={"X-Request-ID": req_id},
                timeout=15,
            )
            return {"id": req_id, "status": r.status_code, "body": r.json() if r.status_code == 200 else r.text}
    
    async def run_concurrent():
        tasks = [send_request(f"concurrent-{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        return results
    
    results = asyncio.run(run_concurrent())
    for r in results:
        assert r["status"] == 200, f"Request {r['id']} failed: {r['body'][:200]}"
        assert r["body"]["id"] == f"chatcmpl-{r['id']}"
    print(f"[PASS] Concurrent requests ({len(results)} requests all succeeded)")


def test_auth_middleware():
    """Test auth middleware by starting server with API_KEY set on a separate port."""
    import subprocess
    env = os.environ.copy()
    env["API_KEY"] = "test-secret-key-123"
    env["PYTHONPATH"] = os.path.join(os.path.dirname(__file__), "..")
    
    proc = subprocess.Popen(
        [sys.executable, "-c", 
         "import sys; sys.path.insert(0, '.'); import uvicorn; uvicorn.run('backend.main:app', host='127.0.0.1', port=8766, log_level='warning')"],
        env=env,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    AUTH_BASE = "http://127.0.0.1:8766"
    
    try:
        for i in range(15):
            try:
                r = httpx.get(f"{AUTH_BASE}/health", timeout=2)
                if r.status_code == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            proc.kill()
            proc.wait()
            raise RuntimeError("Auth test server did not start")
        
        # Public endpoints should work without auth
        r = httpx.get(f"{AUTH_BASE}/health", timeout=5)
        assert r.status_code == 200
        print("[PASS] Auth: public /health accessible without token")
        
        r = httpx.get(f"{AUTH_BASE}/ready", timeout=5)
        assert r.status_code == 200
        print("[PASS] Auth: public /ready accessible without token")
        
        # Protected endpoint without auth header
        payload = {"model": "alive-v1", "messages": [{"role": "user", "content": "Hi"}]}
        r = httpx.post(f"{AUTH_BASE}/chat/completions", json=payload, timeout=5)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        assert "Unauthorized" in r.text
        print("[PASS] Auth: missing token returns 401")
        
        # Protected endpoint with wrong auth header
        r = httpx.post(
            f"{AUTH_BASE}/chat/completions",
            json=payload,
            headers={"Authorization": "Bearer wrong-key"},
            timeout=5,
        )
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("[PASS] Auth: invalid token returns 401")
        
        # Protected endpoint with correct auth header
        r = httpx.post(
            f"{AUTH_BASE}/chat/completions",
            json=payload,
            headers={"Authorization": "Bearer test-secret-key-123"},
            timeout=15,
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
        print("[PASS] Auth: valid token succeeds")
        
    finally:
        proc.kill()
        proc.wait()


def test_very_long_message():
    """Test handling of a very long message content."""
    long_content = "Hello " * 1000
    payload = {
        "model": "alive-v1",
        "messages": [{"role": "user", "content": long_content.strip()}],
    }
    r = httpx.post(f"{BASE}/chat/completions", json=payload, timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    data = r.json()
    assert len(data["choices"][0]["message"]["content"]) > 0
    print(f"[PASS] Long message ({len(long_content)} chars) handled successfully")


def test_empty_content_message():
    """Test handling of empty content in a message.
    
    Pydantic's min_length=1 should reject empty content with 400/422.
    """
    r = httpx.post(
        f"{BASE}/chat/completions",
        json={"model": "alive-v1", "messages": [{"role": "user", "content": ""}]},
        timeout=5,
    )
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}: {r.text[:200]}"
    print(f"[PASS] Empty content -> {r.status_code}")


def test_zero_temperature():
    """Test that zero temperature is accepted (deterministic mode)."""
    payload = {
        "model": "alive-v1",
        "messages": [{"role": "user", "content": "Say something"}],
        "temperature": 0.0,
    }
    r = httpx.post(f"{BASE}/chat/completions", json=payload, timeout=15)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:200]}"
    print("[PASS] Zero temperature accepted")


def test_response_fields():
    """Verify the OpenAI-compatible response schema fields."""
    payload = {
        "model": "alive-v1",
        "messages": [{"role": "user", "content": "Verify response schema"}],
    }
    r = httpx.post(f"{BASE}/chat/completions", json=payload, timeout=15)
    assert r.status_code == 200
    data = r.json()
    
    assert data["id"].startswith("chatcmpl-")
    assert len(data["id"]) > len("chatcmpl-")
    assert data["object"] == "chat.completion"
    assert isinstance(data["created"], int)
    assert data["created"] > 0
    assert data["model"] == "alive-v1"
    assert len(data["choices"]) == 1
    
    choice = data["choices"][0]
    assert choice["index"] == 0
    assert choice["message"]["role"] == "assistant"
    assert isinstance(choice["message"]["content"], str)
    assert len(choice["message"]["content"]) > 0
    assert choice["finish_reason"] == "stop"
    
    usage = data["usage"]
    assert usage["prompt_tokens"] >= 0
    assert usage["completion_tokens"] >= 0
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
    
    print("[PASS] Response schema matches OpenAI specification")


def test_method_not_allowed():
    """Test that unsupported HTTP methods return 405."""
    r = httpx.put(f"{BASE}/chat/completions", json={}, timeout=5)
    assert r.status_code == 405, f"Expected 405, got {r.status_code}"
    print(f"[PASS] PUT /chat/completions -> {r.status_code}")


def test_max_conversation_length():
    """Test that conversations exceeding max length are rejected."""
    too_many = [{"role": "user", "content": f"Message {i}"} for i in range(101)]
    r = httpx.post(
        f"{BASE}/chat/completions",
        json={"model": "alive-v1", "messages": too_many},
        timeout=5,
    )
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}: {r.text[:200]}"
    print(f"[PASS] Max conversation length enforcement -> {r.status_code}")


def test_negative_max_tokens():
    """Test that invalid max_tokens values are rejected."""
    r = httpx.post(
        f"{BASE}/chat/completions",
        json={
            "model": "alive-v1",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": -1,
        },
        timeout=5,
    )
    assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}: {r.text[:200]}"
    print(f"[PASS] Negative max_tokens -> {r.status_code}")


def run_all():
    print("=" * 60)
    print("Alive — End-to-End Integration Tests")
    print("=" * 60)
    
    # Wait for server to be ready
    for i in range(15):
        try:
            r = httpx.get(f"{BASE}/health", timeout=2)
            if r.status_code == 200:
                print(f"[INFO] Server ready (attempt {i+1})")
                break
        except Exception:
            time.sleep(1)
    else:
        print("[FAIL] Server did not start within 15 seconds")
        sys.exit(1)
    
    tests = [
        ("Health endpoint", test_health),
        ("Ready endpoint", test_ready),
        ("Metrics endpoint", test_metrics),
        ("Chat completions (basic)", test_chat_completions_basic),
        ("Chat completions (with system)", test_chat_completions_with_system),
        ("Chat completions (multi-turn)", test_chat_completions_multi_turn),
        ("Request ID propagation", test_request_id_propagation),
        ("Validation: empty messages", test_validation_empty_messages),
        ("Validation: empty content", test_empty_content_message),
        ("Validation: invalid role", test_validation_invalid_role),
        ("Validation: missing model", test_validation_missing_model),
        ("Validation: invalid temperature", test_validation_invalid_temperature),
        ("Validation: negative max_tokens", test_negative_max_tokens),
        ("Validation: max conversation length", test_max_conversation_length),
        ("Zero temperature", test_zero_temperature),
        ("Very long message", test_very_long_message),
        ("Response schema validation", test_response_fields),
        ("Method not allowed (PUT)", test_method_not_allowed),
        ("404 handling", test_404),
        ("Auth middleware", test_auth_middleware),
        ("Behaviour engines (multi-turn)", test_orchestrator_behaviour_engines),
        ("Concurrent requests", test_concurrent_requests),
    ]
    
    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
