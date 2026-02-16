"""Web UI for AI Governance Tool Audit Dashboard."""

from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json
from .audit_logger import AuditLogger
from .refactor_state import RefactorState

app = Flask(__name__,
    template_folder='templates',
    static_folder='static')


def get_audit_logger():
    """Get audit logger instance."""
    return AuditLogger()


def get_refactor_state():
    """Get refactor state manager instance."""
    return RefactorState()


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/logs')
def get_logs():
    """Get audit logs with optional filtering and pagination.

    Query params:
        timeframe: day, week, month, all (default: all)
        status: filter by status
        page: page number (default: 1)
        per_page: records per page (default: 20)
    """
    audit_logger = get_audit_logger()

    timeframe = request.args.get('timeframe', 'all')
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    # Get all logs first (without limit)
    if status:
        all_logs = audit_logger.get_logs_by_status(status, limit=10000)
    else:
        all_logs = audit_logger.get_logs_by_timeframe(timeframe, limit=10000)

    # Calculate pagination
    total_logs = len(all_logs)
    total_pages = (total_logs + per_page - 1) // per_page  # Ceiling division
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_logs = all_logs[start_idx:end_idx]

    return jsonify({
        'success': True,
        'logs': paginated_logs,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_logs': total_logs,
            'total_pages': total_pages,
            'has_previous': page > 1,
            'has_next': page < total_pages
        }
    })


@app.route('/api/log/<int:log_id>')
def get_log_detail(log_id):
    """Get detailed information for a specific audit log entry."""
    audit_logger = get_audit_logger()

    # Get all logs and find the one with matching ID
    logs = audit_logger.get_recent_logs(limit=10000)
    log_entry = next((log for log in logs if log['id'] == log_id), None)

    if not log_entry:
        return jsonify({
            'success': False,
            'error': 'Log entry not found'
        }), 404

    return jsonify({
        'success': True,
        'log': log_entry
    })


@app.route('/api/statistics')
def get_statistics():
    """Get audit statistics.

    Query params:
        timeframe: day, week, month, all (default: all)
    """
    audit_logger = get_audit_logger()

    timeframe = request.args.get('timeframe', 'all')
    stats = audit_logger.get_statistics_by_timeframe(timeframe)

    return jsonify({
        'success': True,
        'statistics': stats
    })


@app.route('/api/cost-over-time')
def get_cost_over_time():
    """Get cost and token usage over time for charts.

    Query params:
        timeframe: day, week, month, all (default: week)
    """
    audit_logger = get_audit_logger()

    timeframe = request.args.get('timeframe', 'week')
    data = audit_logger.get_cost_over_time(timeframe)

    return jsonify({
        'success': True,
        'data': data,
        'timeframe': timeframe
    })


@app.route('/api/sessions')
def get_sessions():
    """Get all refactoring sessions."""
    state_manager = get_refactor_state()
    sessions = state_manager.list_sessions()

    return jsonify({
        'success': True,
        'sessions': sessions,
        'total': len(sessions)
    })


@app.route('/api/session/<session_id>')
def get_session_detail(session_id):
    """Get detailed information for a specific session."""
    state_manager = get_refactor_state()
    session_info = state_manager.get_resume_info(session_id)

    if not session_info:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404

    return jsonify({
        'success': True,
        'session': session_info
    })


@app.route('/api/enhanced-statistics')
def get_enhanced_statistics():
    """Get enhanced statistics including blocked files and sessions.

    Query params:
        timeframe: day, week, month, all (default: all)
    """
    audit_logger = get_audit_logger()
    state_manager = get_refactor_state()

    timeframe = request.args.get('timeframe', 'all')

    # Get basic statistics
    stats = audit_logger.get_statistics_by_timeframe(timeframe)

    # Get blocked files count
    blocked_logs = audit_logger.get_logs_by_status('blocked', limit=10000)
    stats['blocked_files'] = len(blocked_logs)

    # Get session statistics
    sessions = state_manager.list_sessions()
    active_sessions = [s for s in sessions if s.get('can_resume', False)]
    completed_sessions = [s for s in sessions if s.get('percentage', 0) >= 100]

    stats['sessions'] = {
        'total': len(sessions),
        'active': len(active_sessions),
        'completed': len(completed_sessions)
    }

    # Calculate average session progress
    if sessions:
        avg_progress = sum(s.get('percentage', 0) for s in sessions) / len(sessions)
        stats['sessions']['avg_progress'] = round(avg_progress, 1)
    else:
        stats['sessions']['avg_progress'] = 0

    return jsonify({
        'success': True,
        'statistics': stats
    })


@app.route('/api/recent-activity')
def get_recent_activity():
    """Get recent activity summary."""
    audit_logger = get_audit_logger()

    # Get recent logs
    recent_logs = audit_logger.get_recent_logs(limit=10)

    # Group by status
    activity = {
        'recent_refactors': [],
        'recent_blocks': [],
        'recent_errors': []
    }

    for log in recent_logs:
        item = {
            'id': log['id'],
            'timestamp': log['timestamp'],
            'filepath': log['filepath'],
            'action': log['action'],
            'status': log['status'],
            'cost': log.get('cost', 0),
            'tokens': log.get('tokens_used', 0)
        }

        if log['status'] == 'success':
            activity['recent_refactors'].append(item)
        elif log['status'] == 'blocked':
            activity['recent_blocks'].append(item)
        elif log['status'] in ['error', 'failed']:
            activity['recent_errors'].append(item)

    return jsonify({
        'success': True,
        'activity': activity
    })


def run_server(host='127.0.0.1', port=5000, debug=True):
    """Run the Flask development server.

    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    print(f"\n🚀 AI Governance Audit Dashboard")
    print(f"{'=' * 50}")
    print(f"Starting server at http://{host}:{port}")
    print(f"Press Ctrl+C to stop\n")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server()
