import time


def print_log(message: str):
    """
    Print log message with timestamp to screen and file.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    output = f"[{timestamp}] {message}"
    print(output)
    with open("output\\logs.txt", "a", encoding="utf-8") as log_file:
        log_file.write(output + "\n")
