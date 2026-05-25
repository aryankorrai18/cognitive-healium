# tests/test_deployed_site.py
"""
Integration test that runs against the LIVE GitHub Pages deployment.
Only runs on main/master branch pushes.

The DEPLOYED_URL env var is set by the CI workflow:
    https://<owner>.github.io/<repo>/
"""

import os
import pytest
from playwright.sync_api import sync_playwright
from engine.memory import HealiumMemory
from healing_agent import SelfHealingPage

DEPLOYED_URL = os.getenv(
    "DEPLOYED_URL",
    "https://YOUR_USERNAME.github.io/cognitive-healium/"
)


@pytest.mark.healium
def test_deployed_site_search_input():
    """Verify the deployed site's search input can be healed when broken."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        memory = HealiumMemory(tenant_id="ci-deployed-test")
        healing_page = SelfHealingPage(page, memory=memory)

        healing_page.goto(DEPLOYED_URL)

        # Confirm the page loaded
        title = page.title()
        assert "Healium" in title or "Test" in title, \
            f"Unexpected page title: {title}"

        # Confirm the selector works normally
        page.fill("#search-input", "baseline check")

        # Break the UI (simulates a developer renaming the element)
        page.evaluate("window.BREAK_UI()")

        # Now the old selector fails — Healium must heal it
        healing_page.fill(
            "#search-input",
            "Healium healed this on deployed site!",
            intent="product search input field"
        )

        # Verify the value was actually set
        value = page.evaluate("document.querySelector('input').value")
        assert value == "Healium healed this on deployed site!", \
            f"Unexpected value: {value}"

        # Verify a healing event was recorded
        assert healing_page.healing_events, \
            "Expected at least one healing event"
        assert healing_page.healing_events[0].status == "healed"

        browser.close()


@pytest.mark.healium
def test_deployed_site_search_button():
    """Verify the deployed site's search button can be healed when broken."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        memory = HealiumMemory(tenant_id="ci-deployed-test")
        healing_page = SelfHealingPage(page, memory=memory)

        healing_page.goto(DEPLOYED_URL)
        page.fill("#search-input", "integration test")

        # Break the button
        page.evaluate("window.BREAK_UI()")

        healing_page.click(
            "#search-btn",
            intent="search submit button"
        )

        result = page.inner_text("#result")
        assert result != "", "Expected result div to show search result"

        browser.close()