from flask import render_template, flash, redirect, url_for, request, abort, current_app, jsonify, send_from_directory
from flask_login import current_user, login_required
from app.tasks import bp
from app.tasks.forms import TaskForm, TaskEditForm, CommentForm
from app.models import Task, Project, Comment, User, Attachment
from app.persistence import (
    get_project_by_id, save_task, get_task_by_id, delete_task, 
    get_user_by_username, save_comment, get_comments_by_task,
    save_attachment, get_attachments_by_task, get_attachment_by_id, delete_object_by_id
)
import os
from werkzeug.utils import secure_filename

@bp.route('/projects/<project_id>/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
    project = get_project_by_id(project_id)
    if not project:
        abort(404)
    
    if project.owner_id != current_user.id and current_user.id not in project.member_ids:
        abort(403)
    
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            due_date=form.due_date.data,
            project_id=project_id,
            creator_id=current_user.id
        )
        save_task(task)
        flash('Task created successfully!', 'success')
        return redirect(url_for('projects.view_project', project_id=project_id))
    
    return render_template('tasks/create_task.html',
                         title='Create Task',
                         form=form,
                         project=project)

@bp.route('/tasks/<task_id>')
@login_required
def view_task(task_id):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    
    project = get_project_by_id(task.project_id)
    if not project:
        abort(404)
    
    if project.owner_id != current_user.id and current_user.id not in project.member_ids:
        abort(403)
    
    comment_form = CommentForm()
    comments = get_comments_by_task(task_id)
    attachments = get_attachments_by_task(task_id)
    
    # Enriquecer comentarios con el nombre de usuario
    from app.persistence import get_user_by_id
    for comment in comments:
        user = get_user_by_id(comment.user_id)
        comment.user_name = user.username if user else 'User'
    
    assignee_name = None
    if task.assignee_id:
        from app.persistence import get_user_by_id
        assignee = get_user_by_id(task.assignee_id)
        if assignee:
            assignee_name = assignee.username
    
    return render_template('tasks/view_task.html',
                         title=task.title,
                         task=task,
                         project=project,
                         comments=comments,
                         attachments=attachments,
                         comment_form=comment_form,
                         assignee_name=assignee_name)

@bp.route('/tasks/<task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    
    project = get_project_by_id(task.project_id)
    if not project:
        abort(404)
    
    if project.owner_id != current_user.id and current_user.id not in project.member_ids:
        abort(403)
    
    form = TaskEditForm()
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.status = form.status.data
        task.priority = form.priority.data
        task.due_date = form.due_date.data
        save_task(task)
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks.view_task', task_id=task.id))
    elif request.method == 'GET':
        form.title.data = task.title
        form.description.data = task.description
        form.status.data = task.status
        form.priority.data = task.priority
        form.due_date.data = task.due_date
    
    return render_template('tasks/edit_task.html',
                         title='Edit Task',
                         form=form,
                         task=task,
                         project=project)

@bp.route('/tasks/<task_id>/delete', methods=['POST'])
@login_required
def delete_task_route(task_id):
    # Intentar cargar la tarea
    task = get_task_by_id(task_id)
    
    # Si no existe la tarea, podría estar ya eliminada o ser corrupta
    if not task:
        # Intentar obtener el project_id desde el referrer
        try:
            project_id = request.referrer.split('/projects/')[1].split('/')[0]
        except:
            # Si no podemos obtenerlo, redirigir a la lista de proyectos
            flash('No se pudo determinar el proyecto asociado a la tarea', 'warning')
            return redirect(url_for('projects.projects'))
        
        # Forzar la eliminación llamando a delete_task aún cuando no existe
        delete_task(task_id)
        
        flash('Tarea eliminada correctamente', 'success')
        return redirect(url_for('projects.view_project', project_id=project_id))

    # Obtener el proyecto asociado
    project_id = task.project_id
    project = get_project_by_id(project_id)
    
    # Verificar que existe el proyecto
    if not project:
        abort(404)
    
    # Verificar permisos
    if project.owner_id != current_user.id and current_user.id not in project.member_ids:
        abort(403)
    
    # Eliminar la tarea
    success = delete_task(task_id)
    
    if success:
        flash('Tarea eliminada correctamente', 'success')
    else:
        flash('Se ha intentado eliminar la tarea, pero puede que no se haya eliminado completamente', 'warning')
    
    return redirect(url_for('projects.view_project', project_id=project_id))

@bp.route('/tasks/<task_id>/assign', methods=['POST'])
@login_required
def assign_task(task_id):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    
    project = get_project_by_id(task.project_id)
    if not project:
        abort(404)
    
    if project.owner_id != current_user.id and current_user.id not in project.member_ids:
        abort(403)
    
    username = request.form.get('username')
    user = get_user_by_username(username)
    
    if user is None:
        flash('User not found.', 'danger')
    elif user.id != project.owner_id and user.id not in project.member_ids:
        flash('User is not a member of this project.', 'warning')
    else:
        task.assignee_id = user.id
        save_task(task)
        flash(f'Task assigned to {username}.', 'success')
    
    return redirect(url_for('tasks.view_task', task_id=task.id))

@bp.route('/tasks/<task_id>/comment', methods=['POST'])
@login_required
def add_comment(task_id):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    
    project = get_project_by_id(task.project_id)
    if not project:
        abort(404)
    
    if project.owner_id != current_user.id and current_user.id not in project.member_ids:
        abort(403)
    
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            task_id=task.id,
            user_id=current_user.id
        )
        save_comment(comment)
        flash('Comment added successfully!', 'success')
    
    return redirect(url_for('tasks.view_task', task_id=task.id))

@bp.route('/tasks/<task_id>/upload', methods=['POST'])
@login_required
def upload_file(task_id):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    
    project = get_project_by_id(task.project_id)
    if not project:
        abort(404)
    
    if project.owner_id != current_user.id and current_user.id not in project.member_ids:
        abort(403)
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if 'file' not in request.files:
        if is_ajax:
            return jsonify({"success": False, "message": "No file selected"})
        flash('No file selected', 'warning')
        return redirect(url_for('tasks.view_task', task_id=task.id))
    
    file = request.files['file']
    if file.filename == '':
        if is_ajax:
            return jsonify({"success": False, "message": "No file selected"})
        flash('No file selected', 'warning')
        return redirect(url_for('tasks.view_task', task_id=task.id))
    
    # Verificar extensión de archivo permitida
    allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        if is_ajax:
            return jsonify({"success": False, "message": "File type not allowed"})
        flash('File type not allowed. Allowed extensions: ' + ', '.join(allowed_extensions), 'danger')
        return redirect(url_for('tasks.view_task', task_id=task.id))
    
    if file:
        filename = secure_filename(file.filename)
        # Asegurar que el nombre de archivo sea único usando timestamp
        from datetime import datetime
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        try:
            file.save(file_path)
            
            attachment = Attachment(
                filename=unique_filename,
                file_path=file_path,
                task_id=task.id,
                user_id=current_user.id
            )
            attachment_id = save_attachment(attachment)
            
            if is_ajax:
                return jsonify({
                    "success": True, 
                    "message": "File uploaded successfully!",
                    "filename": filename,
                    "attachment_id": attachment_id
                })
            flash('File uploaded successfully!', 'success')
        except Exception as e:
            current_app.logger.error(f"Error al guardar archivo: {str(e)}")
            if is_ajax:
                return jsonify({"success": False, "message": "Error saving file"})
            flash('Error uploading file. Please try again.', 'danger')
    
    return redirect(url_for('tasks.view_task', task_id=task.id))

@bp.route('/tasks/<task_id>/status/<status>', methods=['POST'])
@login_required
def change_task_status(task_id, status):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    
    project = get_project_by_id(task.project_id)
    if not project:
        abort(404)
    
    if project.owner_id != current_user.id and current_user.id not in project.member_ids:
        abort(403)
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if status not in ['todo', 'in_progress', 'done']:
        if is_ajax:
            return jsonify({"success": False, "message": "Invalid task status"})
        flash('Invalid task status', 'danger')
    else:
        old_status = task.status
        task.status = status
        save_task(task)
        
        if is_ajax:
            return jsonify({
                "success": True, 
                "message": f"Task status updated to {status.replace('_', ' ')}", 
                "new_status": status.replace('_', ' '),
                "old_status": old_status.replace('_', ' ')
            })
        flash(f'Task status updated to {status.replace("_", " ")}', 'success')
    
    return redirect(url_for('tasks.view_task', task_id=task.id))

@bp.route('/tasks/attachment/<filename>')
@login_required
def download_attachment(filename):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    try:
        return send_from_directory(upload_folder, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@bp.route('/tasks/attachment/<attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    from app.persistence import get_attachments_by_task, save_attachment
    from app.models import Attachment
    import pickle
    s = current_app.extensions['sirope'] if 'sirope' in current_app.extensions else None
    if not s:
        import sirope
        s = sirope.Sirope()
    # Buscar el adjunto en Redis
    serialized = s._redis.hget("Attachment", str(attachment_id))
    task_id = request.form.get('task_id')
    if serialized:
        attachment = pickle.loads(serialized)
        # Eliminar archivo físico si existe
        try:
            if os.path.exists(attachment.file_path):
                os.remove(attachment.file_path)
        except Exception as e:
            current_app.logger.warning(f"No se pudo eliminar el archivo físico: {e}")
        # Eliminar registro en Redis
        s._redis.hdel("Attachment", str(attachment_id))
        flash('Attachment deleted successfully!', 'success')
    else:
        flash('Attachment not found.', 'warning')
    return redirect(url_for('tasks.view_task', task_id=task_id)) 