"""Audit logger for tracking all AI governance actions."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict


class AuditLogger:
    """Logs all governance actions to SQLite database."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize audit logger.

        Args:
            db_path: Path to SQLite database. Defaults to .ai-governance-audit.db
        """
        if db_path is None:
            db_path = Path.cwd() / ".ai-governance-audit.db"

        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filepath TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                reason TEXT,
                tokens_used INTEGER DEFAULT 0,
                cost REAL DEFAULT 0.0,
                findings TEXT,
                model TEXT,
                target_description TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def log_action(
        self,
        filepath: str,
        action: str,
        status: str,
        reason: Optional[str] = None,
        tokens_used: int = 0,
        cost: float = 0.0,
        findings: Optional[List[Dict]] = None,
        model: Optional[str] = None,
        target_description: Optional[str] = None
    ) -> int:
        """Log an action to the audit database.

        Args:
            filepath: Path to file being processed
            action: Action type (refactor, scan, init, audit)
            status: Status (allowed, blocked, error, success)
            reason: Reason for status
            tokens_used: Number of tokens used
            cost: Cost in USD
            findings: List of security findings
            model: AI model used
            target_description: Refactoring target description

        Returns:
            Row ID of inserted record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.utcnow().isoformat()

        # Convert findings to string for storage
        findings_str = None
        if findings:
            findings_str = "; ".join([
                f"{f['pattern']}({f['severity']}): {f['match_count']} matches"
                for f in findings
            ])

        cursor.execute('''
            INSERT INTO audit_log
            (timestamp, filepath, action, status, reason, tokens_used, cost, findings, model, target_description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            filepath,
            action,
            status,
            reason,
            tokens_used,
            cost,
            findings_str,
            model,
            target_description
        ))

        row_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return row_id

    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent audit logs.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of audit log records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM audit_log
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_logs_by_status(self, status: str, limit: int = 50) -> List[Dict]:
        """Get logs filtered by status.

        Args:
            status: Status to filter by
            limit: Maximum number of records to return

        Returns:
            List of audit log records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM audit_log
            WHERE status = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (status, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_statistics(self) -> Dict:
        """Get audit statistics.

        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total counts by status
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM audit_log
            GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())

        # Total cost and tokens
        cursor.execute('''
            SELECT
                SUM(tokens_used) as total_tokens,
                SUM(cost) as total_cost,
                COUNT(*) as total_requests
            FROM audit_log
        ''')
        totals = cursor.fetchone()

        # Recent activity (last 24 hours)
        cursor.execute('''
            SELECT COUNT(*) as recent_count
            FROM audit_log
            WHERE datetime(timestamp) > datetime('now', '-1 day')
        ''')
        recent = cursor.fetchone()

        conn.close()

        return {
            'total_requests': totals[2] or 0,
            'total_tokens': totals[0] or 0,
            'total_cost': round(totals[1] or 0, 4),
            'status_counts': status_counts,
            'recent_24h': recent[0] or 0
        }

    def format_log_entry(self, entry: Dict) -> str:
        """Format a log entry for display.

        Args:
            entry: Log entry dictionary

        Returns:
            Formatted string
        """
        lines = []
        lines.append(f"\n[{entry['timestamp']}] ID: {entry['id']}")
        lines.append(f"File: {entry['filepath']}")
        lines.append(f"Action: {entry['action']} | Status: {entry['status']}")

        if entry.get('reason'):
            lines.append(f"Reason: {entry['reason']}")

        if entry.get('findings'):
            lines.append(f"Findings: {entry['findings']}")

        if entry.get('tokens_used'):
            lines.append(f"Tokens: {entry['tokens_used']} | Cost: ${entry['cost']:.4f}")

        if entry.get('model'):
            lines.append(f"Model: {entry['model']}")

        if entry.get('target_description'):
            lines.append(f"Target: {entry['target_description']}")

        return "\n".join(lines)
