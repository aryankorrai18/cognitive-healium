"""
healium_plugin.py

pytest plugin for Cognitive Healium.
Registers itself automatically when listed in conftest.py:

    # tests/conftest.py
    pytest_plugins = ["healium_plugin"]

CLI flags:
    --healium-enabled       activate self-healing
    --healium-tenant=NAME   isolate ChromaDB collection (default: pytest-session)
    --healium-fresh         wipe ChromaDB before the run (clean-slate demo)

Fixtures provided:
    healium_memory          shared HealiumMemory (session-scoped)
    healing_page            SelfHealingPage wrapping a pytest-playwright `page`
    healing_driver_factory  factory -> SelfHealingDriver wrapping any Selenium driver
"""

import shutil
import logging
import pytest

logger = logging.getLogger("healium")


def pytest_addoption(parser):
    g = parser.getgroup("healium", "Cognitive Healium self-healing")
    g.addoption(
        "--healium-enabled", action="store_true", default=False,
        help="Enable Cognitive Healium self-healing for all tests"
    )
    g.addoption(
        "--healium-tenant", default="pytest-session",
        help="ChromaDB collection name / tenant ID (default: pytest-session)"
    )
    g.addoption(
        "--healium-fresh", action="store_true", default=False,
        help="Clear ChromaDB memory before the run (good for clean demos)"
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "healium: mark test as using Cognitive Healium self-healing"
    )


@pytest.fixture(scope="session")
def _healium_enabled(request) -> bool:
    return request.config.getoption("--healium-enabled")


@pytest.fixture(scope="session")
def _healium_tenant(request) -> str:
    return request.config.getoption("--healium-tenant")


@pytest.fixture(scope="session")
def healium_providers(_healium_enabled):
    if not _healium_enabled:
        return None, None, None
    from engine.providers import get_providers
    return get_providers()


@pytest.fixture(scope="session")
def healium_memory(request, _healium_enabled, _healium_tenant):
    if not _healium_enabled:
        return None

    if request.config.getoption("--healium-fresh"):
        shutil.rmtree("data/", ignore_errors=True)
        logger.info("Healium: ChromaDB cleared (--healium-fresh)")

    from engine.memory import HealiumMemory
    mem = HealiumMemory(tenant_id=_healium_tenant)
    logger.info(f"Healium: memory ready (tenant: {_healium_tenant})")
    return mem


@pytest.fixture
def healing_page(page, _healium_enabled, healium_memory, healium_providers):
    if not _healium_enabled or healium_memory is None:
        yield page
        return

    from healing_agent import SelfHealingPage
    cache, storage, event_store = healium_providers

    hp = SelfHealingPage(
        page             = page,
        memory           = healium_memory,
        tenant_id        = healium_memory.tenant_id,
        cache_provider   = cache,
        storage_provider = storage,
        event_store      = event_store,
    )
    yield hp

    if hp.healing_events:
        healed = sum(1 for e in hp.healing_events if e.status == "healed")
        logger.info(
            f"Healium [playwright | {hp.tenant_id}]: "
            f"{healed}/{len(hp.healing_events)} locators auto-healed"
        )


@pytest.fixture
def healing_driver_factory(_healium_enabled, healium_memory, healium_providers):
    from engine.selenium_wrapper import SelfHealingDriver
    cache, storage, event_store = healium_providers or (None, None, None)
    created: list = []

    def factory(driver, tenant_id: str = None):
        h = SelfHealingDriver(
            driver           = driver,
            memory           = healium_memory,
            tenant_id        = tenant_id or (
                healium_memory.tenant_id if healium_memory else "default"
            ),
            cache_provider   = cache,
            storage_provider = storage,
            event_store      = event_store,
        )
        created.append(h)
        return h

    yield factory

    for h in created:
        if h.healing_events:
            healed = sum(1 for e in h.healing_events if e.status == "healed")
            logger.info(
                f"Healium [selenium | {h.tenant_id}]: "
                f"{healed}/{len(h.healing_events)} locators auto-healed"
            )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    yield
    for fixture_name in ("healing_page",):
        val = item.funcargs.get(fixture_name)
        if val and hasattr(val, "healing_events") and val.healing_events:
            healed = sum(1 for e in val.healing_events if e.status == "healed")
            item.user_properties.append(("healium_total",  len(val.healing_events)))
            item.user_properties.append(("healium_healed", healed))