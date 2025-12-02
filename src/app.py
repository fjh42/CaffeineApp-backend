import json
from flask import Flask, request
import datetime
import db

DB = db.DatabaseDriver()

app = Flask(__name__)

def success_response(data,status_code=200):
    """
    Standardized success response
    """
    return json.dumps(data), status_code

def failure_response(description,status_code=500):
    """
    Standardized failure response
    """
    return json.dumps({"error":description}),status_code

@app.before_first_request
def initialize_database():
    """
    Initialize the database by creating the necessary tables.
    """
    pass

@app.route("/")
def hello_world():
    return "Hello world!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)