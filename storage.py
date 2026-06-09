"""
Persistencia simple en JSON. Sin dependencias de BD.
Guarda historial de scans y reportes por cliente.
"""
import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("data")


def _client_dir(client_name: str) -> Path:
    safe_name = client_name.lower().replace(" ", "_")
    path = DATA_DIR / safe_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_scan(client_name: str, raw_data: dict) -> str:
    """Guarda los datos crudos del scan. Devuelve el path."""
    d = _client_dir(client_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = d / f"scan_{timestamp}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    return str(filepath)


def save_report(client_name: str, report: dict) -> str:
    """Guarda el reporte generado. Devuelve el path."""
    d = _client_dir(client_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = d / f"report_{timestamp}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return str(filepath)


def get_last_report(client_name: str) -> dict | None:
    """Devuelve el último reporte guardado para ese cliente."""
    d = _client_dir(client_name)
    reports = sorted(d.glob("report_*.json"), reverse=True)
    if not reports:
        return None
    with open(reports[0], encoding="utf-8") as f:
        return json.load(f)


def list_reports(client_name: str) -> list:
    """Lista todos los reportes de un cliente, del más nuevo al más viejo."""
    d = _client_dir(client_name)
    reports = sorted(d.glob("report_*.json"), reverse=True)
    result = []
    for r in reports:
        try:
            with open(r, encoding="utf-8") as f:
                data = json.load(f)
            result.append({
                "filename": r.name,
                "generated_at": data.get("generated_at", ""),
                "status": data.get("status", ""),
                "path": str(r),
            })
        except Exception:
            pass
    return result


def load_report(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_clients_config() -> list:
    """Carga la config de clientes y sus competidores."""
    config_path = DATA_DIR / "clients.json"
    if not config_path.exists():
        return []
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def save_clients_config(clients: list):
    DATA_DIR.mkdir(exist_ok=True)
    config_path = DATA_DIR / "clients.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)
