SCAN = {
    "scan_id": "scan-001",
    "piece_id": "piece-001",
    "stage": "cutting",
    "employee_id": "employee-001",
    "ts": "2026-10-26T10:00:00Z",
}


def test_scan_idempotency(client, scanner_token):
    headers = {"Authorization": f"Bearer {scanner_token}"}
    first = client.post("/scans", json=SCAN, headers=headers)
    duplicate = client.post("/scans", json=SCAN, headers=headers)

    assert first.status_code == 201
    assert duplicate.status_code == 200
    assert duplicate.json() == first.json()


def test_out_of_order_stage_returns_conflict(client, scanner_token):
    response = client.post(
        "/scans",
        json={**SCAN, "stage": "finishing"},
        headers={"Authorization": f"Bearer {scanner_token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Out-of-order stage for piece 'piece-001': expected cutting, got finishing"
    )


def test_scanner_cannot_read_manager_report(client, scanner_token):
    response = client.get(
        "/reports/daily-throughput?date=2026-10-26",
        headers={"Authorization": f"Bearer {scanner_token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "manager role required"


def test_manager_can_read_daily_throughput(client, scanner_token, manager_token):
    scan_response = client.post(
        "/scans",
        json=SCAN,
        headers={"Authorization": f"Bearer {scanner_token}"},
    )
    report_response = client.get(
        "/reports/daily-throughput?date=2026-10-26",
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    assert scan_response.status_code == 201
    assert report_response.status_code == 200
    assert report_response.json() == {
        "date": "2026-10-26",
        "counts": {
            "cutting": 1,
            "stitching": 0,
            "finishing": 0,
            "qc": 0,
            "packed": 0,
        },
    }


def test_scan_for_unknown_piece_returns_not_found(client, scanner_token):
    response = client.post(
        "/scans",
        json={**SCAN, "piece_id": "unknown-piece"},
        headers={"Authorization": f"Bearer {scanner_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Piece 'unknown-piece' not found"


def test_scan_id_cannot_be_reused_with_different_payload(client, scanner_token):
    headers = {"Authorization": f"Bearer {scanner_token}"}
    first = client.post("/scans", json=SCAN, headers=headers)
    conflicting = client.post(
        "/scans",
        json={**SCAN, "employee_id": "different-employee"},
        headers=headers,
    )

    assert first.status_code == 201
    assert conflicting.status_code == 409
    assert conflicting.json()["detail"] == (
        "scan_id has already been used with a different payload"
    )


def test_missing_and_invalid_tokens_cannot_read_manager_report(client):
    missing = client.get("/reports/daily-throughput?date=2026-10-26")
    invalid = client.get(
        "/reports/daily-throughput?date=2026-10-26",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
