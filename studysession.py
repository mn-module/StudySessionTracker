import datetime
import pytz
from typing import Tuple


class StudySession:
    """Represents and manages a study-session for a specific subject."""

    # Initialization and Representation Methods:

    def __init__(self, subject_name: str, timezone: pytz.timezone = pytz.timezone("UTC")):
        """Initialize a StudySession instance."""
        self.subject_name = subject_name
        # Internal attributes
        self._start_time = None
        self._stop_time = None
        self._pause_resume_times = []
        self._cached_cumulative_pause_duration = 0
        self._state = "INACTIVE"
        # Setting timezone
        self.timezone = timezone

    def __repr__(self):
        """Return a developer-friendly representation."""
        return f"StudySession(subject_name={self.subject_name!r}, timezone=pytz.timezone({self.timezone.zone!r}))"

    def __str__(self):
        """Return a user-friendly string representation."""
        return (f"{self.state.capitalize()} study-session for subject: {self.subject_name!r}"
                f" with {self.timezone.zone!r} timezone.")

    # Properties (Getters and Setters):

    @property
    def subject_name(self) -> str:
        """Return the subject_name."""
        return self._subject_name

    @subject_name.setter
    def subject_name(self, name: str) -> None:
        """Setter for the subject_name attribute."""
        if not isinstance(name, str):
            raise TypeError(f"excepted type: 'str', got {type(name).__name__!r} instead!")

        self._subject_name = name

    @property
    def timezone(self) -> pytz.timezone:
        """Return the current timezone object."""
        return self._timezone

    @timezone.setter
    def timezone(self, tz_obj: pytz.timezone) -> None:
        """Setter for timezone attribute."""
        if not isinstance(tz_obj, pytz.BaseTzInfo):
            raise TypeError(f"excepted type: 'pytz.timezone'"
                            f", got {type(tz_obj).__name__!r} instead!")

        if self.state != "INACTIVE":
            raise StudySessionError(f"cannot set timezone for a study-session that is currently {self.state!r}, "
                                    "note: timezone can only be set when the study-session is in 'INACTIVE' state!")

        self._timezone = tz_obj

    @property
    def start_time(self) -> datetime.datetime:
        """Return the start time of the study-session."""
        return self._start_time

    @property
    def stop_time(self) -> datetime.datetime:
        """Return the stop time of the study-session."""
        return self._stop_time

    @property
    def pause_resume_times(self) -> Tuple:
        """Return all pause-resume timestamp pairs from the study session."""
        return tuple(self._pause_resume_times)

    @property
    def state(self) -> str:
        """Return the current state of the study-session."""
        return self._state

    # Instance Methods (Public):
    # Core study-session interaction methods

    def start_tracking(self) -> None:
        """Start tracking the study-session duration."""
        if self.state == "RUNNING":
            raise StudySessionError("this study-session is already running!")
        if self.state == "STOPPED":
            raise StudySessionError("this study-session hasn't been reset!")
        if self.state == "PAUSED":
            raise StudySessionError("cannot start a study-session that is currently paused!")

        self._start_time = datetime.datetime.now(self.timezone)
        self._state = "RUNNING"

    def stop_tracking(self) -> None:
        """Stop tracking the study-session duration."""
        if self.state != "RUNNING" and self.state != "PAUSED":
            raise StudySessionError("cannot stop a study-session that isn't currently running or paused!")

        previous_state = self.state
        self._stop_time = datetime.datetime.now(self.timezone)
        self._state = "STOPPED"
        # Only need to update the cached cumulative pause duration if the study-session stopped from PAUSED state
        if previous_state == "PAUSED":
            self._cached_cumulative_pause_duration = (self._cached_cumulative_pause_duration +
                                                      self.get_pause_duration(-1))

    def pause_tracking(self) -> None:
        """Pause tracking the study-session duration."""
        if self.state != "RUNNING":
            raise StudySessionError("cannot pause a study-session that isn't currently running!")

        self._pause_resume_times.append((datetime.datetime.now(self.timezone), None))
        self._state = "PAUSED"

    def resume_tracking(self) -> None:
        """Resume tracking the study-session from a previously paused state."""
        if self.state != "PAUSED":
            raise StudySessionError("cannot resume a study-session that isn't currently paused!")

        last_pause, _ = self._pause_resume_times[-1]
        self._pause_resume_times[-1] = (last_pause, datetime.datetime.now(self.timezone))
        self._cached_cumulative_pause_duration = self._cached_cumulative_pause_duration + self.get_pause_duration(-1)
        self._state = "RUNNING"

    def discard_tracking(self) -> None:
        """Discard tracking the study-session."""
        if self.state != "RUNNING" and self.state != "PAUSED":
            raise StudySessionError("cannot discard a study-session that isn't currently running or paused!")

        self._start_time = None
        self._pause_resume_times.clear()
        self._cached_cumulative_pause_duration = 0
        self._state = "INACTIVE"

    def reset_tracking(self) -> None:
        """Reset tracking the study-session data to its initial state, excluding the 'total_time'."""
        if self.state != "STOPPED":
            raise StudySessionError("cannot reset a study-session that hasn't been stopped!")

        self._start_time = None
        self._stop_time = None
        self._pause_resume_times.clear()
        self._cached_cumulative_pause_duration = 0
        self._state = "INACTIVE"

    # Calculation methods

    def get_duration(self) -> float:
        """Retrieve the duration of the study-session."""
        if self.state == "INACTIVE":
            raise StudySessionError("attempting to calculate the duration of an inactive study-session!")

        if self.state == "STOPPED":
            duration = self.stop_time - self.start_time
        else:   # RUNNING or PAUSED
            duration = datetime.datetime.now(self.timezone) - self.start_time
        return duration.total_seconds()

    def get_active_duration(self) -> float:
        """Retrieve the active duration of the study-session(excluding the cumulative pause duration)."""
        return self.get_duration() - self.get_cumulative_pause_duration()

    def get_pause_duration(self, idx: int) -> float:
        """Calculate the pause duration for a specific pause-resume pair of the study-session."""
        if self.state == "INACTIVE":
            raise StudySessionError("attempting to calculate the pause duration of an inactive study-session!")

        pause, resume = self._pause_resume_times[idx]
        if resume is None:
            if self.state == "PAUSED":
                resume = datetime.datetime.now(self.timezone)
            elif self.state == "STOPPED":
                resume = self.stop_time
        return (resume-pause).total_seconds()

    def get_cumulative_pause_duration(self) -> float:
        """Calculate the cumulative pause duration of the study-session."""
        if self.state == "INACTIVE":
            raise StudySessionError("attempting to calculate the cumulative pause duration "
                                    "of an inactive study-session!")

        if self.state == "PAUSED":
            cumulative_pause_duration = self._cached_cumulative_pause_duration + self.get_pause_duration(-1)
        else:   # RUNNING or STOPPED
            cumulative_pause_duration = self._cached_cumulative_pause_duration
        return cumulative_pause_duration

    # Static Methods (Public):

    @staticmethod
    def format_time(time_seconds: float) -> str:
        """Format time in seconds to 'hr:mm:sec.fraction' format."""
        hrs, remainder = divmod(time_seconds, 3600)
        mins, secs_with_fraction = divmod(remainder, 60)
        secs, fraction = divmod(secs_with_fraction, 1)
        return f"{int(hrs):02}:{int(mins):02}:{int(secs):02}.{int(fraction*10000):04}"


class StudySessionError(Exception):
    """Custom exception for StudySession related errors."""


class StudySessionNotFoundError(Exception):
    """Raised when the requested study-session is not found in the database."""
    def __init__(self, subject_name: str):
        Exception.__init__(self, f"study-session with subject name: {subject_name!r} not found in the database!")
