from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class ProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Create Project')

class ProjectEditForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    submit = SubmitField('Update Project') 