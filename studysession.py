import datetime


from typing import Tuple


class StudySession:
    """
    Represents and manages a study session for a specific subject.

    Properties:
        - subject_name: Name of the subject for the study session. (str)
        - total_time: Total time for the subject in seconds. (int)
        - start_time: Timestamp when the study session started. (datetime.datetime or None)
        - stop_time: Timestamp when the study session stopped. (datetime.datetime or None)
        - pause_resume_times: Tuple of tuples containing pause and resume timestamps. Each inner tuple represents
          a pair of pause and resume times. If the session was paused but not resumed before stopping, the resume part
          of the tuple will be `None`. (Tuple[Tuple[datetime.datetime, datetime.datetime or None]])
        - state: Current state of the study session [e.g "RUNNING"/"PAUSED"/"INACTIVE"/"STOPPED"]. (str)

    Methods:
        - start_tracking(): Start tracking the study session duration.
        - stop_tracking(): Stop tracking the study session duration.
        - pause_tracking(): Pause tracking the study session duration.
        - resume_tracking(): Resume tracking the study session from a previously paused state.
        - discard_tracking(): Discard tracking the study session.
        - reset_tracking(): Reset tracking the study session data to its initial state.
        - get_duration(): Retrieve duration of the study session excluding the cumulative pause duration.
        - get_cumulative_pause_duration(): Calculate the cumulative pause duration during the study session.
        - format_time(time_seconds: int): Static method to format time in seconds to 'hr:mm:sec' format.

    Internal Attributes:
        - _subject_name: Internal storage for the subject name. (str)
        - _total_time: Internal storage for the total time. (int)
        - _start_time: Internal storage for the timestamp when the study session started, None if not started.
                       (datetime.datetime or None)
        - _stop_time: Internal storage for the timestamp when the study session stopped, None if not stopped.
                      (datetime.datetime or None)
        - _pause_resume_times: Internal storage for the list of tuples containing pause and resume timestamps.
                               (List[Tuple[datetime.datetime, datetime.datetime or None]])
        - _state: Internal storage for the current state of the session. (str)

    Internal Methods:
        - _determine_stop_time(): Determine the time the session was stopped.
        - _update_total_time(): Update the total time with session duration.
    """

    def __init__(self, subject_name: str, total_time: int = 0):
        """
        Initialize a StudySession object.

        Parameters:
            subject_name (str): The name of the subject for this study session.
            total_time (int, optional): The total time (in seconds) already spent on this subject. Defaults to 0.
        """
        self.subject_name = subject_name
        self.total_time = total_time
        # Internal attributes
        self._start_time = None
        self._stop_time = None
        self._pause_resume_times = []
        self._state = "INACTIVE"

    def __repr__(self) -> str:
        """Return a developer-friendly representation of the object."""
        return f"StudySession(subject_name={self.subject_name!r}, total_time={self.total_time})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the object."""
        return (f"StudySession for {self.subject_name!r} with the total time of "
                f"{StudySession.format_time(self.total_time)} and current state: {self.state}.")

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
    def total_time(self) -> int:
        """Property to get the total time."""
        return self._total_time

    @total_time.setter
    def total_time(self, val: int):
        """Setter for the total time."""
        if not isinstance(val, int):
            raise ValueError("Total time must be an integer.")
        if val < 0:
            raise ValueError("Total time cannot be negative.")
        self._total_time = val

    @property
    def start_time(self) -> datetime.datetime:
        """Get the start time of the session."""
        return self._start_time

    @property
    def stop_time(self) -> datetime.datetime:
        """Get the stop time of the session."""
        return self._stop_time

    @property
    def pause_resume_times(self) -> Tuple:
        """
        Retrieve all the pause and resume times as pairs.

        Note:
            This property returns the internal list of pause and resume times as a tuple of tuples.
            Each inner tuple represents a pair of pause and resume times. If the session was paused but
            not resumed before stopping, the resume part of the tuple will be `None`.
        """
        return tuple(self._pause_resume_times)

    @property
    def state(self):
        """Get the current state of the session."""
        return self._state

    # Core session interaction methods:
    def start_tracking(self) -> None:
        """Start tracking the study session duration."""
        if self.state == "RUNNING":
            raise StudySessionError("Session is already running.")
        elif self.state == "STOPPED":
            raise StudySessionError("Session hasn't been reset.")
        elif self.state == "PAUSED":
            raise StudySessionError("Cannot start a session that is currently paused.")
        self._start_time = datetime.datetime.now()
        self._state = "RUNNING"

    def stop_tracking(self) -> None:
        """Stop tracking the study session duration."""
        if self.state != "RUNNING" and self.state != "PAUSED":
            raise StudySessionError("Cannot stop a session that isn't currently running or paused.")
        self._determine_stop_time()
        self._state = "STOPPED"
        self._update_total_time()

    def pause_tracking(self):
        """Pause tracking the study session duration."""
        if self.state != "RUNNING":
            raise StudySessionError("Cannot pause a session that isn't currently running.")
        self._pause_resume_times.append((datetime.datetime.now(), None))
        self._state = "PAUSED"

    def resume_tracking(self):
        """Resume tracking the study session from a previously paused state."""
        if self.state != "PAUSED":
            raise StudySessionError("Cannot resume a session that isn't currently paused.")
        last_pause, _ = self._pause_resume_times[-1]
        self._pause_resume_times[-1] = (last_pause, datetime.datetime.now())
        self._state = "RUNNING"

    def discard_tracking(self) -> None:
        """Discard tracking the study session."""
        if self.state != "RUNNING" and self.state != "PAUSED":
            raise StudySessionError("Cannot discard a session that isn't currently running or paused.")
        self._start_time = None
        self._pause_resume_times.clear()
        self._state = "INACTIVE"

    def reset_tracking(self) -> None:
        """Reset tracking the study session data to its initial state."""
        if self.state != "STOPPED":
            raise StudySessionError("Cannot reset a session that hasn't been stopped.")
        self._start_time = None
        self._stop_time = None
        self._pause_resume_times.clear()
        self._state = "INACTIVE"

    def get_duration(self) -> int:
        """Retrieve duration of the study session excluding the cumulative pause duration."""
        if self.state == "STOPPED":
            duration = (self.stop_time - self.start_time).total_seconds()
        elif self.state == "RUNNING":
            duration = (datetime.datetime.now() - self.start_time).total_seconds()
        elif self.state == "PAUSED":
            duration = (self._pause_resume_times[-1][0] - self.start_time).total_seconds()
        else:
            raise StudySessionError("Study session hasn't started yet.")
        return int(duration - self.get_cumulative_pause_duration())

    def get_cumulative_pause_duration(self) -> int:
        """Calculate the cumulative pause duration during the study session."""
        if self.state == "INACTIVE":
            raise StudySessionError("Attempting to calculate the total pause duration for an inactive session.")
        cumulative_pause_duration = 0
        for pause, resume in self._pause_resume_times:
            if resume:
                cumulative_pause_duration = cumulative_pause_duration + ((resume - pause).total_seconds())
        return int(cumulative_pause_duration)

    def _determine_stop_time(self) -> None:
        """Determine the time the session was stopped."""
        if self.state == "RUNNING":
            self._stop_time = datetime.datetime.now()
        elif self.state == "PAUSED":
            self._stop_time = self._pause_resume_times[-1][0]  # Set end time to the last pause point

    def _update_total_time(self) -> None:
        """Update the total time with session duration."""
        self.total_time = self.total_time + self.get_duration()

    @staticmethod
    def format_time(time_seconds: int) -> str:
        """Static method to format time in seconds to 'hr:mm:sec' format."""
        hrs, remainder = divmod(time_seconds, 3600)
        mins, secs = divmod(remainder, 60)
        return f"{hrs:02}:{mins:02}:{secs:02}"


class StudySessionError(Exception):
    """Custom exception for StudySession related errors."""
