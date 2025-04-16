import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        print(f"File created: {event.src_path}")

if __name__ == "__main__":
    path = r"K:\\Documents\\icecrawl\\.Augmentorium"
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print(f"Watching {path} for new files...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
