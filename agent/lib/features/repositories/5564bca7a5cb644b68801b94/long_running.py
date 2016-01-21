import os
import time

log_message("second process log", "info")

"""This call is here to test stopping a running script"""
while True:
    print(str(os.getpid()) + "-Long_running.py: Hello from the long running BPM Process")
    """Sleep is here to reduce cpu usage"""
    time.sleep(0.1)
