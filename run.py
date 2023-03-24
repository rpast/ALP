import os
import webbrowser
from threading import Timer

def open_browser():
    """Open default browser to display the app."""
    webbrowser.open_new('http://127.0.0.1:8000/')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    os.system('gunicorn --workers 4 --bind 0.0.0.0:8000 wsgi:app')
