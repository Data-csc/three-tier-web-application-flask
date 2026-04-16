from flask import Flask, make_response, request, jsonify, after_this_request, render_template, redirect, g
from flask_sqlalchemy import SQLAlchemy
from parameters import master_username, db_password, endpoint, db_instance_name
import requests, json
import uuid
import logging
from logging_config import configure_logging

app = Flask(__name__)
configure_logging(app)
logger = logging.getLogger(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{master_username}:{db_password}@{endpoint}/{db_instance_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class TodoTable(db.Model):
    __tablename__ = "todotable"
 
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(100))
 
    def __init__(self, task):
        self.task = task
 
    def __repr__(self):
        return f"{self.id}:{self.task}"

with app.app_context():
    db.create_all()

@app.before_request
def set_request_id():
    g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

@app.after_request
def add_request_id_header(response):
    response.headers['X-Request-ID'] = g.request_id
    return response

def create_object(results):
    return {result.id: result.task for result in results}

@app.route('/', methods=['GET'])
def display():
    logger.info("Display route entry")
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    todos = TodoTable.query.all()
    logger.info("Display route completed", extra={'todo_count': len(todos)})
    return jsonify(create_object(todos))

@app.route("/create", methods =['POST'])
def create():
    logger.info("Create route entry")
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    try:
        if request.method == "POST":
            task_text = request.form.get("task")
            todo = TodoTable(task=task_text)
            db.session.add(todo)
            db.session.commit()
            logger.info("Create route completed", extra={'task': task_text})
            return redirect("/", 302)
    except:
        logger.error("Create route failed", exc_info=True)
        return redirect("/", 404)

@app.route("/update", methods =['POST'])
def update():
    logger.info("Update route entry")
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    try:
        if request.method == "POST":
            task_id = request.form.get("task_id")
            todo = TodoTable.query.get(task_id)
            todo.task = request.form.get("task")

            db.session.commit()
            logger.info("Update route completed", extra={'task_id': task_id})
            return redirect("/", 302)
    except:
        logger.error("Update route failed", exc_info=True)
        return redirect("/", 404)

@app.route("/complete/<task_id>", methods=["POST"])
def complete(task_id):
    logger.info("Complete route entry", extra={'task_id': task_id})
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    try:
        todo = TodoTable.query.get(task_id)
        db.session.delete(todo)
        db.session.commit()
        logger.info("Complete route completed", extra={'task_id': task_id})
        return redirect("/", 302)
    except:
        logger.error("Complete route failed", exc_info=True)
        return redirect("/", 404)
    

@app.route('/health')
def index():
    return make_response("Successful health check for ALB!", 200)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000, debug=False)