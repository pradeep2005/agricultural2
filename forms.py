# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User, Tool # Import your models here

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    role = SelectField('Role', choices=[('owner', 'Owner/Manager'), ('worker', 'Worker')], validators=[DataRequired()])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddToolForm(FlaskForm):
    name = StringField('Tool Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Add Tool')

class EditToolForm(FlaskForm):
    name = StringField('Tool Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    status = SelectField('Status', choices=[('Available', 'Available'), ('In-Use', 'In-Use'), ('Maintenance', 'Maintenance')], validators=[DataRequired()])
    last_maintenance = DateField('Last Maintenance Date (YYYY-MM-DD)', format='%Y-%m-%d', description='Optional', render_kw={"placeholder": "YYYY-MM-DD"})
    submit = SubmitField('Update Tool')

class AssignTaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    priority = SelectField('Priority', choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')], validators=[DataRequired()])
    worker_id = SelectField('Assign to Worker', coerce=int, validators=[DataRequired()])
    tool_id = SelectField('Select Tool (Optional)', coerce=int, choices=[(0, '-- No specific tool --')], default=0) # 0 for no tool
    submit = SubmitField('Assign Task')

    def __init__(self, *args, **kwargs):
        super(AssignTaskForm, self).__init__(*args, **kwargs)
        # Re-fetch choices to ensure they are up-to-date
        self.worker_id.choices = [(worker.id, worker.username) for worker in User.query.filter_by(role='worker').all()]
        self.tool_id.choices.extend([(tool.id, f"{tool.name} ({tool.status})") for tool in Tool.query.all()])

class UpdateTaskStatusForm(FlaskForm):
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('In-Progress', 'In-Progress'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField('Update Status')

class ReportIssueForm(FlaskForm):
    tool_id = SelectField('Select Tool', coerce=int, validators=[DataRequired()])
    title = StringField('Issue Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Detailed Description of Issue', validators=[DataRequired()])
    submit = SubmitField('Report Issue')

    def __init__(self, *args, **kwargs):
        super(ReportIssueForm, self).__init__(*args, **kwargs)
        self.tool_id.choices = [(tool.id, f"{tool.name} ({tool.status})") for tool in Tool.query.all()]


# NEW FORM: JobRequestForm
class JobRequestForm(FlaskForm):
    title = StringField('Request Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Describe the job you are requesting/suggesting', validators=[DataRequired()])
    tool_id = SelectField('Relevant Tool (Optional)', coerce=int, choices=[(0, '-- No specific tool --')], default=0)
    submit = SubmitField('Submit Job Request')

    def __init__(self, *args, **kwargs):
        super(JobRequestForm, self).__init__(*args, **kwargs)
        self.tool_id.choices.extend([(tool.id, f"{tool.name} ({tool.status})") for tool in Tool.query.all()])

# NEW FORM: OwnerActionJobRequestForm
class OwnerActionJobRequestForm(FlaskForm):
    action = SelectField('Action', choices=[('approve', 'Approve as Task'), ('decline', 'Decline Request')], validators=[DataRequired()])
    # Optional fields if approving to create a task
    new_task_priority = SelectField('Task Priority (if approved)', choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')], default='Medium')
    # worker_id (auto-filled from request, but could be selectable if needed)
    submit = SubmitField('Process Request')