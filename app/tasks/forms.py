from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from datetime import datetime

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    due_date = DateTimeField('Due Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
    submit = SubmitField('Create Task')

class TaskEditForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    status = SelectField('Status', choices=[
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    due_date = DateTimeField('Due Date', format='%Y-%m-%d %H:%M', validators=[Optional()])
    submit = SubmitField('Update Task')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Add Comment') 