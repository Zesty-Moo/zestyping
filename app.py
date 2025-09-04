
import queue
from settings import Settings
from ui import MultiPingApp
from ping_worker import HostManager

def main():
    sample_queue = queue.Queue()
    settings = Settings.load()
    host_manager = HostManager(sample_queue=sample_queue)
    app = MultiPingApp(settings=settings, host_manager=host_manager, sample_queue=sample_queue)
    app.mainloop()

if __name__ == "__main__":
    main()
