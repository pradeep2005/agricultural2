from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from datetime import datetime

# Import from your new files
from models import db, User, Tool, Task, ToolIssue, JobRequest # Added JobRequest
from forms import (RegistrationForm, LoginForm, AddToolForm, EditToolForm,
                   AssignTaskForm, UpdateTaskStatusForm, ReportIssueForm,
                   JobRequestForm, OwnerActionJobRequestForm) # Added new forms
from decorators import owner_required, worker_required
from config import Config # Assuming you will use a config.py


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    # If user is logged in, go to their dashboard
    if current_user.is_authenticated:
        if current_user.role == 'owner':
            return redirect(url_for('owner_dashboard'))
        elif current_user.role == 'worker':
            return redirect(url_for('worker_dashboard'))
    
    # If user is NOT logged in, show the homepage
    return render_template('home.html')

@app.route('/tractor')
def tractor():
    return render_template('tractor.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('owner_dashboard') if current_user.role == 'owner' else url_for('worker_dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        role = form.role.data

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Account created successfully for {username} as {role}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('owner_dashboard') if current_user.role == 'owner' else url_for('worker_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            if user.role == 'owner':
                return redirect(url_for('owner_dashboard'))
            else:
                return redirect(url_for('worker_dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Owner Routes
@app.route('/owner/dashboard')
@owner_required
def owner_dashboard():
    tools = Tool.query.all()
    tasks = Task.query.all()
    issues = ToolIssue.query.all()
    job_requests = JobRequest.query.filter_by(status='Pending').order_by(JobRequest.requested_date.desc()).all() # Only show pending requests
    workers = User.query.filter_by(role='worker').all()

    # Statistics
    total_tools = len(tools)
    available_tools = len([tool for tool in tools if tool.status == 'Available'])
    in_use_tools = len([tool for tool in tools if tool.status == 'In-Use'])
    maintenance_tools = len([tool for tool in tools if tool.status == 'Maintenance'])

    total_tasks = len(tasks)
    pending_tasks = len([task for task in tasks if task.status == 'Pending'])
    in_progress_tasks = len([task for task in tasks if task.status == 'In-Progress'])
    completed_tasks = len([task for task in tasks if task.status == 'Completed'])

    # Forms for owner actions on job requests
    job_request_forms = {}
    for req in job_requests:
        form = OwnerActionJobRequestForm()
        job_request_forms[req.id] = form

    return render_template('owner/dashboard.html',
                           tools=tools,
                           tasks=tasks,
                           issues=issues,
                           job_requests=job_requests, # Pass job requests
                           workers=workers,
                           total_tools=total_tools,
                           available_tools=available_tools,
                           in_use_tools=in_use_tools,
                           maintenance_tools=maintenance_tools,
                           total_tasks=total_tasks,
                           pending_tasks=pending_tasks,
                           in_progress_tasks=in_progress_tasks,
                           completed_tasks=completed_tasks,
                           job_request_forms=job_request_forms) # Pass job request forms

@app.route('/owner/add_tool', methods=['GET', 'POST'])
@owner_required
def add_tool():
    form = AddToolForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        new_tool = Tool(name=name, description=description)
        db.session.add(new_tool)
        db.session.commit()
        flash('Tool added successfully!', 'success')
        return redirect(url_for('owner_dashboard'))
    return render_template('owner/add_tool.html', form=form)

@app.route('/owner/edit_tool/<int:tool_id>', methods=['GET', 'POST'])
@owner_required
def edit_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    form = EditToolForm(obj=tool)
    if form.validate_on_submit():
        tool.name = form.name.data
        tool.description = form.description.data
        tool.status = form.status.data
        tool.last_maintenance = form.last_maintenance.data if form.last_maintenance.data else None
        db.session.commit()
        flash('Tool updated successfully!', 'success')
        return redirect(url_for('owner_dashboard'))
    return render_template('owner/edit_tool.html', form=form, tool=tool)

@app.route('/owner/delete_tool/<int:tool_id>', methods=['POST'])
@owner_required
def delete_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    # Also delete any tasks or issues associated with this tool to prevent foreign key errors
    Task.query.filter_by(tool_id=tool.id).delete()
    ToolIssue.query.filter_by(tool_id=tool.id).delete()
    JobRequest.query.filter_by(tool_id=tool.id).delete() # Delete requests for this tool
    db.session.delete(tool)
    db.session.commit()
    flash('Tool deleted successfully!', 'success')
    return redirect(url_for('owner_dashboard'))

@app.route('/owner/assign_task', methods=['GET', 'POST'])
@owner_required
def assign_task():
    form = AssignTaskForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        priority = form.priority.data
        worker_id = form.worker_id.data
        tool_id = form.tool_id.data if form.tool_id.data != 0 else None

        new_task = Task(title=title, description=description, priority=priority, worker_id=worker_id)
        if tool_id:
            new_task.tool_id = tool_id
            tool = Tool.query.get(tool_id)
            if tool:
                tool.status = 'In-Use'
        db.session.add(new_task)
        db.session.commit()
        flash('Task assigned successfully!', 'success')
        return redirect(url_for('owner_dashboard'))
    return render_template('owner/assign_task.html', form=form)

# NEW ROUTE: Owner action on job request
@app.route('/owner/process_job_request/<int:request_id>', methods=['POST'])
@owner_required
def process_job_request(request_id):
    job_request = JobRequest.query.get_or_404(request_id)
    form = OwnerActionJobRequestForm()
    if form.validate_on_submit():
        action = form.action.data
        if action == 'approve':
            # Create a new task based on the job request
            new_task = Task(
                title=f"Worker Request: {job_request.title}",
                description=job_request.description,
                priority=form.new_task_priority.data, # Use priority from form
                worker_id=job_request.worker_id,
                tool_id=job_request.tool_id
            )
            db.session.add(new_task)
            job_request.status = 'Approved'
            flash(f"Job request '{job_request.title}' approved and converted to a task!", 'success')
            # If a tool was requested, mark it as in-use
            if job_request.tool and job_request.tool.status == 'Available':
                job_request.tool.status = 'In-Use'

        elif action == 'decline':
            job_request.status = 'Declined'
            flash(f"Job request '{job_request.title}' declined.", 'info')
        db.session.commit()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('owner_dashboard'))

# Worker Routes
@app.route('/worker/dashboard')
@worker_required
def worker_dashboard():
    assigned_tasks = Task.query.filter_by(worker_id=current_user.id).order_by(Task.assigned_date.desc()).all()
    available_tools = Tool.query.filter_by(status='Available').all()
    your_job_requests = JobRequest.query.filter_by(worker_id=current_user.id).order_by(JobRequest.requested_date.desc()).all() # Worker's own job requests

    # Worker specific statistics
    total_tasks = len(assigned_tasks)
    pending_tasks = len([task for task in assigned_tasks if task.status == 'Pending'])
    in_progress_tasks = len([task for task in assigned_tasks if task.status == 'In-Progress'])
    completed_tasks = len([task for task in assigned_tasks if task.status == 'Completed'])

    # Prepare forms for inline task status updates
    task_forms = {}
    for task in assigned_tasks:
        form = UpdateTaskStatusForm(obj=task)
        task_forms[task.id] = form

    return render_template('worker/dashboard.html',
                           assigned_tasks=assigned_tasks,
                           available_tools=available_tools,
                           your_job_requests=your_job_requests, # Pass worker's own job requests
                           total_tasks=total_tasks,
                           pending_tasks=pending_tasks,
                           in_progress_tasks=in_progress_tasks,
                           completed_tasks=completed_tasks,
                           task_forms=task_forms)

@app.route('/worker/update_task/<int:task_id>', methods=['POST'])
@worker_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.worker_id != current_user.id:
        flash('You are not authorized to update this task.', 'danger')
        return redirect(url_for('worker_dashboard'))

    form = UpdateTaskStatusForm()
    if form.validate_on_submit():
        new_status = form.status.data
        task.status = new_status
        if new_status == 'Completed':
            task.completed_date = datetime.utcnow()
            if task.tool:
                task.tool.status = 'Available'
        db.session.commit()
        flash('Task status updated successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(url_for('worker_dashboard'))

@app.route('/worker/report_issue', methods=['GET', 'POST'])
@worker_required
def report_issue():
    form = ReportIssueForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        tool_id = form.tool_id.data

        new_issue = ToolIssue(title=title, description=description, reporter_id=current_user.id, tool_id=tool_id)
        tool = Tool.query.get(tool_id)
        if tool and tool.status != 'Maintenance':
            tool.status = 'Maintenance'
        db.session.add(new_issue)
        db.session.commit()
        flash('Tool issue reported successfully!', 'success')
        return redirect(url_for('worker_dashboard'))
    return render_template('worker/report_issue.html', form=form)

# NEW ROUTE: Worker can request a job
@app.route('/worker/request_job', methods=['GET', 'POST'])
@worker_required
def request_job():
    form = JobRequestForm()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        tool_id = form.tool_id.data if form.tool_id.data != 0 else None

        new_request = JobRequest(title=title, description=description, worker_id=current_user.id, tool_id=tool_id)
        db.session.add(new_request)
        db.session.commit()
        flash('Your job request has been submitted to the owner for review!', 'success')
        return redirect(url_for('worker_dashboard')) # THIS LINE changed
    return render_template('worker/request_job.html', form=form)

# In your app.py, likely within the Worker Routes section

@app.route('/worker/available_jobs')
@worker_required
def available_jobs():
    # Logic to fetch and display jobs that are available for workers to take
    # For example, tasks that are 'Pending' and not yet assigned to anyone,
    # or perhaps a different model for jobs explicitly listed as 'available'.
    
    # Placeholder: For now, let's assume it lists tasks with status 'Pending'
    # and no worker_id assigned, or a dedicated 'Job' model
    
    # Example: Query tasks that are pending and unassigned
    available_tasks = Task.query.filter_by(status='Pending', worker_id=None).all()

    return render_template('worker/available_jobs.html', available_tasks=available_tasks)

# In your app.py, likely within the Worker Routes section

@app.route('/worker/my_applications')
@worker_required
def my_applications():
    # Logic to fetch and display job requests this worker has made
    # or jobs they have applied for (if you implement an 'application' system)
    
    # Since worker_dashboard already shows 'your_job_requests', you could:
    # 1. Reuse that logic here, if this page is simply a dedicated view for requests.
    #    E.g., job_requests = JobRequest.query.filter_by(worker_id=current_user.id).order_by(JobRequest.requested_date.desc()).all()
    # 2. Implement a more formal 'application' system if jobs are distinct from requests.

    # For now, let's assume it lists their submitted JobRequests
    worker_requests = JobRequest.query.filter_by(worker_id=current_user.id).order_by(JobRequest.requested_date.desc()).all()

    return render_template('worker/my_applications.html', worker_requests=worker_requests)
# In your app.py, likely within the Worker Routes section

@app.route('/worker/my_jobs') # Or /worker/assigned_tasks if that's more precise
@worker_required
def my_jobs(): # Or assigned_tasks
    # Logic to fetch and display jobs/tasks assigned to the current worker
    assigned_tasks = Task.query.filter_by(worker_id=current_user.id).order_by(Task.assigned_date.desc()).all()

    return render_template('worker/my_jobs.html', assigned_tasks=assigned_tasks) # Or worker/assigned_tasks.html

# In your app.py, you could add this
@app.route('/profile', methods=['GET', 'POST'])
@login_required # Any logged-in user can view their profile
def profile():
    # You might want a form here for editing profile details
    # form = ProfileEditForm(obj=current_user)
    # if form.validate_on_submit():
    #    current_user.email = form.email.data
    #    db.session.commit()
    #    flash('Profile updated!', 'success')
    #    return redirect(url_for('profile'))
    
    return render_template('profile.html', user=current_user) # Or form=form


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default owner if not exists
        if not User.query.filter_by(username='admin', role='owner').first():
            admin_user = User(username='admin', email='admin@example.com', role='owner')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Default 'admin' owner account created.")
        # Create default worker if not exists
        if not User.query.filter_by(username='worker1', role='worker').first():
            worker_user = User(username='worker1', email='worker1@example.com', role='worker')
            worker_user.set_password('worker123')
            db.session.add(worker_user)
            db.session.commit()
            print("Default 'worker1' worker account created.")

    app.run(debug=True)