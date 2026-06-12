import matplotlib
import subprocess

matplotlib.use("Agg")

from essemtec import app as app_module


def test_run_app_without_csv_does_not_open_file_dialog(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("file dialog should not open automatically")

    monkeypatch.setattr(app_module, "ask_for_csv_file", fail_if_called)
    monkeypatch.setattr(app_module.TemperaturePlotApp, "run", lambda self: None)

    assert app_module.run_app() == 0


def test_macos_file_dialog_uses_native_osascript(monkeypatch) -> None:
    calls = []

    def fake_run(command, capture_output, text, check):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="/tmp/example.csv\n", stderr="")

    monkeypatch.setattr(app_module.subprocess, "run", fake_run)

    assert app_module.ask_for_csv_file_macos("Choose CSV") == app_module.Path("/tmp/example.csv")
    assert calls == [["osascript", "-e", 'POSIX path of (choose file with prompt "Choose CSV")']]


def test_macos_file_dialog_returns_none_when_cancelled(monkeypatch) -> None:
    def fake_run(command, capture_output, text, check):
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="User canceled.")

    monkeypatch.setattr(app_module.subprocess, "run", fake_run)

    assert app_module.ask_for_csv_file_macos("Choose CSV") is None
