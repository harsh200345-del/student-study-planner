let currentFilter = 'all';
let searchDebounceTimeout = null;
let statusChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
    loadSubjects();
    loadTasks();
});

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    const bgCol = type === 'success' ? 'bg-emerald-600' : 'bg-slate-900';
    toast.className = `toast pointer-events-auto px-4 py-3 rounded-2xl text-white text-xs font-semibold shadow-xl flex items-center gap-2 ${bgCol}`;
    toast.innerHTML = `<i data-lucide="${type === 'success' ? 'check-circle' : 'info'}" class="w-4 h-4"></i> ${message}`;
    container.appendChild(toast);
    lucide.createIcons();
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function setFilter(filter) {
    currentFilter = filter;
    document.querySelectorAll('.filter-tab').forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-100');
        btn.classList.add('text-slate-600', 'hover:bg-slate-100');
    });

    const activeBtn = document.getElementById(`btn-filter-${filter}`);
    if (activeBtn) {
        activeBtn.classList.remove('text-slate-600', 'hover:bg-slate-100');
        activeBtn.classList.add('bg-indigo-600', 'text-white', 'shadow-md', 'shadow-indigo-100');
    }

    loadTasks();
}

function debounceSearch() {
    clearTimeout(searchDebounceTimeout);
    searchDebounceTimeout = setTimeout(() => loadTasks(), 300);
}

async function loadDashboardStats() {
    try {
        const response = await fetch('/api/dashboard/stats');
        const stats = await response.json();

        document.getElementById('statTotalTasks').textContent = stats.total_tasks;
        document.getElementById('statRemainingTasks').textContent = stats.pending_tasks;
        document.getElementById('statCompletionRate').textContent = `${stats.completion_rate}%`;
        document.getElementById('statProgressBar').style.width = `${stats.completion_rate}%`;

        document.getElementById('statTodayFocus').textContent = `${stats.today_completed} / ${stats.today_total}`;
        document.getElementById('statHoursCompleted').textContent = stats.study_hours_completed;
        document.getElementById('statHoursPlanned').textContent = stats.study_hours_planned;

        renderStatusChart(stats.completed_tasks, stats.pending_tasks, stats.overdue_tasks);
    } catch (err) {
        console.error('Error loading stats:', err);
    }
}

async function loadSubjects() {
    try {
        const response = await fetch('/api/subjects');
        const subjects = await response.json();

        const subjectList = document.getElementById('subjectList');
        const subjectFilter = document.getElementById('subjectFilter');
        const taskSubjectSelect = document.getElementById('taskSubject');

        subjectList.innerHTML = '';
        subjectFilter.innerHTML = '<option value="all">All Subjects</option>';
        taskSubjectSelect.innerHTML = '';

        subjects.forEach(subj => {
            subjectList.innerHTML += `
                <div class="p-3.5 rounded-2xl bg-slate-50/80 border border-slate-100 space-y-2">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2">
                            <span class="w-3 h-3 rounded-full shadow-sm" style="background-color: ${subj.color}"></span>
                            <span class="text-xs font-bold text-slate-800">${subj.name}</span>
                        </div>
                        <span class="text-[11px] text-slate-400 font-semibold">${subj.completed_tasks}/${subj.total_tasks} tasks</span>
                    </div>
                    <div class="w-full bg-slate-200/70 h-2 rounded-full overflow-hidden">
                        <div class="h-full rounded-full transition-all duration-500" style="width: ${subj.completion_rate}%; background-color: ${subj.color}"></div>
                    </div>
                </div>
            `;
            subjectFilter.innerHTML += `<option value="${subj.id}">${subj.name}</option>`;
            taskSubjectSelect.innerHTML += `<option value="${subj.id}">${subj.name}</option>`;
        });

        lucide.createIcons();
    } catch (err) {
        console.error('Error loading subjects:', err);
    }
}

async function loadTasks() {
    try {
        const search = document.getElementById('searchInput').value;
        const subjectId = document.getElementById('subjectFilter').value;

        const response = await fetch(`/api/tasks?filter=${currentFilter}&subject_id=${subjectId}&search=${encodeURIComponent(search)}`);
        const tasks = await response.json();

        const container = document.getElementById('taskList');
        container.innerHTML = '';

        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="bg-white rounded-3xl p-10 border border-slate-100 text-center text-slate-400 shadow-sm">
                    <i data-lucide="check-circle" class="w-12 h-12 mx-auto text-slate-300 mb-2"></i>
                    <p class="text-sm font-bold text-slate-700">No tasks found</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }

        tasks.forEach(task => {
            const isDone = task.is_completed;
            const priorityBadge = task.priority === 'High' 
                ? 'bg-rose-50 text-rose-600 border-rose-100' 
                : (task.priority === 'Medium' ? 'bg-amber-50 text-amber-600 border-amber-100' : 'bg-slate-100 text-slate-600 border-slate-200');

            let dateBadgeClass = 'text-slate-500';
            if (task.status === 'overdue') dateBadgeClass = 'text-rose-600 font-bold';
            if (task.status === 'today') dateBadgeClass = 'text-indigo-600 font-bold';

            const hoursDisplay = task.duration_mins >= 60 ? `${(task.duration_mins/60).toFixed(1)} hrs` : `${task.duration_mins} mins`;

            container.innerHTML += `
                <div class="bg-white rounded-2xl p-4.5 border border-slate-100/80 shadow-sm flex items-start gap-4 task-card">
                    <input type="checkbox" ${isDone ? 'checked' : ''} onchange="toggleTask(${task.id})" class="task-checkbox mt-1">
                    
                    <div class="flex-1 min-w-0">
                        <p class="text-xs font-bold ${isDone ? 'line-through text-slate-400' : 'text-slate-900'}">${task.title}</p>
                        ${task.description ? `<p class="text-[11px] text-slate-400 mt-0.5 truncate font-medium">${task.description}</p>` : ''}
                        
                        <div class="flex flex-wrap items-center gap-3 mt-3">
                            <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-[11px] font-bold" style="background-color: ${task.subject_color}15; color: ${task.subject_color}">
                                <span class="w-2 h-2 rounded-full" style="background-color: ${task.subject_color}"></span>
                                ${task.subject_name}
                            </span>
                            
                            <span class="text-[11px] ${dateBadgeClass} flex items-center gap-1">
                                <i data-lucide="calendar" class="w-3.5 h-3.5"></i>
                                ${task.due_date} ${task.status === 'overdue' ? '(Overdue)' : ''}
                            </span>

                            <span class="text-[11px] text-slate-400 font-semibold flex items-center gap-1">
                                <i data-lucide="clock" class="w-3.5 h-3.5"></i>
                                ${hoursDisplay}
                            </span>

                            <span class="px-2.5 py-0.5 border rounded-lg text-[10px] font-bold ${priorityBadge}">
                                ${task.priority}
                            </span>
                        </div>
                    </div>

                    <div class="flex items-center gap-1">
                        <button onclick="openEditTaskModal(${task.id}, '${task.title.replace(/'/g, "\\'")}', ${task.subject_id}, '${task.due_date}', ${task.duration_mins}, '${task.priority}', '${(task.description || '').replace(/'/g, "\\'")}')" class="text-slate-300 hover:text-indigo-600 p-1.5 rounded-xl hover:bg-indigo-50 transition-colors">
                            <i data-lucide="pencil" class="w-4 h-4"></i>
                        </button>
                        <button onclick="deleteTask(${task.id})" class="text-slate-300 hover:text-rose-500 p-1.5 rounded-xl hover:bg-rose-50 transition-colors">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>
                    </div>
                </div>
            `;
        });

        lucide.createIcons();
    } catch (err) {
        console.error('Error loading tasks:', err);
    }
}

async function toggleTask(taskId) {
    await fetch(`/api/tasks/${taskId}/toggle`, { method: 'PUT' });
    loadTasks();
    loadDashboardStats();
    loadSubjects();
    showToast('Task status updated!');
}

async function deleteTask(taskId) {
    if (confirm('Delete this task?')) {
        await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
        loadTasks();
        loadDashboardStats();
        loadSubjects();
        showToast('Task deleted successfully.', 'info');
    }
}

function openTaskModal() {
    document.getElementById('taskId').value = '';
    document.getElementById('taskModalTitle').textContent = 'Add New Study Task';
    document.getElementById('taskDueDate').value = "2026-10-25";
    document.getElementById('taskModal').classList.remove('hidden');
}

function openEditTaskModal(id, title, subjectId, dueDate, duration, priority, description) {
    document.getElementById('taskId').value = id;
    document.getElementById('taskModalTitle').textContent = 'Edit Study Task';
    document.getElementById('taskTitle').value = title;
    document.getElementById('taskSubject').value = subjectId;
    document.getElementById('taskDueDate').value = dueDate;
    document.getElementById('taskDuration').value = duration;
    document.getElementById('taskPriority').value = priority;
    document.getElementById('taskDescription').value = description;
    document.getElementById('taskModal').classList.remove('hidden');
}

function closeTaskModal() {
    document.getElementById('taskModal').classList.add('hidden');
    document.getElementById('taskForm').reset();
}

async function handleTaskSubmit(e) {
    e.preventDefault();
    const taskId = document.getElementById('taskId').value;
    const payload = {
        title: document.getElementById('taskTitle').value,
        subject_id: document.getElementById('taskSubject').value,
        due_date: document.getElementById('taskDueDate').value,
        duration_mins: document.getElementById('taskDuration').value,
        priority: document.getElementById('taskPriority').value,
        description: document.getElementById('taskDescription').value
    };

    if (taskId) {
        await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        showToast('Task updated successfully!');
    } else {
        await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        showToast('Task created successfully!');
    }

    closeTaskModal();
    loadTasks();
    loadDashboardStats();
    loadSubjects();
}

function openSubjectModal() {
    document.getElementById('subjectModal').classList.remove('hidden');
}

function closeSubjectModal() {
    document.getElementById('subjectModal').classList.add('hidden');
    document.getElementById('subjectForm').reset();
}

async function handleSubjectSubmit(e) {
    e.preventDefault();
    const payload = {
        name: document.getElementById('subjectName').value,
        color: document.getElementById('subjectColor').value,
        description: document.getElementById('subjectDescription').value
    };

    await fetch('/api/subjects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    closeSubjectModal();
    loadSubjects();
    loadDashboardStats();
    showToast('Subject created successfully!');
}

function renderStatusChart(completed, pending, overdue) {
    const ctx = document.getElementById('statusChart').getContext('2d');
    if (statusChartInstance) statusChartInstance.destroy();

    statusChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'Pending', 'Overdue'],
            datasets: [{
                data: [completed, pending, overdue],
                backgroundColor: ['#10b981', '#6366f1', '#f43f5e'],
                borderWidth: 0,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 10, padding: 15, font: { size: 11, weight: '600' } } }
            },
            cutout: '78%'
        }
    });
}