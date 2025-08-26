# Vercel Python entrypoint for Flask (WSGI)
# https://vercel.com/docs/functions/runtimes/python
from app import create_app

# Expose a WSGI application named `app`
app = create_app()
