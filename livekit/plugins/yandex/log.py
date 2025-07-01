"""Basic logging utilities for Yandex SpeechKit STT plugin."""

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

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator

logger = logging.getLogger("livekit.plugins.yandex")


def log_with_context(level: int, message: str, **context: Any) -> None:
    """Log message with context information."""
    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        message = f"[{context_str}] {message}"
    logger.log(level, message)


@contextmanager
def log_timing(operation: str, **context: Any) -> Generator[Dict[str, Any], None, None]:
    """Context manager to log operation timing."""
    start_time = time.time()
    logger.debug(f"Starting {operation}")

    timing_info = {"start_time": start_time}

    try:
        yield timing_info
        duration = time.time() - start_time
        timing_info["duration"] = duration
        log_with_context(logging.INFO, f"Completed {operation} in {duration:.3f}s", **context)
    except Exception as e:
        duration = time.time() - start_time
        timing_info["duration"] = duration
        log_with_context(logging.ERROR, f"Failed {operation} after {duration:.3f}s: {e}", **context)
        raise
