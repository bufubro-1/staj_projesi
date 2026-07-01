"""Proje kök dizini — CSV dosyaları repo kökünde (python/ üst klasör)."""
from pathlib import Path
import os

_KOK: Path | None = None


def proje_kok() -> Path:
    global _KOK
    if _KOK is not None:
        return _KOK

    env = os.getenv("SIRKET_PROJE_KOKU")
    if env:
        _KOK = Path(env).resolve()
        return _KOK

    repo = Path(__file__).resolve().parent.parent
    if (repo / "master_sirketler.csv").exists() or (repo / "dotnet").is_dir():
        _KOK = repo
        return _KOK

    cwd = Path.cwd()
    if (cwd / "master_sirketler.csv").exists():
        _KOK = cwd
        return _KOK

    _KOK = repo
    return _KOK


def csv_yol(dosya: str) -> Path:
    return proje_kok() / dosya
