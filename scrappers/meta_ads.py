"""
Consulta la Meta Ads Library API (pública, sin autenticación de usuario).
Documentación: https://www.facebook.com/ads/library/api/
"""
import requests
from datetime import datetime

META_ADS_URL = "https://graph.facebook.com/v19.0/ads_archive"

def get_meta_ads(
    page_name: str,
    access_token: str,
    country: str = "AR",
    limit: int = 20
) -> dict:
    """
    Busca avisos activos o recientes de una página en la Ads Library.
    Requiere un Meta App Access Token (app_id|app_secret) — gratuito.
    """
    result = {
        "page_name": page_name,
        "scraped_at": datetime.now().isoformat(),
        "status": "ok",
        "ads": [],
        "total_found": 0,
        "error": None,
    }

    params = {
        "search_terms": page_name,
        "ad_type": "ALL",
        "ad_reached_countries": country,
        "fields": "ad_creative_body,ad_creative_link_caption,ad_creative_link_description,ad_creative_link_title,ad_snapshot_url,page_name,spend,impressions,ad_delivery_start_time,ad_delivery_stop_time",
        "limit": limit,
        "access_token": access_token,
    }

    try:
        resp = requests.get(META_ADS_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        ads_raw = data.get("data", [])
        result["total_found"] = len(ads_raw)

        for ad in ads_raw:
            parsed = {
                "page_name": ad.get("page_name", ""),
                "title": ad.get("ad_creative_link_title", ""),
                "body": ad.get("ad_creative_body", ""),
                "description": ad.get("ad_creative_link_description", ""),
                "caption": ad.get("ad_creative_link_caption", ""),
                "start_date": ad.get("ad_delivery_start_time", ""),
                "end_date": ad.get("ad_delivery_stop_time", ""),
                "snapshot_url": ad.get("ad_snapshot_url", ""),
                "spend": ad.get("spend", {}),
                "impressions": ad.get("impressions", {}),
            }
            result["ads"].append(parsed)

    except requests.exceptions.HTTPError as e:
        result["status"] = "error"
        try:
            err_data = e.response.json()
            result["error"] = err_data.get("error", {}).get("message", str(e))
        except Exception:
            result["error"] = str(e)
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def get_ads_for_competitors(competitors: list, access_token: str, country: str = "AR") -> list:
    """
    competitors: [{"name": "Marca X", "facebook_page": "MarcaX"}, ...]
    """
    results = []
    for comp in competitors:
        page = comp.get("facebook_page") or comp.get("name", "")
        ads_data = get_meta_ads(page, access_token, country)
        ads_data["competitor_name"] = comp.get("name", page)
        results.append(ads_data)
    return results
