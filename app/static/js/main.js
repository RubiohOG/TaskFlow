// TaskFlow main JavaScript file

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Handle Kanban drag-and-drop if on task board
    const kanbanItems = document.querySelectorAll('.kanban-item');
    if (kanbanItems.length > 0) {
        kanbanItems.forEach(item => {
            item.addEventListener('dragstart', handleDragStart);
            item.addEventListener('dragend', handleDragEnd);
        });
        
        const kanbanColumns = document.querySelectorAll('.kanban-column');
        kanbanColumns.forEach(column => {
            column.addEventListener('dragover', handleDragOver);
            column.addEventListener('drop', handleDrop);
        });
    }
    
    // Ajax for task status updates
    const statusForms = document.querySelectorAll('.task-status-form');
    statusForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            const url = form.getAttribute('action');
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI without reload
                    const taskElement = form.closest('.task-item');
                    taskElement.querySelector('.task-status').textContent = data.new_status;
                    
                    // Show notification
                    const notification = document.createElement('div');
                    notification.className = 'alert alert-success alert-dismissible fade show';
                    notification.innerHTML = `
                        ${data.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    document.querySelector('main > .container').prepend(notification);
                    
                    // Auto dismiss the notification
                    setTimeout(() => {
                        const bsAlert = new bootstrap.Alert(notification);
                        bsAlert.close();
                    }, 5000);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});

// Drag and drop functions for Kanban board
function handleDragStart(e) {
    this.classList.add('dragging');
    e.dataTransfer.setData('text/plain', this.getAttribute('data-task-id'));
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
}

function handleDrop(e) {
    e.preventDefault();
    const taskId = e.dataTransfer.getData('text/plain');
    const status = this.getAttribute('data-status');
    
    // Send AJAX request to update task status
    fetch(`/tasks/${taskId}/status/${status}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Move the task visually
            const task = document.querySelector(`[data-task-id="${taskId}"]`);
            this.querySelector('.kanban-items').appendChild(task);
        }
    })
    .catch(error => console.error('Error:', error));
} 