from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_required
from app.projects import bp
from app.projects.forms import ProjectForm, ProjectEditForm
from app.models import Project, User
from app.persistence import (
    save_project, get_project_by_id, get_projects_by_owner, 
    get_projects_by_member, delete_project, get_user_by_username,
    get_tasks_by_project, get_user_by_id, count_project_tasks,
    count_project_members, get_project_owner
)
from app.persistence import _deleted_project_ids

@bp.route('/projects')
@login_required
def projects():
    owned_projects = get_projects_by_owner(current_user.id)
    member_projects = get_projects_by_member(current_user.id)
    return render_template('projects/projects.html',
                         title='My Projects',
                         owned_projects=owned_projects,
                         member_projects=member_projects,
                         count_project_tasks=count_project_tasks,
                         count_project_members=count_project_members,
                         get_project_owner=get_project_owner)

@bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        # Crear un nuevo proyecto
        project = Project(
            title=form.title.data,
            description=form.description.data,
            owner_id=current_user.id
        )
        
        # Guardar el proyecto
        try:
            # Aquí aseguramos que no está en la lista de eliminados
            if str(project.id) in _deleted_project_ids:
                _deleted_project_ids.remove(str(project.id))
            
            # Guardar el proyecto
            oid = save_project(project)
            
            # Verificar que se guardó correctamente
            saved_project = get_project_by_id(project.id)
            if saved_project:
                flash('Project created successfully!', 'success')
            else:
                from app.persistence import get_sirope
                s = get_sirope()
                # Verificar directamente en Redis
                if s._redis.hexists("Project", str(project.id)):
                    flash('Project created, but with issues retrieving it. It should appear soon.', 'warning')
                else:
                    flash('Failed to create project. Please try again.', 'danger')
        except Exception as e:
            current_app.logger.error(f"Error al crear proyecto: {str(e)}")
            flash(f'Error creating project: {str(e)}', 'danger')
        
        return redirect(url_for('projects.projects'))
    
    return render_template('projects/create_project.html',
                         title='Create Project',
                         form=form)

@bp.route('/projects/<project_id>')
@login_required
def view_project(project_id):
    from app.persistence import get_sirope
    
    # Verificar primero si está en la lista de eliminados
    if str(project_id) in _deleted_project_ids:
        flash('Este proyecto ha sido eliminado.', 'warning')
        return redirect(url_for('projects.projects'))
    
    project = get_project_by_id(project_id)
    if not project:
        flash('Proyecto no encontrado. Puede haber sido eliminado.', 'warning')
        return redirect(url_for('projects.projects'))
    
    if project.owner_id != current_user.id and current_user.id not in project.member_ids:
        abort(403)
    
    # Marcar como eliminado si no existe en Redis
    s = get_sirope()
    if not s._redis.hexists("Project", str(project_id)):
        _deleted_project_ids.add(str(project_id))
        flash('Este proyecto ha sido eliminado de la base de datos.', 'warning')
        return redirect(url_for('projects.projects'))
    
    # Obtener tareas asociadas al proyecto
    tasks = get_tasks_by_project(project_id)
    
    # Obtener información del propietario
    owner = get_user_by_id(project.owner_id)
    
    # Obtener información de los miembros
    members = []
    for member_id in project.member_ids:
        member = get_user_by_id(member_id)
        if member:
            members.append(member)
    
    # Obtener asignados de tareas
    task_assignees = {}
    for task in tasks:
        if task.assignee_id:
            assignee = get_user_by_id(task.assignee_id)
            if assignee:
                task_assignees[task.id] = {
                    'username': assignee.username,
                    'id': assignee.id
                }
    
    return render_template('projects/view_project.html',
                         title=project.title,
                         project=project,
                         tasks=tasks,
                         owner=owner,
                         members=members,
                         task_assignees=task_assignees)

@bp.route('/projects/<project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    from app.persistence import get_sirope
    
    # Verificar primero si está en la lista de eliminados
    if str(project_id) in _deleted_project_ids:
        flash('Este proyecto ha sido eliminado.', 'warning')
        return redirect(url_for('projects.projects'))
    
    project = get_project_by_id(project_id)
    if not project:
        flash('Proyecto no encontrado. Puede haber sido eliminado.', 'warning')
        return redirect(url_for('projects.projects'))
    
    if project.owner_id != current_user.id:
        abort(403)
    
    # Marcar como eliminado si no existe en Redis
    s = get_sirope()
    if not s._redis.hexists("Project", str(project_id)):
        _deleted_project_ids.add(str(project_id))
        flash('Este proyecto ha sido eliminado de la base de datos.', 'warning')
        return redirect(url_for('projects.projects'))
    
    form = ProjectEditForm()
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        save_project(project)
        flash('Project updated successfully!', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    elif request.method == 'GET':
        form.title.data = project.title
        form.description.data = project.description
    
    return render_template('projects/edit_project.html',
                         title='Edit Project',
                         form=form,
                         project=project)

@bp.route('/projects/<project_id>/delete', methods=['POST'])
@login_required
def delete_project_route(project_id):
    # Verificar primero si ya está en la lista de eliminados
    if str(project_id) in _deleted_project_ids:
        flash('Este proyecto ya había sido eliminado.', 'info')
        return redirect(url_for('projects.projects'))
    
    project = get_project_by_id(project_id)
    if not project:
        # Si no se encuentra, añadirlo a la lista de eliminados por si acaso
        _deleted_project_ids.add(str(project_id))
        flash('Proyecto no encontrado. Ha sido marcado como eliminado.', 'warning')
        return redirect(url_for('projects.projects'))
    
    if project.owner_id != current_user.id:
        abort(403)
    
    # Marcar como eliminado en la lista de eliminados primero
    _deleted_project_ids.add(str(project_id))
    
    # Intentar eliminar físicamente
    delete_project(project_id)
    
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('projects.projects'))

@bp.route('/projects/<project_id>/add_member', methods=['POST'])
@login_required
def add_member(project_id):
    from app.persistence import get_sirope
    
    # Verificar primero si está en la lista de eliminados
    if str(project_id) in _deleted_project_ids:
        flash('Este proyecto ha sido eliminado.', 'warning')
        return redirect(url_for('projects.projects'))
    
    project = get_project_by_id(project_id)
    if not project:
        flash('Proyecto no encontrado. Puede haber sido eliminado.', 'warning')
        return redirect(url_for('projects.projects'))
    
    if project.owner_id != current_user.id:
        abort(403)
    
    # Marcar como eliminado si no existe en Redis
    s = get_sirope()
    if not s._redis.hexists("Project", str(project_id)):
        _deleted_project_ids.add(str(project_id))
        flash('Este proyecto ha sido eliminado de la base de datos.', 'warning')
        return redirect(url_for('projects.projects'))
    
    username = request.form.get('username')
    user = get_user_by_username(username)
    
    if user is None:
        flash('User not found.', 'danger')
    elif user.id in project.member_ids:
        flash('User is already a member of this project.', 'warning')
    else:
        project.add_member(user.id)
        save_project(project)
        flash(f'{username} has been added to the project.', 'success')
    
    return redirect(url_for('projects.view_project', project_id=project.id))

@bp.route('/projects/<project_id>/remove_member/<user_id>', methods=['POST'])
@login_required
def remove_member(project_id, user_id):
    from app.persistence import get_sirope
    
    # Verificar primero si está en la lista de eliminados
    if str(project_id) in _deleted_project_ids:
        flash('Este proyecto ha sido eliminado.', 'warning')
        return redirect(url_for('projects.projects'))
    
    project = get_project_by_id(project_id)
    if not project:
        flash('Proyecto no encontrado. Puede haber sido eliminado.', 'warning')
        return redirect(url_for('projects.projects'))
    
    if project.owner_id != current_user.id:
        abort(403)
    
    # Marcar como eliminado si no existe en Redis
    s = get_sirope()
    if not s._redis.hexists("Project", str(project_id)):
        _deleted_project_ids.add(str(project_id))
        flash('Este proyecto ha sido eliminado de la base de datos.', 'warning')
        return redirect(url_for('projects.projects'))
    
    if user_id in project.member_ids:
        project.remove_member(user_id)
        save_project(project)
        flash(f'User has been removed from the project.', 'success')
    
    return redirect(url_for('projects.view_project', project_id=project.id)) 