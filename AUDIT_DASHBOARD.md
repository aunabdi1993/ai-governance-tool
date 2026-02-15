# AI Governance Audit Dashboard

The AI Governance Tool now includes a comprehensive web-based audit dashboard for visualizing and analyzing your refactoring activities.

## Features

### 📊 Visual Analytics
- **Cost tracking over time** - Line charts showing USD costs per day/week/month
- **Token usage trends** - Bar charts tracking token consumption
- **Real-time statistics** - Total requests, tokens, costs, and success rates
- **Time-based filtering** - View data by day, week, month, or all-time

### 🔍 Detailed Audit Logs
- **Comprehensive log table** - View all refactoring requests with timestamps
- **Status filtering** - Filter by success, blocked, error, or allowed
- **Code diff visualization** - Side-by-side comparison of original vs refactored code
- **Security findings** - Review all security policy violations

### 📝 Request Details
- View original code before refactoring (stored as text)
- View approved refactored code (stored as text)
- Token usage breakdown (input/output tokens)
- Exact cost calculation in USD
- Model used (e.g., claude-sonnet-4-5-20250929)
- Refactoring target description
- Security scan results and findings

## Quick Start

### 1. Launch the Dashboard

```bash
ai-governance dashboard
```

This will start the web server at `http://127.0.0.1:5000`

### 2. Custom Host/Port

```bash
ai-governance dashboard --port 8080
ai-governance dashboard --host 0.0.0.0 --port 3000
```

### 3. Production Mode

```bash
ai-governance dashboard --no-debug
```

## Dashboard Interface

### Main View
The dashboard opens to a comprehensive overview showing:

1. **Header** - Title and description
2. **Filters** - Time period and status filters
3. **Statistics Cards** - Key metrics at a glance
   - Total Requests
   - Total Tokens Used
   - Total Cost (USD)
   - Successful Refactorings
4. **Charts** - Visual trends over time
   - Cost Over Time (line chart)
   - Token Usage Over Time (bar chart)
5. **Audit Log Table** - Recent requests with details

### Detail Modal
Click any log entry to view:
- Full request metadata
- Original code (before refactoring)
- Refactored code (after AI processing)
- Side-by-side diff view
- Security findings (if any)
- Complete token and cost breakdown

## API Endpoints

The dashboard provides a REST API for programmatic access:

### Get Logs
```
GET /api/logs?timeframe=week&status=success&limit=100
```

**Parameters:**
- `timeframe`: day, week, month, all (default: all)
- `status`: success, blocked, error, allowed
- `limit`: max records to return (default: 100)

**Response:**
```json
{
  "success": true,
  "logs": [...],
  "count": 42
}
```

### Get Log Detail
```
GET /api/log/<id>
```

**Response:**
```json
{
  "success": true,
  "log": {
    "id": 123,
    "timestamp": "2026-02-15T10:30:00",
    "filepath": "/path/to/file.py",
    "action": "refactor",
    "status": "success",
    "original_code": "...",
    "refactored_code": "...",
    "tokens_used": 2500,
    "cost": 0.0525,
    "model": "claude-sonnet-4-5-20250929",
    ...
  }
}
```

### Get Statistics
```
GET /api/statistics?timeframe=month
```

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_requests": 150,
    "total_tokens": 125000,
    "total_cost": 2.625,
    "status_counts": {
      "success": 120,
      "blocked": 20,
      "error": 10
    }
  }
}
```

### Get Cost Over Time
```
GET /api/cost-over-time?timeframe=week
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "2026-02-08",
      "cost": 0.15,
      "tokens": 5000,
      "requests": 10
    },
    ...
  ]
}
```

## Database Schema

The audit log database (`.ai-governance-audit.db`) stores:

### audit_log Table
```sql
CREATE TABLE audit_log (
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
    target_description TEXT,
    original_code TEXT,         -- NEW: Full original code
    refactored_code TEXT        -- NEW: Full refactored code
);
```

### Migration
The system automatically migrates existing databases by adding the new `original_code` and `refactored_code` columns if they don't exist.

## Usage Tips

### 1. Monitor Costs
Use the dashboard to track spending over time and identify expensive refactoring operations.

### 2. Audit Security
Review blocked requests to ensure security policies are working correctly.

### 3. Review Changes
Use the side-by-side code diff to verify AI refactorings before applying them to your codebase.

### 4. Analyze Patterns
Look for trends in token usage to optimize prompt engineering and target descriptions.

### 5. Export Data
Use the API endpoints to export audit data for further analysis or compliance reporting.

## Troubleshooting

### Flask not installed
```bash
pip install flask
```

### Port already in use
```bash
ai-governance dashboard --port 8080
```

### Database not found
The dashboard will create `.ai-governance-audit.db` automatically in the current directory if it doesn't exist.

### No data showing
Run some refactoring operations first:
```bash
ai-governance refactor myfile.py --target "modernize code"
```

## Security Considerations

1. **Local only by default** - The dashboard binds to `127.0.0.1` (localhost) by default
2. **Code storage** - Original and refactored code is stored in SQLite locally
3. **No authentication** - The dashboard has no built-in auth; use firewall rules if exposing externally
4. **Sensitive data** - Audit logs may contain code snippets; secure the `.ai-governance-audit.db` file appropriately

## Examples

### View last 24 hours of activity
1. Launch dashboard: `ai-governance dashboard`
2. Select "Last 24 Hours" from timeframe dropdown
3. Click "Refresh"

### Find all blocked requests
1. Launch dashboard
2. Select "Blocked" from status filter
3. Click any entry to see why it was blocked

### Track weekly spending
1. Select "Last Week" timeframe
2. View the "Total Cost" card
3. Check the "Cost Over Time" chart for daily breakdown

## Development

The dashboard is built with:
- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript + Chart.js
- **Database**: SQLite3
- **UI**: Modern CSS with responsive design

To customize:
- Templates: `ai_governance/templates/dashboard.html`
- API: `ai_governance/web_ui.py`
- Database: `ai_governance/audit_logger.py`

## Support

For issues or feature requests, please check the main project documentation or open an issue on the project repository.
