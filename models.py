# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='worker') # 'owner' or 'worker'
    tasks = db.relationship('Task', backref='assignee', lazy=True)
    reported_issues = db.relationship('ToolIssue', backref='reporter', lazy=True)
    job_requests = db.relationship('JobRequest', backref='requester', lazy=True) # Requester of the job request


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Available') # Available, In-Use, Maintenance
    last_maintenance = db.Column(db.DateTime, nullable=True)
    tasks = db.relationship('Task', backref='tool', lazy=True)
    issues = db.relationship('ToolIssue', backref='tool_affected', lazy=True)
    # MODIFIED: Changed backref from 'requested_tool' to 'tool'
    job_requests = db.relationship('JobRequest', backref='tool', lazy=True)

    def __repr__(self):
        return f"Tool('{self.name}', '{self.status}')"

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), nullable=False, default='Medium') # Low, Medium, High
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, In-Progress, Completed
    assigned_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime, nullable=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id'), nullable=True) # Task might not require a specific tool

    def __repr__(self):
        return f"Task('{self.title}', '{self.status}', 'Assigned to: {self.assignee.username if self.assignee else 'N/A'}')"

class ToolIssue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reported_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Reported') # Reported, Under Review, Resolved
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id'), nullable=False)

    def __repr__(self):
        return f"ToolIssue('{self.title}', 'Tool: {self.tool_affected.name if self.tool_affected else 'N/A'}', 'Status: {self.status}')"

class JobRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requested_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Approved, Declined
    # This `worker_id` seems off if the JobRequest is made *by* a user.
    # It should probably be `requester_id` as defined in User.job_requests
    worker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Consider renaming to requester_id for clarity
    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id'), nullable=True) # Optional: request can be about a tool

    def __repr__(self):
        # Accessing `self.requester` is correct due to `User.job_requests` backref
        return f"JobRequest('{self.title}', 'Requested by: {self.requester.username}', 'Status: {self.status}')"