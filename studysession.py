import datetime
from typing import Tuple


class StudySession:
    """
    Represents and manages a study-session for a specific subject.

    Properties:
        - subject_name: Name of the subject for the study-session. (str)
        - start_time: Timestamp when the study-session started. (datetime.datetime or None)
        - stop_time: Timestamp when the study-session stopped. (datetime.datetime or None)
        - pause_resume_times: A tuple containing multiple tuples, where each inner tuple represents a pair of pause
          and resume timestamps. If the study-session was paused but not resumed before stopping, the resume part of
          the tuple will be `None`. (Tuple[Tuple[datetime.datetime, datetime.datetime or None]])
        - state: Current state of the study-session. (str)
          Valid states and their meanings are:
              - "RUNNING": The study-session is currently active and tracking time.
              - "PAUSED": The study-session has been temporarily paused and is not tracking time.
              - "INACTIVE": The study-session has not been started yet.
              - "STOPPED": The study-session has been stopped, and the time has been recorded. It needs to be reset
                 before starting again.


    Internal Attributes:
        - _subject_name: Internal storage for the subject name. (str)
        - _start_time: Internal storage for the timestamp when the study-session started, None if not started.
          (datetime.datetime or None)
        - _stop_time: Internal storage for the timestamp when the study-session stopped, None if not stopped.
          (datetime.datetime or None)
        - _pause_resume_times: Internal storage for a list containing multiple tuples, where each inner tuple represents
          a pair of pause and resume timestamps. (List[Tuple[datetime.datetime, datetime.datetime or None]])
        - _state: Internal storage for the current state of the study-session. (str)

    Instance Methods:
        - start_tracking(self) -> None: Start tracking the study-session duration.
        - stop_tracking(self) -> None: Stop tracking the study-session duration.
        - pause_tracking(self) -> None: Pause tracking the study-session duration.
        - resume_tracking(self) -> None: Resume tracking the study-session from a previously paused state.
        - discard_tracking(self) -> None: Discard tracking the study-session.
        - reset_tracking(self) -> None: Reset tracking the study-session data to its initial state,
          excluding the 'total_time'.
        - get_duration(self) -> int: Retrieve the duration of the study-session.
        - get_active_duration(self) -> int: Retrieve the active duration of the study-session(excluding the
          cumulative pause duration).
        - get_cumulative_pause_duration(self) -> int: Calculate the cumulative pause duration during the study-session.

    Internal Instance Methods:
        - _determine_stop_time(self) -> None: Determine the time the study-session was stopped.

    Static Method:
        - format_time(time_seconds: int) -> str: Format time in seconds to 'hr:mm:sec' format.
    """
    # Initialization and representation methods:
    def __init__(self, subject_name: str):
        """Initialize a StudySession object."""
        self.subject_name = subject_name
        # Internal attributes
        self._start_time = None
        self._stop_time = None
        self._pause_resume_times = []
        self._state = "INACTIVE"

    def __repr__(self) -> str:
        """Return a developer-friendly representation of the object."""
        return f"StudySession(subject_name={self.subject_name!r})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the object."""
        return f"StudySession for {self.subject_name!r} and current state: {self.state}."

    # Properties:
    @property
    def subject_name(self) -> str:
        """Property to get the subject name."""
        return self._subject_name

    @subject_name.setter
    def subject_name(self, name: str) -> None:
        """Setter for the subject name."""
        if not isinstance(name, str):
            raise ValueError("Subject name must be a string.")
        self._subject_name = name

    @property
    def start_time(self) -> datetime.datetime:
        """Get the start time of the study-session."""
        return self._start_time

    @property
    def stop_time(self) -> datetime.datetime:
        """Get the stop time of the study-session."""
        return self._stop_time

    @property
    def pause_resume_times(self) -> Tuple:
        """Retrieve all the pause and resume times as pairs."""
        return tuple(self._pause_resume_times)

    @property
    def state(self):
        """Get the current state of the study-session."""
        return self._state

    # Core study-session interaction methods:
    # Instance Methods:
    def start_tracking(self) -> None:
        """Start tracking the study-session duration."""
        if self.state == "RUNNING":
            raise StudySessionError("Study-session is already running.")
        elif self.state == "STOPPED":
            raise StudySessionError("Study-session hasn't been reset.")
        elif self.state == "PAUSED":
            raise StudySessionError("Cannot start a study-session that is currently paused.")
        self._start_time = datetime.datetime.now()
        self._state = "RUNNING"

    def stop_tracking(self) -> None:
        """Stop tracking the study-session duration."""
        if self.state != "RUNNING" and self.state != "PAUSED":
            raise StudySessionError("Cannot stop a study-session that isn't currently running or paused.")
        self._determine_stop_time()
        self._state = "STOPPED"

    def pause_tracking(self):
        """Pause tracking the study-session duration."""
        if self.state != "RUNNING":
            raise StudySessionError("Cannot pause a study-session that isn't currently running.")
        self._pause_resume_times.append((datetime.datetime.now(), None))
        self._state = "PAUSED"

    def resume_tracking(self):
        """Resume tracking the study-session from a previously paused state."""
        if self.state != "PAUSED":
            raise StudySessionError("Cannot resume a study-session that isn't currently paused.")
        last_pause, _ = self._pause_resume_times[-1]
        self._pause_resume_times[-1] = (last_pause, datetime.datetime.now())
        self._state = "RUNNING"

    def discard_tracking(self) -> None:
        """Discard tracking the study-session."""
        if self.state != "RUNNING" and self.state != "PAUSED":
            raise StudySessionError("Cannot discard a study-session that isn't currently running or paused.")
        self._start_time = None
        self._pause_resume_times.clear()
        self._state = "INACTIVE"

    def reset_tracking(self) -> None:
        """Reset tracking the study-session data to its initial state, excluding the 'total_time'."""
        if self.state != "STOPPED":
            raise StudySessionError("Cannot reset a study-session that hasn't been stopped.")
        self._start_time = None
        self._stop_time = None
        self._pause_resume_times.clear()
        self._state = "INACTIVE"

    def get_duration(self) -> int:
        """Retrieve the duration of the study-session."""
        if self.state == "STOPPED":
            duration = (self.stop_time - self.start_time).total_seconds()
        elif self.state == "RUNNING":
            duration = (datetime.datetime.now() - self.start_time).total_seconds()
        elif self.state == "PAUSED":
            duration = (self._pause_resume_times[-1][0] - self.start_time).total_seconds()
        else:
            raise StudySessionError("Study-session hasn't started yet.")
        return int(duration)

    def get_active_duration(self) -> int:
        """Retrieve the active duration of the study-session(excluding the cumulative pause duration)."""
        return self.get_duration() - self.get_cumulative_pause_duration()

    def get_cumulative_pause_duration(self) -> int:
        """Calculate the cumulative pause duration during the study-session."""
        if self.state == "INACTIVE":
            raise StudySessionError("Attempting to calculate the total pause duration for an inactive study-session.")
        cumulative_pause_duration = 0
        for pause, resume in self._pause_resume_times:
            if resume:
                cumulative_pause_duration = cumulative_pause_duration + ((resume - pause).total_seconds())
        return int(cumulative_pause_duration)

    # Internal Instance Methods:
    def _determine_stop_time(self) -> None:
        """Determine the time the study-session was stopped."""
        if self.state == "RUNNING":
            self._stop_time = datetime.datetime.now()
        elif self.state == "PAUSED":
            self._stop_time = self._pause_resume_times[-1][0]  # Set end time to the last pause point

    # Static Method:
    @staticmethod
    def format_time(time_seconds: int) -> str:
        """Format time in seconds to 'hr:mm:sec' format."""
        hrs, remainder = divmod(time_seconds, 3600)
        mins, secs = divmod(remainder, 60)
        return f"{hrs:02}:{mins:02}:{secs:02}"


class StudySessionError(Exception):
    """Custom exception for StudySession related errors."""
