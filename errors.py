import json
from urllib.request import urlopen
import functools
import logging

def log_error(func):
    def no_error(*args, **kwargs):
        try:
            return func(*args, ** kwargs)
        except Exception as e:
            logging.error(str(e))
            return None
    return no_error


def slack(text: str, webhookAddress: str) -> str:
    """Send a slack message slack message"""

    data = bytes(json.dumps({"text": text}), "utf-8")
    handler = urlopen(webhookAddress, data)
    return handler.read().decode('utf-8')


def slack_error(func):
    """
    A decorator that wraps the passed in function and sends a slack message of the exceptions if one occurs
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except Exception as e:
            slack(f"There was an exception in `{func.__name__}`: {e}", YOUR_WEBHOOK)
            raise

    return wrapper
