"""Web UI for AI Governance Tool Audit Dashboard."""

from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json
from .audit_logger import AuditLogger

app = Flask(__name__,
    template_folder='templates',
    static_folder='static')


def get_audit_logger():
    """Get audit logger instance."""
    return AuditLogger()


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/logs')
def get_logs():
    """Get audit logs with optional filtering.

    Query params:
        timeframe: day, week, month, all (default: all)
        status: filter by status
        limit: max records to return (default: 100)
    """
    audit_logger = get_audit_logger()

    timeframe = request.args.get('timeframe', 'all')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 100))

    if status:
        logs = audit_logger.get_logs_by_status(status, limit)
    else:
        logs = audit_logger.get_logs_by_timeframe(timeframe, limit)

    return jsonify({
        'success': True,
        'logs': logs,
        'count': len(logs)
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
