"""
Consulta la Meta Ads Library API (pública).
Documentación: https://www.facebook.com/ads/library/api/

IMPORTANTE: para usar esta API necesitás:
1. Completar la verificación de identidad en https://facebook.com/ID
   (subir documento + confirmar país). Tarda 1-3 días hábiles.
2. Un token válido (App Token APP_ID|APP_SECRET, o User Token).
"""
import requests
from datetime import datetime

META_ADS_URL = "https://graph.facebook.com/v21.0/ads_archive"

# Mapa de códigos de error de Meta a mensajes claros
META_ERROR_HINTS = {
    190: "Token inválido o expirado. Generá uno nuevo en el panel de Meta.",
    200: "El token no tiene permisos suficientes. Falta aprobar scopes de Ads Library.",
    10:  "Permiso insuficiente. Verificá identidad en facebook.com/ID y permisos de la app.",
    100: "Parámetro inválido o falta verificación de identidad (facebook.com/ID).",
    613: "Límite de llamadas alcanzado (200/hora). Esperá un rato.",
    4:   "Límite de requests de la app alcanzado. Esperá unos minutos.",
}


def get_meta_ads(
    page_name: str,
    access_token: str,
    country: str = "AR",
    limit: int = 20
) -> dict:
    result = {
        "page_name": page_name,
        "scraped_at": datetime.now().isoformat(),
        "status": "ok",
        "ads": [],
        "total_found": 0,
        "error": None,
        "error_code": None,
        "error_hint": None,
    }

    params = {
        "search_terms": page_name,
        "ad_type": "ALL",
        "ad_reached_countries": country,
        "fields": "ad_creative_bodies,ad_creative_link_captions,ad_creative_link_descriptions,ad_creative_link_titles,ad_snapshot_url,page_name,ad_delivery_start_time,ad_delivery_stop_time",
        "limit": limit,
        "access_token": access_token,
    }

    try:
        resp = requests.get(META_ADS_URL, params=params, timeout=20)

        # Capturar el error de Meta ANTES de raise, para leer el código
        if resp.status_code != 200:
            try:
                err = resp.json().get("error", {})
                code = err.get("code")
                msg  = err.get("message", "Error desconocido")
                result["status"] = "error"
                result["error"] = msg
                result["error_code"] = code
                result["error_hint"] = META_ERROR_HINTS.get(code, "")
            except Exception:
                result["status"] = "error"
                result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            return result

        data = resp.json()
        ads_raw = data.get("data", [])
        result["total_found"] = len(ads_raw)

        for ad in ads_raw:
            # Los campos plurales devuelven listas; tomamos el primer elemento
            def first(lst):
                return lst[0] if isinstance(lst, list) and lst else (lst if isinstance(lst, str) else "")

            parsed = {
                "page_name": ad.get("page_name", ""),
                "title": first(ad.get("ad_creative_link_titles", [])),
                "body": first(ad.get("ad_creative_bodies", [])),
                "description": first(ad.get("ad_creative_link_descriptions", [])),
                "caption": first(ad.get("ad_creative_link_captions", [])),
                "start_date": ad.get("ad_delivery_start_time", ""),
                "end_date": ad.get("ad_delivery_stop_time", ""),
                "snapshot_url": ad.get("ad_snapshot_url", ""),
            }
            result["ads"].append(parsed)

    except requests.exceptions.Timeout:
        result["status"] = "error"
        result["error"] = "Timeout al conectar con Meta"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def get_ads_for_competitors(competitors: list, access_token: str, country: str = "AR") -> list:
    results = []
    for comp in competitors:
        page = comp.get("facebook_page") or comp.get("name", "")
        ads_data = get_meta_ads(page, access_token, country)
        ads_data["competitor_name"] = comp.get("name", page)
        results.append(ads_data)
    return results