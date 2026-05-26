"""
Production Integration Test.
Runs against the LIVE deployed GitHub Pages site.
Uses the cognitive-healium package just like a real QA engineer would.
"""

import os
import pytest
from playwright.sync_api import sync_playwright

# Importing exactly as a user would after pip install cognitive-healium
from healing_agent import SelfHealingPage
from engine.memory import HealiumMemory

# The deployed frontend URL
DEPLOYED_URL = os.getenv(
    "DEPLOYED_URL", 
    "https://aryankorrai18.github.io/cognitive-healium/"
)


@pytest.mark.healium
def test_deployed_search_input_heals():
    """A developer renamed the search input. Healium must heal it on the live site."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Initialize Healium just like an external user
        memory = HealiumMemory(tenant_id="production-ci")
        healing_page = SelfHealingPage(page, memory=memory)

        # 1. Go to the LIVE deployed site
        healing_page.goto(DEPLOYED_URL)

        # 2. Confirm the selector works normally
        page.fill("#search-input", "baseline check")

        # 3. Simulate the UI breaking on the deployed site
        page.evaluate("window.BREAK_UI()")

        # 4. The old locator fails -> AI heals it
        healing_page.fill(
            "#search-input",
            "Healium healed production!",
            intent="product search input field"
        )

        # 5. Verify it actually worked
        value = page.evaluate("document.querySelector('input').value")
        assert value == "Healium healed production!", f"Unexpected value: {value}"

        assert healing_page.healing_events, "Expected at least one healing event"
        assert healing_page.healing_events[0].status == "healed"

        browser.close()


@pytest.mark.healium
def test_deployed_search_button_heals():
    """Verify the deployed site's search button can be healed when broken."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        memory = HealiumMemory(tenant_id="production-ci")
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