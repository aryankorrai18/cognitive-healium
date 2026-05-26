"""
Playwright self-healing tests using the local fixture page.
Fast — no network needed.
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
    healing_page.page.fill("#search-input", "initial test")
    healing_page.page.evaluate("window.BREAK_UI()")

    healing_page.fill(
        "#search-input",
        "Healium healed this!",
        intent="product search input field"
    )

    value = healing_page.page.evaluate("document.querySelector('input').value")
    assert value == "Healium healed this!", f"Unexpected value: {value}"

    assert healing_page.healing_events, "Expected at least one healing event"
    assert healing_page.healing_events[0].status == "healed"
    assert healing_page.healing_events[0].confidence > 0.5