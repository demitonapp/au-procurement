"""fetch_releases' `since` translations must name real scraper parameters.

api.py maps the generic `since` date onto each scraper's native parameter.
Nothing tied those names to the scrapers themselves, so when nsw/live.py was
rewritten and dropped `from_date`, the translation kept injecting it and every
`since` call died with TypeError - silently, for two months, because the only
caller logged the failure and returned an empty package.
"""
import importlib
import inspect
from datetime import date

import pytest

from opencontractau.api import _JURISDICTION_SCRAPERS, fetch_releases

# Jurisdiction -> the kwarg api.py injects when `since` is given.
TRANSLATIONS = {"ACT": "where", "AUSTENDER": "from_date"}


@pytest.mark.parametrize("key,param", TRANSLATIONS.items())
def test_translated_kwarg_is_accepted_by_scraper(key, param):
    scrape = importlib.import_module(_JURISDICTION_SCRAPERS[key]).scrape
    assert param in inspect.signature(scrape).parameters, (
        f"api.py injects {param!r} for {key}, but its scrape() no longer takes it"
    )


@pytest.mark.asyncio
async def test_since_is_dropped_for_scrapers_without_a_date_param(monkeypatch):
    """NSW_LIVE takes max_pages only; `since` must not reach it."""
    seen = {}

    async def fake_scrape(**kwargs):
        seen.update(kwargs)
        return "package"

    module = importlib.import_module(_JURISDICTION_SCRAPERS["NSW_LIVE"])
    monkeypatch.setattr(module, "scrape", fake_scrape)

    assert await fetch_releases("NSW_LIVE", since=date(2026, 1, 1), max_pages=2) == "package"
    assert seen == {"max_pages": 2}
