from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from app.main import bp
from app.models import User, Project, Task
from app.persistence import (
    get_projects_by_owner, get_projects_by_member, get_tasks_by_assignee, 
    count_project_tasks, get_project_by_id
)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # Get user's projects
    owned_projects = get_projects_by_owner(current_user.id)
    member_projects = get_projects_by_member(current_user.id)
    
    # Get user's tasks
    assigned_tasks = get_tasks_by_assignee(current_user.id)
    
    return render_template('main/index.html',
                         title='Dashboard',
                         owned_projects=owned_projects,
                         member_projects=member_projects,
                         assigned_tasks=assigned_tasks,
                         count_project_tasks=count_project_tasks,
                         get_project_by_id=get_project_by_id) 