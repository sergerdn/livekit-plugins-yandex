# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Pytest configuration for integration tests.

Integration tests require real Yandex Cloud credentials and test the integration between
unit components and the actual Yandex SpeechKit service. They focus on testing the
interaction between components rather than end-to-end functionality.
"""
from typing import List

import pytest
from _pytest.config import Config
from _pytest.nodes import Item

# Note: validate_credentials, skip_if_no_credentials, and other shared fixtures
# are available from the global tests/conftest.py


# Pytest configuration for integration tests
def pytest_configure(config: Config) -> None:
    """Configure integration test markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (requires credentials)"
    )


def pytest_collection_modifyitems(config: Config, items: List[Item]) -> None:
    """Automatically mark all tests in this directory as integration tests."""
    for item in items:
        item.add_marker(pytest.mark.integration)


# Note: event_loop fixture is available from the global tests/conftest.py


def pytest_sessionstart(session: pytest.Session) -> None:
    """Integration test session start."""
    print("Starting integration tests - requires real credentials")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Integration test session finish."""
    if exitstatus == 0:
        print("Integration tests completed successfully")
    else:
        print(f"Integration tests completed with exit status: {exitstatus}")
