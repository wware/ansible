import os
from flask import Flask
from werkzeug import serving

app = Flask(__name__)

@app.route("/")
def hello():
  return "Hello World! This is Flask ({0}).\n".format(os.environ.get("KEY"))

serving.run_simple("0.0.0.0", 5000, app)
