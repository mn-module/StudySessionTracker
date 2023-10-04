import os
import sqlite3
from collections.abc import Iterator
from typing import List, Tuple, Iterable


class TotalTimeDBHandler:
    """
    A database handler for tracking total study time for each subject.

    Manages CRUD operations on a SQLite database where each subject's name is used as a primary key
    to track its total study duration. Supports optional explicit transaction commits after key operations.
    """
    # Initialization and representation methods:
    def __init__(self, db_folder_path: str, db_file_name: str, *, auto_explicit_commit_flag=True):
        """
        Initialize the database handler with the provided folder path and file name.

        Parameters:
        - db_folder_path (str): The path to the folder where the database file will be stored.
        - db_file_name (str): The name of the database file.
        - auto_explicit_commit_flag (bool, optional): If set to True, certain instance methods will
          explicitly commit transactions after executing their database operations. This behavior
          applies only to the instance methods and not the underlying SQLite3 connection. The
          affected methods are: add_record, add_records, change_record_subject_name,
          set_record_total_time, increment_record_total_time, remove_record, remove_records, and
          clear_all. By default, it is set to True.
        """
        # validation for db_folder_path and db_file_name
        if not isinstance(db_folder_path, str):
            raise TypeError(f"Excepted Type: 'str' for db_folder_path"
                            f", but got {type(db_folder_path).__name__!r} instead!")
        if not isinstance(db_file_name, str):
            raise TypeError(f"Excepted Type: 'str' for db_file_name"
                            f", but got {type(db_file_name).__name__!r} instead!")

        self._db_folder_path = db_folder_path
        self._db_file_name = db_file_name
        self._conn = None
        self.auto_explicit_commit_flag = auto_explicit_commit_flag
        # setting up the database connection
        self.init_db()

    def __repr__(self):
        """Return a representative string."""
        return (f"TotalTimeDBHandler(db_folder_path={self.db_folder_path!r}, "
                f"db_file_name={self.db_file_name!r}, auto_commit_flag={self.auto_explicit_commit_flag!r})")

    def __str__(self):
        """Return a readable string representation."""
        return f"Total-Time Database Handler: {self.get_db_path()}"

    # Properties:
    @property
    def db_folder_path(self) -> str:
        """Get the database folder path."""
        return self._db_folder_path

    @property
    def db_file_name(self) -> str:
        """Get the database file name."""
        return self._db_file_name

    @property
    def auto_explicit_commit_flag(self) -> bool:
        """Get the flag status for auto explicit commit."""
        return self._auto_explicit_commit_flag

    @auto_explicit_commit_flag.setter
    def auto_explicit_commit_flag(self, val: bool) -> None:
        """Set the flag status for auto explicit commit."""
        if not isinstance(val, bool):
            raise TypeError(f"Expected Type: 'bool' for auto_explicit_commit_flag"
                            f", but got {type(val).__name__!r} instead!")
        self._auto_explicit_commit_flag = val

    # Database setup and configuration:
    def _ensure_db_folder_exists(self) -> None:
        """Ensure that the database folder exists."""
        if not os.path.exists(self.db_folder_path):
            os.makedirs(self.db_folder_path)

    def get_db_path(self) -> str:
        """Get the full database path."""
        return os.path.join(self.db_folder_path, self.db_file_name)

    def init_db(self) -> None:
        """
        Set up the database by ensuring the required table exists.

        This method can be used to re-open a closed database connection. If the database folder or the
        'records' table does not exist, this method will create them.
        """
        # When this method is used to re-open the database connection, it first closes the existing connection
        # to ensure the database file doesn't remain locked.
        if self._conn is not None:  # Checking it is initial run or not. because _conn is set to None in initial run
            self.close_conn()
        self._ensure_db_folder_exists()
        self._conn = sqlite3.connect(self.get_db_path())
        cur = self._conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS records (
            subject_name TEXT PRIMARY KEY,
            subject_total_time REAL NOT NULL
        )
        """)
        self.commit_conn()

    def _auto_explicit_commit_fn(self) -> None:
        """Automatically commit if the flag is set."""
        if self.auto_explicit_commit_flag:
            self.commit_conn()

    def commit_conn(self) -> None:
        """Commit the current transaction."""
        self._conn.commit()

    def rollback_conn(self) -> None:
        """Rollback any changes made since the last commit."""
        self._conn.rollback()

    def reset_conn(self) -> None:
        """Reset the database connection. Can be used to re-open a closed database connection."""
        # Explicitly closing existing database connection to prevent the database file from getting locked
        self._conn.close()
        self._conn = sqlite3.connect(self.get_db_path())

    def close_conn(self) -> None:
        """Close the database connection."""
        self._conn.close()

    # Context manager methods:
    def __enter__(self):
        """Support for with statement entry."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Handle the database connection cleanup on exiting a 'with' block.

        The behavior is as follows:
        - If no exceptions occurred within the 'with' block, commit any pending changes to the database.
        - If an exception did occur:
            - If 'auto_explicit_commit_flag' is set to True, commit the changes to ensure data persistence even in
              the face of errors. This means that operations like 'add_records' will be saved even if an error
              occurs partway through a series of operations.
            - If 'auto_explicit_commit_flag' is set to False, rollback any changes made within the 'with' block
              to revert the database to its state before entering the block.
        - Finally, close the database connection.
        """
        if exc_type is None:
            self.commit_conn()
        else:   # exception occurred
            if self.auto_explicit_commit_flag:
                self.commit_conn()
            else:
                self.rollback_conn()
        self.close_conn()

    # Core database interaction methods:
    def add_record(self, subject_name: str, total_time: float = 0) -> None:
        """Add a single new record to the database."""
        cur = self._conn.cursor()
        cur.execute("INSERT INTO records (subject_name, subject_total_time) VALUES (?, ?)",
                    (subject_name, total_time))
        self._auto_explicit_commit_fn()

    def add_records(self, subjects_data: Iterable[Tuple[str, float]]) -> None:
        """Add multiple new records to the database."""
        cur = self._conn.cursor()
        cur.executemany("INSERT INTO records (subject_name, subject_total_time) VALUES (?, ?)", subjects_data)
        self._auto_explicit_commit_fn()

    def change_record_subject_name(self, old_subject_name: str, new_subject_name: str) -> None:
        """Change the subject name of a record in the database."""
        cur = self._conn.cursor()
        cur.execute("UPDATE records SET subject_name = ? WHERE subject_name = ?",
                    (new_subject_name, old_subject_name))
        self._auto_explicit_commit_fn()

    def set_record_total_time(self, subject_name: str, total_time: float) -> None:
        """Set the total time of a record in the database."""
        cur = self._conn.cursor()
        cur.execute("UPDATE records SET subject_total_time = ? WHERE subject_name = ?", (total_time, subject_name))
        self._auto_explicit_commit_fn()

    def increment_record_total_time(self, subject_name: str, increment_value: float) -> None:
        """Increment the total time of a record in the database by a given value."""
        cur = self._conn.cursor()
        cur.execute(
            "UPDATE records SET subject_total_time = subject_total_time + ? WHERE subject_name = ?",
            (increment_value, subject_name)
        )
        self._auto_explicit_commit_fn()

    def is_record_present(self, subject_name: str) -> bool:
        """Check if a record is present in the database."""
        cur = self._conn.cursor()
        cur.execute("SELECT subject_name FROM records WHERE subject_name = ?", (subject_name,))
        return cur.fetchone() is not None

    def get_record(self, subject_name: str) -> Tuple[str, float]:
        """Retrieve the record from the database."""
        cur = self._conn.cursor()
        cur.execute("SELECT subject_name, subject_total_time FROM records WHERE subject_name = ?", (subject_name,))
        return cur.fetchone()

    def get_records(self, subject_names: Iterable[str]) -> List[Tuple[str, float]]:
        """Retrieve the records from the database."""
        cur = self._conn.cursor()
        # If subject_names is an iterator, convert it to a tuple
        if isinstance(subject_names, Iterator):
            subject_names = tuple(subject_names)
        cur.execute("SELECT subject_name, subject_total_time FROM records"
                    f" WHERE subject_name IN ({','.join('?' for _ in subject_names)})", subject_names)
        return cur.fetchall()

    def get_all_records(self) -> List[Tuple[str, float]]:
        """Retrieve all records from the database."""
        cur = self._conn.cursor()
        cur.execute("SELECT subject_name, subject_total_time FROM records")
        return cur.fetchall()

    def delete_record(self, subject_name: str) -> None:
        """Delete a single record from the database using provided a subject name."""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM records WHERE subject_name = ?", (subject_name,))
        self._auto_explicit_commit_fn()

    def delete_records(self, subject_names: Iterable[str]) -> None:
        """Delete multiple records from the database using provided subject names."""
        cur = self._conn.cursor()
        cur.executemany(f"DELETE FROM records WHERE subject_name = ?",
                        ((subject_name, ) for subject_name in subject_names))
        self._auto_explicit_commit_fn()

    def delete_all_records(self) -> None:
        """Delete all records from the database."""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM records")
        self._auto_explicit_commit_fn()

    def __del__(self):
        """Destructor to close the database connection."""
        if hasattr(self, '_conn'):
            self._conn.close()
