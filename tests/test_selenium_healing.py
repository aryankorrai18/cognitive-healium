# tests/test_selenium_healing.py
"""
Selenium self-healing tests — same local fixture page as Playwright tests.
Both frameworks share the SAME ChromaDB memory.

Run:
    pytest tests/test_selenium_healing.py --healium-enabled -v
"""

import time
import threading
import http.server
import functools
import pytest
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def local_server():
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(FIXTURE_DIR)
    )
    server = http.server.HTTPServer(("127.0.0.1", 9877), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)
    yield "http://127.0.0.1:9877"
    server.shutdown()


@pytest.fixture
def chrome_options():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    return opts


@pytest.mark.healium
def test_selenium_fill_heals(healing_driver_factory, chrome_options, local_server):
    driver = webdriver.Chrome(options=chrome_options)
    h = healing_driver_factory(driver)

    try:
        h.get(f"{local_server}/test_page.html")
        time.sleep(1)

        h.find_element(By.ID, "search-input").send_keys("initial")
        h.execute_script("window.BREAK_UI()")

        h.fill(
            By.ID, "search-input",
            "Selenium healed this!",
            intent="product search input field"
        )

        value = h.execute_script("return document.querySelector('input').value")
        assert value == "Selenium healed this!", f"Unexpected value: {value}"
        assert h.healing_events, "Expected a healing event"
        assert h.healing_events[0].status == "healed"

    finally:
        driver.quit()


@pytest.mark.healium
def test_selenium_click_heals(healing_driver_factory, chrome_options, local_server):
    driver = webdriver.Chrome(options=chrome_options)
    h = healing_driver_factory(driver)

    try:
        h.get(f"{local_server}/test_page.html")
        time.sleep(1)

        h.find_element(By.ID, "search-input").send_keys("test query")
        h.execute_script("window.BREAK_UI()")

        h.click(By.ID, "search-btn", intent="search submit button")

        result = h.execute_script(
            "return document.getElementById('result').textContent"
        )
        assert result != "", "Expected result div to have content after click"

    finally:
        driver.quit()