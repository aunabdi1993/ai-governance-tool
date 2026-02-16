"""Manages refactoring state for resumability and incremental progress."""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import click
from colorama import Fore, Style


class RefactorState:
    """Tracks refactoring progress for resumability."""

    def __init__(self, state_dir: str = ".ai_governance_state"):
        """
        Initialize state manager.

        Args:
            state_dir: Directory to store state files
        """
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)

    def save_checkpoint(
        self,
        session_id: str,
        completed_files: List[str],
        failed_files: Dict[str, str],
        pending_files: List[str],
        target: str,
        dep_graph: Dict,
        refactor_results: Dict[str, Dict],
        metadata: Optional[Dict] = None
    ):
        """
        Save current refactoring state as a checkpoint.

        Args:
            session_id: Unique session identifier
            completed_files: Files successfully refactored
            failed_files: Dict of {file_path: error_message}
            pending_files: Files not yet processed
            target: Refactoring goal description
            dep_graph: Dependency graph
            refactor_results: Results from completed refactorings
            metadata: Additional metadata to store
        """
        state = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'completed': completed_files,
            'failed': failed_files,
            'pending': pending_files,
            'target': target,
            'dependency_graph': self._serialize_dep_graph(dep_graph),
            'progress': {
                'total': len(completed_files) + len(failed_files) + len(pending_files),
                'completed': len(completed_files),
                'failed': len(failed_files),
                'pending': len(pending_files),
                'percentage': self._calculate_percentage(
                    len(completed_files),
                    len(completed_files) + len(failed_files) + len(pending_files)
                )
            },
            'results_summary': self._summarize_results(refactor_results),
            'metadata': metadata or {}
        }

        state_file = self.state_dir / f"{session_id}.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_checkpoint(self, session_id: str) -> Optional[Dict]:
        """
        Load previous refactoring state.

        Args:
            session_id: Session identifier

        Returns:
            State dict or None if not found
        """
        state_file = self.state_dir / f"{session_id}.json"
        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            return json.load(f)

    def list_sessions(self) -> List[Dict]:
        """
        List all saved refactoring sessions.

        Returns:
            List of session summaries
        """
        sessions = []
        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    progress = state.get('progress', {})

                    sessions.append({
                        'session_id': state['session_id'],
                        'timestamp': state['timestamp'],
                        'target': state.get('target', 'Unknown'),
                        'progress': f"{progress.get('completed', 0)}/{progress.get('total', 0)} files",
                        'percentage': progress.get('percentage', 0),
                        'failed': progress.get('failed', 0),
                        'can_resume': progress.get('pending', 0) > 0
                    })
            except Exception:
                # Skip corrupted state files
                continue

        return sorted(sessions, key=lambda x: x['timestamp'], reverse=True)

    def display_sessions(self):
        """Display all available sessions in a user-friendly format."""
        sessions = self.list_sessions()

        if not sessions:
            click.echo(f"\n{Fore.YELLOW}No saved refactoring sessions found{Style.RESET_ALL}\n")
            return

        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Saved Refactoring Sessions{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

        for i, session in enumerate(sessions, 1):
            # Format timestamp
            try:
                dt = datetime.fromisoformat(session['timestamp'])
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = session['timestamp']

            # Progress bar
            percentage = session.get('percentage', 0)
            bar_length = 30
            filled = int(bar_length * percentage / 100)
            bar = '█' * filled + '░' * (bar_length - filled)

            # Color code by status
            if percentage >= 100:
                status_color = Fore.GREEN
                status = "COMPLETED"
            elif session.get('failed', 0) > 0:
                status_color = Fore.RED
                status = "HAS FAILURES"
            elif session.get('can_resume', False):
                status_color = Fore.YELLOW
                status = "IN PROGRESS"
            else:
                status_color = Fore.WHITE
                status = "UNKNOWN"

            click.echo(f"{i}. {Fore.CYAN}{session['session_id'][:20]}{Style.RESET_ALL}")
            click.echo(f"   {time_str}")
            click.echo(f"   Target: {session.get('target', 'N/A')[:50]}")
            click.echo(f"   Progress: {bar} {percentage:.1f}%")
            click.echo(f"   Status: {status_color}{status}{Style.RESET_ALL} ({session['progress']})")

            if session.get('failed', 0) > 0:
                click.echo(f"   {Fore.RED}Failed: {session['failed']} file(s){Style.RESET_ALL}")

            if session.get('can_resume', False):
                click.echo(f"   {Fore.GREEN}→ Can resume this session{Style.RESET_ALL}")

            click.echo()

    def delete_checkpoint(self, session_id: str) -> bool:
        """
        Delete a checkpoint.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        state_file = self.state_dir / f"{session_id}.json"
        if state_file.exists():
            state_file.unlink()
            return True
        return False

    def clean_old_checkpoints(self, days: int = 30) -> int:
        """
        Delete checkpoints older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of checkpoints deleted
        """
        deleted = 0
        cutoff = datetime.now().timestamp() - (days * 86400)

        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    timestamp = datetime.fromisoformat(state['timestamp']).timestamp()

                    if timestamp < cutoff:
                        state_file.unlink()
                        deleted += 1
            except Exception:
                continue

        return deleted

    def generate_session_id(self, file_paths: List[str], target: str) -> str:
        """
        Generate a unique session ID based on files and target.

        Args:
            file_paths: List of files being refactored
            target: Refactoring goal

        Returns:
            Unique session identifier
        """
        # Create hash of file paths + target + timestamp
        content = ''.join(sorted(file_paths)) + target + datetime.now().isoformat()
        hash_obj = hashlib.md5(content.encode())
        hash_hex = hash_obj.hexdigest()[:12]

        # Create readable ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"refactor_{timestamp}_{hash_hex}"

    def can_resume(self, session_id: str) -> bool:
        """
        Check if a session can be resumed.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists and has pending files
        """
        state = self.load_checkpoint(session_id)
        if not state:
            return False

        pending = state.get('pending', [])
        return len(pending) > 0

    def get_resume_info(self, session_id: str) -> Optional[Dict]:
        """
        Get information needed to resume a session.

        Args:
            session_id: Session identifier

        Returns:
            Dict with resume info or None
        """
        state = self.load_checkpoint(session_id)
        if not state:
            return None

        return {
            'session_id': session_id,
            'target': state.get('target'),
            'pending_files': state.get('pending', []),
            'completed_files': state.get('completed', []),
            'failed_files': state.get('failed', {}),
            'dependency_graph': state.get('dependency_graph'),
            'progress': state.get('progress', {})
        }

    def _serialize_dep_graph(self, dep_graph: Dict) -> Dict:
        """Serialize dependency graph for JSON storage."""
        # Remove non-serializable objects
        serialized = {}

        for key, value in dep_graph.items():
            if key == 'call_graph':
                # Simplify call graph to just counts
                serialized[key] = {
                    'hot_spots': value.get('hot_spots', [])[:5],
                    'caller_count': len(value.get('callers', {}))
                }
            else:
                serialized[key] = value

        return serialized

    def _summarize_results(self, refactor_results: Dict[str, Dict]) -> Dict:
        """Create a summary of refactoring results."""
        total_tokens = 0
        total_cost = 0.0

        for result in refactor_results.values():
            if result.get('success'):
                tokens = result.get('tokens_used', {})
                total_tokens += tokens.get('total', 0)
                total_cost += result.get('cost', 0.0)

        return {
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'successful_count': sum(1 for r in refactor_results.values() if r.get('success'))
        }

    def _calculate_percentage(self, completed: int, total: int) -> float:
        """Calculate completion percentage."""
        if total == 0:
            return 0.0
        return round((completed / total) * 100, 1)

    def mark_file_completed(self, session_id: str, file_path: str, result: Dict):
        """
        Mark a file as completed in an existing checkpoint.

        Args:
            session_id: Session identifier
            file_path: File that was completed
            result: Refactoring result
        """
        state = self.load_checkpoint(session_id)
        if not state:
            return

        # Move from pending to completed
        if file_path in state.get('pending', []):
            state['pending'].remove(file_path)
            state['completed'].append(file_path)

            # Update progress
            state['progress']['completed'] = len(state['completed'])
            state['progress']['pending'] = len(state['pending'])
            state['progress']['percentage'] = self._calculate_percentage(
                len(state['completed']),
                state['progress']['total']
            )

            # Save updated state
            state_file = self.state_dir / f"{session_id}.json"
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)

    def mark_file_failed(self, session_id: str, file_path: str, error: str):
        """
        Mark a file as failed in an existing checkpoint.

        Args:
            session_id: Session identifier
            file_path: File that failed
            error: Error message
        """
        state = self.load_checkpoint(session_id)
        if not state:
            return

        # Move from pending to failed
        if file_path in state.get('pending', []):
            state['pending'].remove(file_path)
            state['failed'][file_path] = error

            # Update progress
            state['progress']['failed'] = len(state['failed'])
            state['progress']['pending'] = len(state['pending'])

            # Save updated state
            state_file = self.state_dir / f"{session_id}.json"
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
