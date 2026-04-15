import csv
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class KnowledgeScanner:
    """
    Scans a local directory for .md, .txt, and .csv files and keeps the history database in sync.
    """

    SUPPORTED_EXTENSIONS = {".md", ".txt", ".csv"}

    def __init__(self, history_mgr):
        self.history_mgr = history_mgr

    def scan_directory(self, target_dir: str):
        """
        Crawls the target directory and syncs files to the database.
        """
        if not target_dir or not os.path.exists(target_dir):
            logger.warning(f"KnowledgeScanner: Skip scan. Directory does not exist: {target_dir}")
            return

        logger.info(f"KnowledgeScanner: Starting scan of {target_dir}")
        Path(target_dir)

        # Get current documents in DB to track deletions/updates
        # Note: We need a way to filter only documents from DB.
        # meetings = self.history_mgr.get_meetings_filtered(source_type="document")
        # For now, we list all and filter.
        all_records = self.history_mgr.get_all_meetings()
        db_docs = {r["file_path"]: r for r in all_records if r.get("source_type") == "document"}

        found_paths = set()

        for root, _, files in os.walk(target_dir):
            for file in files:
                file_path = os.path.join(root, file)
                abs_path = os.path.abspath(file_path)
                ext = os.path.splitext(file)[1].lower()

                if ext in self.SUPPORTED_EXTENSIONS:
                    found_paths.add(abs_path)
                    try:
                        os.path.getmtime(abs_path)
                        # TODO: Store mtime in DB to avoid unnecessary re-parsing.
                        # For now, we compare if the file exists in DB.

                        if abs_path not in db_docs:
                            self._process_file(abs_path, ext)
                        else:
                            # Simple update check: if we decide to store mtime, we'd check it here.
                            pass
                    except Exception as e:
                        logger.error(f"Failed to process file {abs_path}: {e}")

        # Optional: Handle deletions (files in DB but not on disk)
        # for path, record in db_docs.items():
        #     if path not in found_paths:
        #         self.history_mgr.delete_meeting(record["id"])

        logger.info("KnowledgeScanner: Scan complete.")

    def _process_file(self, file_path: str, ext: str):
        """Parses a single file and adds it to the history manager."""
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                if ext == ".csv":
                    reader = csv.reader(f)
                    content = "\n".join([", ".join(row) for row in reader])
                else:
                    content = f.read()

            title = os.path.basename(file_path)
            # Use file modified time as the timestamp
            from datetime import datetime

            datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S")

            # Determine project based on parent folder name if it's deeper than root
            # Or just default to 'Documents'
            project_name = "Knowledge Library"

            self.history_mgr.add_meeting(
                title=title,
                transcript=content,
                audio_path="",
                project_name=project_name,
                category=ext.upper()[1:],  # MD, TXT, CSV
                source_type="document",
                file_path=file_path,
            )
            logger.info(f"KnowledgeScanner: Indexed {title}")

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
