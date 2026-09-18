"""Unit tests for OS-aware dedicated-server and SteamCMD path detection."""

from __future__ import annotations

from pathlib import Path

from satisfactory_shell.utils import platform as plat


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return path


def test_server_exe_prefers_linux_shipping(tmp_path: Path) -> None:
    shipping = _touch(
        tmp_path / "Engine" / "Binaries" / "Linux" / "FactoryServer-Linux-Shipping"
    )
    _touch(tmp_path / "FactoryServer.sh")
    _touch(tmp_path / "FactoryServer.exe")
    assert plat.server_exe(tmp_path) == shipping


def test_server_exe_falls_back_to_windows(tmp_path: Path) -> None:
    exe = _touch(tmp_path / "FactoryServer.exe")
    assert plat.server_exe(tmp_path) == exe


def test_server_exe_none_without_root() -> None:
    assert plat.server_exe(None) is None


def test_find_server_root_walks_up(tmp_path: Path) -> None:
    root = tmp_path / "server"
    _touch(root / "FactoryServer.exe")
    nested = root / "a" / "b"
    nested.mkdir(parents=True)
    assert plat.find_server_root(nested) == root


def test_version_file_linux_then_windows(tmp_path: Path) -> None:
    linux = _touch(
        tmp_path
        / "Engine"
        / "Binaries"
        / "Linux"
        / "FactoryServer-Linux-Shipping.version"
    )
    _touch(
        tmp_path / "Engine" / "Binaries" / "Win64" / "FactoryServer-Win64-Shipping.version"
    )
    assert plat.version_file(tmp_path) == linux


def test_version_file_windows_only(tmp_path: Path) -> None:
    win = _touch(
        tmp_path / "Engine" / "Binaries" / "Win64" / "FactoryServer-Win64-Shipping.version"
    )
    assert plat.version_file(tmp_path) == win


def test_find_steamcmd_local(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("satisfactory_shell.utils.platform.shutil.which", lambda _name: None)
    script = _touch(tmp_path / "steamcmd" / "steamcmd.sh")
    assert plat.find_steamcmd(tmp_path) == script


def test_user_config_dir_xdg(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(plat, "is_windows", lambda: False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert plat.user_config_dir(windows_fallback=tmp_path) == tmp_path / "xdg" / "satisfactory-shell"


def test_process_name_matches() -> None:
    assert plat.process_name_matches("FactoryServer.exe")
    assert plat.process_name_matches("FactoryServer-Linux-Shipping")
    assert not plat.process_name_matches("steamcmd")
