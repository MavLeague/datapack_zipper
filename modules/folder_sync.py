import os
import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class MirrorHandler(FileSystemEventHandler):
    """
    Dieser Handler kennt SEINE spezifische Quelle und SEIN Ziel.
    """
    def __init__(self, source_dir, dest_dir, callback=None):
        self.source_dir = os.path.abspath(source_dir)
        self.dest_dir = os.path.abspath(dest_dir)
        self.callback = callback  # Optional: Funktion, die bei Events aufgerufen wird

    def _get_dest_path(self, src_path):
        relative_path = os.path.relpath(src_path, self.source_dir)
        return os.path.join(self.dest_dir, relative_path)

    def _log(self, message):
        # Wenn eine Callback-Funktion existiert, diese nutzen, sonst print
        if self.callback:
            self.callback(message)
        else:
            print(f"[{self.source_dir} -> {self.dest_dir}] {message}")

    def on_created(self, event):
        dest = self._get_dest_path(event.src_path)
        try:
            if event.is_directory:
                os.makedirs(dest, exist_ok=True)
                self._log(f"Ordner erstellt: {dest}")
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(event.src_path, dest)
                self._log(f"Datei kopiert: {dest}")
        except Exception as e:
            self._log(f"Fehler (Create): {e}")

    def on_deleted(self, event):
        dest = self._get_dest_path(event.src_path)
        try:
            if os.path.exists(dest):
                if event.is_directory:
                    shutil.rmtree(dest)
                else:
                    os.remove(dest)
                self._log(f"Gelöscht: {dest}")
        except Exception as e:
            self._log(f"Fehler (Delete): {e}")

    def on_modified(self, event):
        if event.is_directory: return
        dest = self._get_dest_path(event.src_path)
        try:
            time.sleep(0.1) # Kurzer Puffer für Schreibvorgänge
            shutil.copy2(event.src_path, dest)
            self._log(f"Aktualisiert: {dest}")
        except Exception as e:
            self._log(f"Fehler (Modify): {e}")

    def on_moved(self, event):
        src = self._get_dest_path(event.src_path)
        dest = self._get_dest_path(event.dest_path)
        try:
            if os.path.exists(src):
                shutil.move(src, dest)
                self._log(f"Verschoben nach: {dest}")
            else:
                if not event.is_directory:
                    shutil.copy2(event.dest_path, dest)
        except Exception as e:
            self._log(f"Fehler (Move): {e}")


class SyncManager:
    """
    Die API-Klasse zur Steuerung der Überwachung.
    """
    def __init__(self):
        self.observer = Observer()
        self.watches = []

    def add_sync_pair(self, source, dest, verbose=True):
        """Fügt ein neues Ordner-Paar zur Überwachung hinzu."""
        if not os.path.exists(source):
            raise FileNotFoundError(f"Quellordner nicht gefunden: {source}")
        if not os.path.exists(dest):
            os.makedirs(dest)
            
        # Optional: Callback definieren
        cb = print if verbose else None
        
        event_handler = MirrorHandler(source, dest, callback=cb)
        
        # Der Observer von Watchdog kann mehrere Schedules verwalten
        watch = self.observer.schedule(event_handler, source, recursive=True)
        self.watches.append(watch)
        print(f"Sync registriert: {source} >> {dest}")

    def start(self):
        """Startet den Hintergrundprozess."""
        if not self.observer.is_alive():
            self.observer.start()
            print("Sync-Manager gestartet.")

    def stop(self):
        """Stoppt alle Überwachungen sauber."""
        self.observer.stop()
        self.observer.join()
        print("Sync-Manager gestoppt.")
