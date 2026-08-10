import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Bad_USB_Classifier import payload_setup_agent as psa

DISCORD_HOOK_URL = "https://discord.com/api/webhooks/000000000000000000/fake-token"


def test_scan_file_detects_discord_webhook():
    content = 'STRING $webhook = "DiscordWebhook";\n'
    matches = psa.scan_file(content)
    keys = [m.spec.key for m in matches]
    assert "discord_webhook" in keys


def test_scan_file_ignores_powershell_type_casts():
    content = "STRING $k=[Math]::Ceiling(100/2);\n"
    matches = psa.scan_file(content)
    assert not any(m.spec.key == "bracket_placeholder" for m in matches)


def test_scan_file_detects_all_caps_bracket_placeholder():
    content = "STRING nc [LISTENER_IP_ADDRESS] [PORT]\n"
    matches = psa.scan_file(content)
    placeholders = {
        m.placeholder for m in matches if m.spec.key == "bracket_placeholder"
    }
    assert "[LISTENER_IP_ADDRESS]" in placeholders
    assert "[PORT]" in placeholders


def test_scan_file_clean_script_has_no_matches():
    content = "REM harmless prank\nDELAY 500\nSTRING notepad\nENTER\n"
    assert psa.scan_file(content) == []


def test_discord_webhook_url_validation():
    assert psa.DISCORD_WEBHOOK_RE.match(DISCORD_HOOK_URL)
    assert not psa.DISCORD_WEBHOOK_RE.match("not-a-webhook-url")


def test_analyze_tree_classifies_ready_vs_to_configure(tmp_path):
    (tmp_path / "clean.txt").write_text("REM prank\nSTRING hi\nENTER\n")
    (tmp_path / "needs_config.txt").write_text('STRING $webhook = "DiscordWebhook";\n')

    plan = psa.analyze_tree(tmp_path, use_ollama=False, model="unused")

    ready_names = {p.name for p in plan.ready}
    configure_names = {p.name for p in plan.to_configure}
    assert "clean.txt" in ready_names
    assert "needs_config.txt" in configure_names


def test_apply_and_copy_in_place_writes_configured_value(tmp_path):
    f = tmp_path / "needs_config.txt"
    f.write_text('STRING $webhook = "DiscordWebhook";\n')

    plan = psa.analyze_tree(tmp_path, use_ollama=False, model="unused")
    values = {"discord_webhook": {f: DISCORD_HOOK_URL}}

    psa.apply_and_copy(tmp_path, tmp_path, plan, values)

    assert DISCORD_HOOK_URL in f.read_text()
