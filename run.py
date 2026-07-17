import threading

import voice_email_system
from gui import launch_gui


def start_voice_engine():
    voice_email_system.main()


if __name__ == "__main__":
    engine_thread = threading.Thread(target=start_voice_engine, daemon=True)
    engine_thread.start()

    launch_gui()


