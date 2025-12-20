import os
import xml.etree.ElementTree as ET
from datetime import datetime
from app.core.supabase import _client, _TABLE

NS_SITEMAP = "http://www.sitemaps.org/schemas/sitemap/0.9"
NS_IMAGE = "http://www.google.com/schemas/sitemap-image/1.1"

ET.register_namespace("", NS_SITEMAP)
ET.register_namespace("image", NS_IMAGE)

STATIC_LASTMOD = "2025-12-20"


def get_sitemap_xml() -> str:
    base_url = os.getenv("NEXT_PUBLIC_BASE_URL", "https://bodoge-no-mikata.vercel.app")

    response = (
        _client.table(_TABLE).select("slug, title, updated_at, image_url").execute()
    )
    games = response.data

    root = ET.Element(f"{{{NS_SITEMAP}}}urlset")

    static_pages = [
        {"loc": "/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "/data", "priority": "0.8", "changefreq": "weekly"},
    ]

    for page in static_pages:
        url_elem = ET.SubElement(root, f"{{{NS_SITEMAP}}}url")

        loc = ET.SubElement(url_elem, f"{{{NS_SITEMAP}}}loc")
        loc.text = f"{base_url}{page['loc']}"

        lastmod = ET.SubElement(url_elem, f"{{{NS_SITEMAP}}}lastmod")
        lastmod.text = STATIC_LASTMOD

        changefreq = ET.SubElement(url_elem, f"{{{NS_SITEMAP}}}changefreq")
        changefreq.text = page["changefreq"]

        priority = ET.SubElement(url_elem, f"{{{NS_SITEMAP}}}priority")
        priority.text = page["priority"]

    for game in games:
        url_elem = ET.SubElement(root, f"{{{NS_SITEMAP}}}url")

        loc = ET.SubElement(url_elem, f"{{{NS_SITEMAP}}}loc")
        loc.text = f"{base_url}/games/{game['slug']}"

        lastmod = ET.SubElement(url_elem, f"{{{NS_SITEMAP}}}lastmod")
        updated = game.get("updated_at")
        if updated:
            dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            lastmod.text = dt.strftime("%Y-%m-%d")
        else:
            lastmod.text = STATIC_LASTMOD

        changefreq = ET.SubElement(url_elem, f"{{{NS_SITEMAP}}}changefreq")
        changefreq.text = "weekly"

        priority = ET.SubElement(url_elem, f"{{{NS_SITEMAP}}}priority")
        priority.text = "0.7"

        image_url = game.get("image_url")
        if image_url:
            if image_url.startswith("/"):
                image_url = f"{base_url}{image_url}"

            img = ET.SubElement(url_elem, f"{{{NS_IMAGE}}}image")

            img_loc = ET.SubElement(img, f"{{{NS_IMAGE}}}loc")
            img_loc.text = image_url

            img_title = ET.SubElement(img, f"{{{NS_IMAGE}}}title")
            img_title.text = game.get("title", "")

    xml_str = ET.tostring(root, encoding="unicode", method="xml")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
