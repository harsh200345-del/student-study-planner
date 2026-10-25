"""
Flask Application for Student Study Planner Portal
"""
from flask import Flask, render_template, request, jsonify
from datetime import date, datetime
import database

app = Flask(__name__)

database.init_db(seed_sample_data=True)

@app.route('/')
def index():
    return render_template('index.html')

# ==================== SUBJECT ROUTES ====================

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            s.id, s.name, s.color, s.description, s.created_at,
            COUNT(t.id) AS total_tasks,
            SUM(CASE WHEN t.is_completed = 1 THEN 1 ELSE 0 END) AS completed_tasks,
            SUM(CASE WHEN t.is_completed = 0 THEN 1 ELSE 0 END) AS pending_tasks,
            COALESCE(SUM(t.duration_mins), 0) AS total_duration_mins
        FROM subjects s
        LEFT JOIN tasks t ON s.id = t.subject_id
        GROUP BY s.id
        ORDER BY s.name ASC;
    """)
    rows = cursor.fetchall()
    subjects = []
    for r in rows:
        total = r['total_tasks']
        completed = r['completed_tasks'] or 0
        rate = round((completed / total * 100), 1) if total > 0 else 0
        subjects.append({
            'id': r['id'],
            'name': r['name'],
            'color': r['color'],
            'description': r['description'],
            'total_tasks': total,
            'completed_tasks': completed,
            'pending_tasks': r['pending_tasks'] or 0,
            'completion_rate': rate,
            'total_duration_mins': r['total_duration_mins']
        })
    conn.close()
    return jsonify(subjects)

@app.route('/api/subjects', methods=['POST'])
def add_subject():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    color = data.get('color', '#6366f1').strip()
    description = data.get('description', '').strip()

    if not name:
        return jsonify({'error': 'Subject name is required.'}), 400

    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subjects (name, color, description) VALUES (?, ?, ?);", (name, color, description))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'Subject created successfully!', 'id': new_id}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# ==================== TASK ROUTES ====================

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    filter_type = request.args.get('filter', 'all')
    subject_id = request.args.get('subject_id')
    search = request.args.get('search', '').strip()

    today_str = "2026-10-25"

    conn = database.get_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            t.id, t.subject_id, t.title, t.description, 
            t.due_date, t.due_time, t.duration_mins, t.priority, 
            t.is_completed, t.completed_at, t.created_at,
            s.name AS subject_name, s.color AS subject_color
        FROM tasks t
        JOIN subjects s ON t.subject_id = s.id
        WHERE 1=1
    """
    params = []

    if subject_id and subject_id != 'all':
        query += " AND t.subject_id = ?"
        params.append(subject_id)

    if search:
        query += " AND (t.title LIKE ? OR t.description LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])

    if filter_type == 'today':
        query += " AND t.due_date = ?"
        params.append(today_str)
    elif filter_type == 'upcoming':
        query += " AND t.due_date > ? AND t.is_completed = 0"
        params.append(today_str)
    elif filter_type == 'overdue':
        query += " AND t.due_date < ? AND t.is_completed = 0"
        params.append(today_str)
    elif filter_type == 'completed':
        query += " AND t.is_completed = 1"

    query += " ORDER BY t.is_completed ASC, t.due_date ASC;"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    tasks = []
    for r in rows:
        task_due = r['due_date']
        is_done = bool(r['is_completed'])
        
        if is_done:
            status = 'completed'
        elif task_due < today_str:
            status = 'overdue'
        elif task_due == today_str:
            status = 'today'
        else:
            status = 'upcoming'

        tasks.append({
            'id': r['id'],
            'subject_id': r['subject_id'],
            'subject_name': r['subject_name'],
            'subject_color': r['subject_color'],
            'title': r['title'],
            'description': r['description'],
            'due_date': r['due_date'],
            'duration_mins': r['duration_mins'],
            'priority': r['priority'],
            'is_completed': is_done,
            'status': status
        })

    conn.close()
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.get_json() or {}
    subject_id = data.get('subject_id')
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    due_date = data.get('due_date', '').strip()
    duration_mins = int(data.get('duration_mins', 45))
    priority = data.get('priority', 'Medium')

    if not title or not subject_id or not due_date:
        return jsonify({'error': 'Title, subject, and due date are required.'}), 400

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (subject_id, title, description, due_date, duration_mins, priority)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (subject_id, title, description, due_date, duration_mins, priority))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({'message': 'Task created successfully!', 'id': new_id}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json() or {}
    subject_id = data.get('subject_id')
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    due_date = data.get('due_date', '').strip()
    duration_mins = int(data.get('duration_mins', 45))
    priority = data.get('priority', 'Medium')

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tasks 
        SET subject_id = ?, title = ?, description = ?, due_date = ?, duration_mins = ?, priority = ?
        WHERE id = ?;
    """, (subject_id, title, description, due_date, duration_mins, priority, task_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task updated successfully!'})

@app.route('/api/tasks/<int:task_id>/toggle', methods=['PUT'])
def toggle_task(task_id):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_completed FROM tasks WHERE id = ?;", (task_id,))
    task = cursor.fetchone()
    if not task:
        conn.close()
        return jsonify({'error': 'Task not found'}), 404

    new_state = 0 if task['is_completed'] == 1 else 1
    completed_at = datetime.now().isoformat() if new_state == 1 else None

    cursor.execute("UPDATE tasks SET is_completed = ?, completed_at = ? WHERE id = ?;", (new_state, completed_at, task_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task status updated.', 'is_completed': bool(new_state)})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Task deleted successfully.'})

# ==================== DASHBOARD STATS ====================

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    today_str = "2026-10-25"
    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) AS total,
            SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN is_completed = 0 THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN is_completed = 0 AND due_date < ? THEN 1 ELSE 0 END) AS overdue,
            SUM(CASE WHEN due_date = ? THEN 1 ELSE 0 END) AS today_total,
            SUM(CASE WHEN due_date = ? AND is_completed = 1 THEN 1 ELSE 0 END) AS today_completed,
            COALESCE(SUM(duration_mins), 0) AS total_mins_planned,
            COALESCE(SUM(CASE WHEN is_completed = 1 THEN duration_mins ELSE 0 END), 0) AS total_mins_completed
        FROM tasks;
    """, (today_str, today_str, today_str))
    stats = cursor.fetchone()

    total = stats['total'] or 0
    completed = stats['completed'] or 0
    today_total = stats['today_total'] or 0
    today_completed = stats['today_completed'] or 0
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0

    conn.close()
    return jsonify({
        'total_tasks': total,
        'completed_tasks': completed,
        'pending_tasks': stats['pending'] or 0,
        'overdue_tasks': stats['overdue'] or 0,
        'today_total': today_total,
        'today_completed': today_completed,
        'completion_rate': completion_rate,
        'study_hours_planned': round((stats['total_mins_planned'] or 0) / 60.0, 1),
        'study_hours_completed': round((stats['total_mins_completed'] or 0) / 60.0, 1)
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)