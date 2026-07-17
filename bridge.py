import queue

# Log lines the voice engine wants printed in the GUI transcript
GUI_LOG_QUEUE = queue.Queue()

# Structured events the GUI reacts to (mode changes, login state, etc.)
GUI_COMMAND_QUEUE = queue.Queue()

# Typed text the GUI forwards to the voice engine when in typing mode
INPUT_QUEUE = queue.Queue()
