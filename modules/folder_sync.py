import os
import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MirrorHandler(FileSystemEventHandler):
    """
    This handler knows ITS specific source and destination.
    """
    def __init__(self, source_dir, dest_dir, callback=None):
        self.source_dir = os.path.abspath(source_dir)
        self.dest_dir = os.path.abspath(dest_dir)
        self.callback = callback  # Optional: Function called on events

    def _get_dest_path(self, src_path):
        relative_path = os.path.relpath(src_path, self.source_dir)
        return os.path.join(self.dest_dir, relative_path)

    def _log(self, message):
        # If a callback function exists, use it, otherwise print
        if self.callback:
            self.callback(message)
        else:
            print(f"[{self.source_dir} -> {self.dest_dir}] {message}")

    def on_created(self, event):
        dest = self._get_dest_path(event.src_path)
        try:
            if event.is_directory:
                os.makedirs(dest, exist_ok=True)
                self._log(f"Folder created: {dest}")
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(event.src_path, dest)
                self._log(f"File copied: {dest}")
        except Exception as e:
            self._log(f"Error (Create): {e}")

    def on_deleted(self, event):
        dest = self._get_dest_path(event.src_path)
        try:
            if os.path.exists(dest):
                if event.is_directory:
                    shutil.rmtree(dest)
                else:
                    os.remove(dest)
                self._log(f"Deleted: {dest}")
        except Exception as e:
            self._log(f"Error (Delete): {e}")

    def on_modified(self, event):
        if event.is_directory: return
        dest = self._get_dest_path(event.src_path)
        try:
            time.sleep(0.1) # Short buffer for write operations
            shutil.copy2(event.src_path, dest)
            self._log(f"Updated: {dest}")
        except Exception as e:
            self._log(f"Error (Modify): {e}")

    def on_moved(self, event):
        src = self._get_dest_path(event.src_path)
        dest = self._get_dest_path(event.dest_path)
        try:
            if os.path.exists(src):
                shutil.move(src, dest)
                self._log(f"Moved to: {dest}")
            else:
                if not event.is_directory:
                    shutil.copy2(event.dest_path, dest)
        except Exception as e:
            self._log(f"Error (Move): {e}")

class SingleFileHandler(FileSystemEventHandler):
    """
    This handler monitors a single file. It is set on the parent directory
    but only reacts to events concerning the specific source file.
    """
    def __init__(self, source_file, dest_file, callback=None):
        self.source_file = os.path.abspath(source_file)
        self.dest_file = os.path.abspath(dest_file)
        self.callback = callback

    def _log(self, message):
        if self.callback:
            self.callback(message)
        else:
            print(f"[{os.path.basename(self.source_file)} -> {os.path.basename(self.dest_file)}] {message}")

    def _sync_file(self, event_src_path):
        # Only react if the event concerns the source file
        if os.path.abspath(event_src_path) != self.source_file:
            return
        try:
            # Ensure the destination folder exists
            os.makedirs(os.path.dirname(self.dest_file), exist_ok=True)
            time.sleep(0.1) # Short buffer for write operations
            shutil.copy2(self.source_file, self.dest_file)
            self._log(f"Synchronized: {self.dest_file}")
        except FileNotFoundError:
            # If the source file is quickly deleted and recreated, this error can occur.
            # Usually not critical, as the subsequent "created" event catches up with the synchronization.
            pass
        except Exception as e:
            self._log(f"Error synchronizing: {e}")

    def on_created(self, event):
        if not event.is_directory:
            self._sync_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._sync_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and os.path.abspath(event.src_path) == self.source_file:
            if os.path.exists(self.dest_file):
                os.remove(self.dest_file)
                self._log(f"Destination file deleted: {self.dest_file}")

    def on_moved(self, event):
        # Handles renaming of the source file or if another file becomes the source file
        self.on_deleted(event) if os.path.abspath(event.src_path) == self.source_file else self.on_created(event)


class SyncManager:
    """
    The API class for controlling the monitoring.
    """
    def __init__(self):
        self.observer = Observer()
        self.watches = []

    def add_sync_pair(self, source, dest, verbose=True):
        """Adds a new folder pair for monitoring."""
        if not os.path.exists(source):
            raise FileNotFoundError(f"Source folder not found: {source}")
        
        # Initial sync: Copy all files from source to dest
        shutil.copytree(source, dest, dirs_exist_ok=True)
            
        # Optional: Define callback
        cb = print if verbose else None
        
        event_handler = MirrorHandler(source, dest, callback=cb)
        
        # The Watchdog Observer can manage multiple schedules
        watch = self.observer.schedule(event_handler, source, recursive=True)
        self.watches.append(watch)
        print(f"Sync registered: {source} >> {dest}")

    def add_single_file_sync(self, source_file, dest_file, verbose=True):
        """Adds a single file for monitoring."""
        source_file_abs = os.path.abspath(source_file)
        source_dir = os.path.dirname(source_file_abs)

        if not os.path.isdir(source_dir):
            raise NotADirectoryError(f"The parent directory of the source file does not exist: {source_dir}")

        # Perform an initial synchronization if the file already exists
        if os.path.exists(source_file_abs):
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(source_file_abs, dest_file)

        cb = print if verbose else None
        event_handler = SingleFileHandler(source_file_abs, dest_file, callback=cb)

        # Monitor the directory where the file is located (non-recursive is sufficient)
        watch = self.observer.schedule(event_handler, source_dir, recursive=False)
        self.watches.append(watch)
        print(f"File sync registered: {source_file} >> {dest_file}")

    def start(self):
        """Starts the background process."""
        if not self.observer.is_alive():
            self.observer.start()
            print("Sync Manager started.")

    def stop(self):
        """Stops all monitoring cleanly."""
        self.observer.stop()
        self.observer.join()
        print("Sync Manager stopped.")
