"""Time-based alerting; tested independently from camera and ML libraries."""

from dataclasses import dataclass


@dataclass
class AlertState:
    trigger_seconds: float = 1.5
    closed_since: float | None = None
    last_beep: float = -1e9
    cooldown_seconds: float = 3.0

    def update(self, now: float, closed: bool | None) -> tuple[float, bool, bool]:
        """Return (continuous closed seconds, alarm state, play sound now).

        A missed face cancels the episode, rather than assuming closed eyes.
        """
        if closed is not True:
            self.closed_since = None
            return 0.0, False, False
        if self.closed_since is None:
            self.closed_since = now
        duration = max(0.0, now - self.closed_since)
        alarm = duration >= self.trigger_seconds
        should_beep = alarm and now - self.last_beep >= self.cooldown_seconds
        if should_beep:
            self.last_beep = now
        return duration, alarm, should_beep
