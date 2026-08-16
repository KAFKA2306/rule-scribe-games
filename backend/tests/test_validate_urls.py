from app.scripts.validate_urls import _VALIDATE_FIELDS


def test_primary_source_links_are_url_audited():
    assert {"source_url", "official_url"} <= set(_VALIDATE_FIELDS)
