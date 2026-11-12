"""WSGI entry point for gunicorn:  gunicorn wsgi:app"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Local development only. In the container gunicorn serves the app.
    app.run(host="0.0.0.0", port=8000)
