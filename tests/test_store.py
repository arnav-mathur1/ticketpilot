"""Local JSON store: save -> get -> list_pending -> set_status lifecycle."""
import src.shared.store as store


def test_local_store_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "QUEUE_PATH", tmp_path / "queue.json")
    monkeypatch.setattr(store, "_AWS", False)

    store.save({"id": "T1", "status": store.PENDING, "category": "billing"})
    assert store.get("T1")["status"] == store.PENDING
    assert [r["id"] for r in store.list_pending()] == ["T1"]

    store.set_status("T1", store.APPROVED)
    assert store.get("T1")["status"] == store.APPROVED
    assert store.list_pending() == []
