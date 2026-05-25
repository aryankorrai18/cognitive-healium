# tests/test_playwright_healing.py
"""
Playwright self-healing tests using the local fixture page.
Fast — no network needed.

Run:
    pytest tests/test_playwright_healing.py --healium-enabled -v
"""

import threading
import time
import http.server
import functools
import pytest
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def local_server():
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(FIXTURE_DIR)
    )
    server = http.server.HTTPServer(("127.0.0.1", 9876), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)
    yield "http://127.0.0.1:9876"
    server.shutdown()


@pytest.mark.healium
def test_fill_heals_broken_input(healing_page, local_server):
    healing_page.goto(f"{local_server}/test_page.html")

    # Confirm locator works before breaking
    healing_page.page.fill("#search-input", "initial test")

    # Break the UI
    healing_page.page.evaluate("window.BREAK_UI()")

    # '#search-input' no longer exists — Healium must find it
    healing_page.fill(
        "#search-input",
        "Healium healed this!",
        intent="product search input field"
    )

    value = healing_page.page.evaluate(
        "document.querySelector('input').value"
    )
    assert value == "Healium healed this!", f"Unexpected value: {value}"

    assert healing_page.healing_events, "Expected at least one healing event"
    assert healing_page.healing_events[0].status == "healed"
    assert healing_page.healing_events[0].confidence > 0.5


@pytest.mark.healium
def test_click_heals_broken_button(healing_page, local_server):
    healing_page.goto(f"{local_server}/test_page.html")
    healing_page.page.fill("#search-input", "test query")
    healing_page.page.evaluate("window.BREAK_UI()")

    healing_page.click(
        "#search-btn",
        intent="search submit button"
    )

    result_text = healing_page.page.inner_text("#result")
    assert "test query" in result_text or result_text != ""


@pytest.mark.healium
def test_no_healing_needed_when_locator_valid(healing_page, local_server):
    healing_page.goto(f"{local_server}/test_page.html")

    # DON'T break the UI
    healing_page.fill(
        "#search-input",
        "no healing needed",
        intent="product search input field"
    )

    assert len(healing_page.healing_events) == 0, \
        "Healing should not trigger for a valid locator"