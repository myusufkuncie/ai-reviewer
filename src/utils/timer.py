"""Simple step timer for debugging slow processes"""

import time


class StepTimer:
    """Tracks elapsed time between process steps"""

    def __init__(self):
        self._start = time.time()
        self._step_start = self._start

    def step(self, label: str) -> float:
        """Print label with elapsed time since last step and total elapsed.

        Returns seconds since last step.
        """
        now = time.time()
        step_elapsed = now - self._step_start
        total_elapsed = now - self._start
        print(
            f"[{total_elapsed:6.1f}s total | +{step_elapsed:5.2f}s] {label}"
        )
        self._step_start = now
        return step_elapsed

    def reset_step(self):
        """Reset step timer without printing (e.g. at start of a new file)"""
        self._step_start = time.time()
