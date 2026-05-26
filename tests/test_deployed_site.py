"""
Production Integration Test.
Runs against the LIVE deployed GitHub Pages site.
Uses the cognitive-healium package just like a real QA engineer would.
"""

import os
import pytest
from playwright.sync_api import sync_playwright

from healing_agent import SelfHealingPage
from engine.memory import HealiumMemory

DEPLOYED_URL = os.getenv(
    "DEPLOYED_URL", 
    "https://aryankorrai18.github.io/cognitive-healium/"
)


@pytest.mark.healium
def test_deployed_search_input():
    """QA expects #search-input. If dev changed it, SDK heals it."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        memory = HealiumMemory(tenant_id="production-ci")
        healing_page = SelfHealingPage(page, memory=memory)

        # Go to the LIVE deployed site
        healing_page.goto(DEPLOYED_URL)

        # The QA test expects #search-input. 
        # If the dev changed the ID, the SDK will heal it automatically!
        healing_page.fill(
            "#search-input",
            "Healium healed production!",
            intent="product search input field"
        )

        # Verify it worked
        value = page.evaluate("document.querySelector('input').value")
        assert value == "Healium healed production!", f"Unexpected value: {value}"

        # If the SDK healed it, we check the event
        if healing_page.healing_events:
            assert healing_page.healing_events[0].status == "healed"

        browser.close()