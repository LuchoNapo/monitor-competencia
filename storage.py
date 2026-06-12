"""
Capa de persistencia de Atalaya — Supabase (PostgreSQL).

Mantiene la misma interfaz que la versión anterior basada en JSON, así que
app.py no necesita cambios. Las credenciales se leen de los secrets de Streamlit:
    SUPABASE_URL = "https://xxxxx.supabase.co"
    SUPABASE_KEY = "sb_publishable_..."

Tablas (creadas en Supabase):
  clientes(id, nombre, competidores jsonb, creado)
  reportes(id, cliente, report_markdown, model, usage jsonb, generado)
"""
import os
from datetime import datetime

import streamlit as st
from supabase import create_client, Client


# ── Conexión (cacheada para no recrearla en cada rerun) ────────────────────────
@st.cache_resource
def _get_client() -> Client:
    url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_KEY en los secrets.")
    return create_client(url, key)


# ── Clientes ────────────────────────────────────────────────────────────────────
def load_clients_config() -> list:
    """Devuelve la lista de clientes con sus competidores."""
    try:
        sb = _get_client()
        resp = sb.table("clientes").select("nombre, competidores").order("creado").execute()
        return [
            {"name": row["nombre"], "competitors": row.get("competidores", [])}
            for row in resp.data
        ]
    except Exception as e:
        print(f"[STORAGE] Error cargando clientes: {e}")
        return []


def save_clients_config(clients: list):
    """Sincroniza la lista completa de clientes con la base.
    Hace upsert por nombre; elimina los que ya no están."""
    try:
        sb = _get_client()
        nombres_actuales = [c["name"] for c in clients]

        # Upsert de cada cliente (inserta o actualiza según nombre)
        for c in clients:
            sb.table("clientes").upsert(
                {"nombre": c["name"], "competidores": c.get("competitors", [])},
                on_conflict="nombre",
            ).execute()

        # Borrar los que ya no están en la lista
        existentes = sb.table("clientes").select("nombre").execute()
        for row in existentes.data:
            if row["nombre"] not in nombres_actuales:
                sb.table("clientes").delete().eq("nombre", row["nombre"]).execute()
    except Exception as e:
        print(f"[STORAGE] Error guardando clientes: {e}")


# ── Reportes ────────────────────────────────────────────────────────────────────
def save_report(client_name: str, report: dict) -> str:
    """Guarda un reporte generado. Devuelve el id como string."""
    try:
        sb = _get_client()
        resp = sb.table("reportes").insert({
            "cliente": client_name,
            "report_markdown": report.get("report_markdown", ""),
            "model": report.get("model", ""),
            "usage": report.get("usage"),
        }).execute()
        return str(resp.data[0]["id"]) if resp.data else ""
    except Exception as e:
        print(f"[STORAGE] Error guardando reporte: {e}")
        return ""


def get_last_report(client_name: str) -> dict | None:
    """Devuelve el último reporte de un cliente, o None."""
    try:
        sb = _get_client()
        resp = (sb.table("reportes")
                  .select("*")
                  .eq("cliente", client_name)
                  .order("generado", desc=True)
                  .limit(1)
                  .execute())
        if resp.data:
            row = resp.data[0]
            return {
                "report_markdown": row.get("report_markdown", ""),
                "model": row.get("model", ""),
                "usage": row.get("usage"),
                "generated_at": row.get("generado", ""),
            }
        return None
    except Exception as e:
        print(f"[STORAGE] Error obteniendo último reporte: {e}")
        return None


def list_reports(client_name: str) -> list:
    """Lista los reportes de un cliente, del más nuevo al más viejo."""
    try:
        sb = _get_client()
        resp = (sb.table("reportes")
                  .select("id, generado, model")
                  .eq("cliente", client_name)
                  .order("generado", desc=True)
                  .execute())
        return [
            {
                "id": str(row["id"]),
                "path": str(row["id"]),          # 'path' = id, para compatibilidad con app.py
                "generated_at": row.get("generado", ""),
                "status": "ok",
            }
            for row in resp.data
        ]
    except Exception as e:
        print(f"[STORAGE] Error listando reportes: {e}")
        return []


def load_report(report_id: str) -> dict:
    """Carga un reporte completo por su id."""
    try:
        sb = _get_client()
        resp = sb.table("reportes").select("*").eq("id", int(report_id)).limit(1).execute()
        if resp.data:
            row = resp.data[0]
            return {
                "report_markdown": row.get("report_markdown", ""),
                "model": row.get("model", ""),
                "usage": row.get("usage"),
                "generated_at": row.get("generado", ""),
                "client_name": row.get("cliente", ""),
            }
        return {}
    except Exception as e:
        print(f"[STORAGE] Error cargando reporte {report_id}: {e}")
        return {}


# ── Scans (datos crudos) ───────────────────────────────────────────────────────
def save_scan(client_name: str, raw_data: dict) -> str:
    """
    Los datos crudos del scan no se persisten en la base (son voluminosos y
    transitorios). Se mantiene la función por compatibilidad con app.py.
    Si en el futuro querés guardarlos, se puede agregar una tabla 'scans'.
    """
    return ""