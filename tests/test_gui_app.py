import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui import app as gui_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(gui_app, "WORKSPACE", tmp_path)
    monkeypatch.setattr(gui_app, "SOURCE_DIR", tmp_path / "source")
    monkeypatch.setattr(gui_app, "ORGANIZED_DIR", tmp_path / "organized")
    monkeypatch.setattr(gui_app, "READY_DIR", tmp_path / "ready")
    for d in (gui_app.SOURCE_DIR, gui_app.ORGANIZED_DIR, gui_app.READY_DIR):
        d.mkdir(parents=True, exist_ok=True)
    gui_app.app.config["TESTING"] = True
    with gui_app.app.test_client() as c:
        yield c


def test_index_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"BK_Flipper_Full_Pipline" in resp.data


def test_tree_unknown_stage_rejected(client):
    resp = client.get("/api/tree/nope")
    assert resp.status_code == 400


def test_tree_empty_source(client):
    resp = client.get("/api/tree/source")
    assert resp.status_code == 200
    assert resp.get_json()["children"] == []


def test_upload_writes_nested_files(client):
    data = {
        "files": [
            (io.BytesIO(b"REM prank\nSTRING hi\nENTER\n"), "a.txt"),
            (io.BytesIO(b'STRING $webhook = "DiscordWebhook";\n'), "b.txt"),
        ],
        "relpaths": ["myrepo/a.txt", "myrepo/sub/b.txt"],
    }
    resp = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["written"] == 2
    assert (gui_app.SOURCE_DIR / "myrepo" / "a.txt").is_file()
    assert (gui_app.SOURCE_DIR / "myrepo" / "sub" / "b.txt").is_file()


def test_upload_rejects_path_traversal(client):
    data = {
        "files": [(io.BytesIO(b"pwned"), "evil.txt")],
        "relpaths": ["../../evil.txt"],
    }
    resp = client.post("/api/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "Invalid" in resp.get_json()["error"]
    assert not (gui_app.WORKSPACE.parent.parent / "evil.txt").exists()


def test_clone_rejects_non_http_url(client):
    resp = client.post("/api/clone", json={"url": "file:///etc/passwd"})
    assert resp.status_code == 400


def test_classify_then_enrich_then_apply_full_flow(client):
    (gui_app.SOURCE_DIR / "a.txt").write_text("REM prank\nSTRING hi\nENTER\n")
    (gui_app.SOURCE_DIR / "b.txt").write_text('STRING $webhook = "DiscordWebhook";\n')

    resp = client.post("/api/classify", json={"use_ollama": False})
    assert resp.status_code == 200

    resp = client.post("/api/enrich/scan", json={"use_ollama": False})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["to_configure_count"] == 1
    field_keys = [f["key"] for f in body["fields"]]
    assert "discord_webhook" in field_keys

    resp = client.post(
        "/api/enrich/apply", json={"values": {"discord_webhook": "not-a-url"}}
    )
    assert resp.status_code == 400

    valid_url = "https://discord.com/api/webhooks/123456789012345678/abcXYZ"
    resp = client.post(
        "/api/enrich/apply", json={"values": {"discord_webhook": valid_url}}
    )
    assert resp.status_code == 200

    ready_files = list(gui_app.READY_DIR.rglob("b.txt"))
    assert ready_files
    assert valid_url in ready_files[0].read_text()


def test_reset_clears_stage(client):
    (gui_app.SOURCE_DIR / "x.txt").write_text("hi")
    resp = client.post("/api/reset", json={"stage": "source"})
    assert resp.status_code == 200
    assert list(gui_app.SOURCE_DIR.iterdir()) == []


# ─── Clone depuis un fichier .txt d'URLs ────────────────────────────────────


@pytest.fixture
def fake_default_url_file(tmp_path, monkeypatch):
    url_file = tmp_path / "default_url.txt"
    url_file.write_text(
        "# commentaire\nhttps://github.com/a/repo-a\nhttps://github.com/b/repo-b\n"
    )
    monkeypatch.setattr(gui_app, "DEFAULT_URL_FILE", url_file)
    return url_file


def test_urlfile_default_returns_content_and_count(client, fake_default_url_file):
    resp = client.get("/api/urlfile/default")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] == 2
    assert body["filename"] == "default_url.txt"


def test_urlfile_default_missing_returns_404(client, monkeypatch, tmp_path):
    monkeypatch.setattr(gui_app, "DEFAULT_URL_FILE", tmp_path / "does_not_exist.txt")
    resp = client.get("/api/urlfile/default")
    assert resp.status_code == 404


def test_clone_list_uses_default_when_no_file_uploaded(
    client, fake_default_url_file, monkeypatch
):
    calls = []

    def fake_download(url_file, download_dir):
        calls.append(Path(url_file))
        (download_dir / "repo-a").mkdir()
        (download_dir / "repo-b").mkdir()
        return download_dir

    monkeypatch.setattr(gui_app, "download_repos_from_urls", fake_download)

    resp = client.post("/api/clone-list", data={}, content_type="multipart/form-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 2
    assert sorted(body["new_repos"]) == ["repo-a", "repo-b"]
    assert calls == [fake_default_url_file]


def test_clone_list_uses_uploaded_file_when_provided(client, monkeypatch):
    def fake_download(url_file, download_dir):
        assert Path(url_file).read_text().strip() == "https://github.com/x/y"
        (download_dir / "y").mkdir()
        return download_dir

    monkeypatch.setattr(gui_app, "download_repos_from_urls", fake_download)

    data = {
        "file": (io.BytesIO(b"https://github.com/x/y\n"), "mylist.txt"),
    }
    resp = client.post("/api/clone-list", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["source_label"] == "mylist.txt"
    assert body["new_repos"] == ["y"]
