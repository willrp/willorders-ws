from setuptools import setup

setup(
   name="willorders-ws",
   version="0.0.1",
   description="Willorders Web service for WillBuyer demonstration platform.",
   license="MIT",
   author="Will Roger Pereira",
   author_email="willrogerpereira@hotmail.com",
   url="https://github.com/willrp/willorders-ws",
   install_requires=[
       "Flask",
       "flask-restplus",
       "marshmallow",
       "psycopg2",
       "python-dotenv",
       "requests",
       "SQLAlchemy",
       "Werkzeug"
   ],
)
