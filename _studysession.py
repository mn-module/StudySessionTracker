import os

from studysession import StudySession as ParentStudySession
from studysession import StudySessionError, StudySessionNotFoundError
from totaltimedbhandler import TotalTimeDBHandler


class _StudySession(ParentStudySession):
    """
    This private class is just a demo of how you can use the 'StudySession' class with 'TotalTimeDBHandler'
    to persist the data. The real reason I wrote it like this because I didn't want to
    create a GUI app or CLI app. That's too boring, and honestly, those apps won't be easy
    to use on my iPad Pro. But this current style? This is how I use it on my iPad Pro to
    track my study progress. So easy and simple! Give it a try! ;)
    """

    @ParentStudySession.subject_name.setter
    def subject_name(self, name: str) -> None:
        """Return the subject_name."""
        if not isinstance(name, str):
            raise TypeError(f"excepted type: 'str', got {type(name).__name__!r} instead!")

        if "," in name:    # the comma is forbidden here
            raise ValueError("found comma in the subject_name, "
                             "note: the comma is forbidden here because of csv logging functionality!")

        self._subject_name = name

    def __repr__(self):
        return f"_{ParentStudySession.__repr__(self)}"

    def save_to_db(self, db_handler: TotalTimeDBHandler) -> None:
        """
        If the study-session subject name has a corresponding record in the database, the total time associated
        with it is incremented by the new value. Otherwise, a new record is created.
        """
        # Check study-session state before saving
        if self.state != "STOPPED":
            raise StudySessionError("this study-session must be stopped before saving data to the database!")

        if db_handler.is_record_present(self.subject_name):  # Record already exists, update the record
            db_handler.increment_record_total_time(self.subject_name, self.get_active_duration())
        else:   # Record doesn't already exist, create a new record
            db_handler.add_record(self.subject_name, self.get_active_duration())

    def log_to_csv(self, csv_folder_path: str) -> None:
        """
        Log the study-session subject name, start time, stop time, duration, cumulative pause duration
        and active duration data to the csv file.
         """
        # Note: this method only allows csv folder path because the file name is dynamically generated
        # based on study-session start time

        # Check study-session state before saving
        if self.state != "STOPPED":
            raise StudySessionError("this study-session must be stopped before saving data to the csv file!")

        # Check and create the csv folder path if it doesn't exist
        if not os.path.exists(csv_folder_path):
            os.makedirs(csv_folder_path)
        # Generate csv path based on study-session start time
        csv_path = os.path.join(csv_folder_path, f"{self.start_time.strftime('%Y-%m')}.csv")
        # Create a new csv file and write header if csv file is missing or is empty
        if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
            with open(csv_path, "w") as file:
                file.write("subject name,start time,stop time,timezone,duration,cumulative pause duration,"
                           "active duration\n")
        # Writing Data to csv
        with open(csv_path, "a") as file:
            fmt_study_session_duration = _StudySession.format_time(self.get_duration())
            fmt_study_session_cumulative_pause_duration = _StudySession.format_time(
                self.get_cumulative_pause_duration())
            fmt_study_session_active_duration = _StudySession.format_time(self.get_active_duration())
            file.write(f"{self.subject_name},"
                       f"{self.start_time.strftime('%A %I:%M:%S %p')},"
                       f"{self.stop_time.strftime('%A %I:%M:%S %p')},"
                       f"{self.timezone.zone},"
                       f"{fmt_study_session_duration},"
                       f"{fmt_study_session_cumulative_pause_duration},"
                       f"{fmt_study_session_active_duration}\n")

    def delete_from_db(self, db_handler: TotalTimeDBHandler) -> None:
        """
        Delete a record from the database if the study-session subject name corresponds to a record in the database.
        Otherwise, raise a StudySessionNotFoundError.
        """
        if db_handler.is_record_present(self.subject_name):
            db_handler.delete_record(self.subject_name)
        else:
            raise StudySessionNotFoundError(self.subject_name)
