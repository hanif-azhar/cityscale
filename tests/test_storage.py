from pathlib import Path

from modules.storage import list_runs, load_run, save_run


def test_storage_round_trip(tmp_path: Path):
    payload = {"city": "demo", "value": 123}
    saved = save_run(tmp_path, payload)

    assert saved.exists()

    runs = list_runs(tmp_path)
    assert runs

    loaded = load_run(saved)
    assert loaded["city"] == "demo"
    assert loaded["value"] == 123
