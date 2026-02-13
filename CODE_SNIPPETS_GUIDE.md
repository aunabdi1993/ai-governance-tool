# Code Snippets & Execution Flow Guide

## 1. SINGLE-FILE REFACTORING EXECUTION TRACE

### Entry Point: CLI refactor command
**File**: `cli.py:153-318`

```python
@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--target', '-t', required=True, ...)
@click.option('--policy', '-p', type=click.Path(exists=True), ...)
@click.option('--no-backup', is_flag=True, ...)
@click.option('--dry-run', is_flag=True, ...)
@click.option('--apply', is_flag=True, ...)
def refactor(filepath, target, policy, no_backup, dry_run, apply):
    """Refactor a file using AI with security controls."""
```

### Step 1: Component Initialization (lines 162-170)

```python
try:
    policy_engine = PolicyEngine(policy)
    scanner = Scanner(policy_engine)
    audit_logger = AuditLogger()
    diff_manager = DiffManager(create_backups=not no_backup)
except Exception as e:
    click.echo(f"{Fore.RED}Error initializing components: {e}{Style.RESET_ALL}")
    return
```

**What happens**:
- `PolicyEngine(policy)` loads YAML file from `policy` or default `profiles/default-secure.yaml`
- Compiles regex patterns from policy into `compiled_patterns` dict
- Returns policy metadata, blocked file patterns, sensitive patterns

### Step 2: Display Policy Info (lines 173-175)

```python
policy_info = policy_engine.get_policy_info()
click.echo(f"{Fore.YELLOW}Policy: {policy_info['name']} (v{policy_info['version']}){Style.RESET_ALL}")
click.echo(f"Description: {policy_info['description']}\n")
```

**Output**:
```
Policy: default-secure (v1.0)
Description: Default security profile blocking sensitive files and patterns
```

### Step 3: Security Scan (lines 178-215)

```python
click.echo(f"{Fore.CYAN}Scanning file: {filepath}{Style.RESET_ALL}")
scan_result = scanner.scan_file(filepath)
```

**scanner.scan_file() in detail** (scanner.py:19-124):

```python
def scan_file(self, filepath: str) -> Dict:
    file_path = Path(filepath)
    
    # Check 1: File exists?
    if not file_path.exists():
        return {'allowed': False, 'reason': f"File not found: {filepath}", 
                'findings': [], 'file_size': 0, 'error': True}
    
    # Check 2: Is it a file?
    if not file_path.is_file():
        return {'allowed': False, 'reason': f"Not a file: {filepath}",
                'findings': [], 'file_size': 0, 'error': True}
    
    file_size = file_path.stat().st_size
    
    # Check 3: File path pattern blocked?
    is_blocked, block_reason = self.policy_engine.is_file_blocked(str(file_path))
    if is_blocked:
        return {'allowed': False, 'reason': block_reason, 'findings': [],
                'file_size': file_size, 'error': False}
    
    # Check 4: Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return {'allowed': False, 'reason': "File is not a valid text file",
                'findings': [], 'file_size': file_size, 'error': True}
    
    # Check 5: Scan content for sensitive patterns
    findings = self.policy_engine.scan_content(content)
    
    if findings:
        # Build detailed reason
        critical_findings = [f for f in findings if f['severity'] == 'critical']
        high_findings = [f for f in findings if f['severity'] == 'high']
        
        reason_parts = []
        if critical_findings:
            patterns = ', '.join([f['pattern'] for f in critical_findings])
            reason_parts.append(f"Critical: {patterns}")
        if high_findings:
            patterns = ', '.join([f['pattern'] for f in high_findings])
            reason_parts.append(f"High: {patterns}")
        
        reason = "Sensitive content detected - " + "; ".join(reason_parts)
        
        return {
            'allowed': False,
            'reason': reason,
            'findings': findings,
            'file_size': file_size,
            'error': False,
            'content': content
        }
    
    # All checks passed
    return {
        'allowed': True,
        'reason': "No policy violations detected",
        'findings': [],
        'file_size': file_size,
        'error': False,
        'content': content
    }
```

### Step 4: Check Scan Results (lines 182-215)

```python
if scan_result.get('error'):
    click.echo(f"\n{Fore.RED}❌ ERROR: {scan_result['reason']}{Style.RESET_ALL}")
    audit_logger.log_action(filepath=filepath, action='refactor', status='error',
                            reason=scan_result['reason'])
    return

if not scan_result['allowed']:
    click.echo(f"\n{Fore.RED}🚫 BLOCKED: {scan_result['reason']}{Style.RESET_ALL}")
    click.echo(f"File size: {scan_result['file_size']} bytes\n")
    
    if scan_result['findings']:
        click.echo(f"{Fore.YELLOW}Sensitive patterns detected:{Style.RESET_ALL}")
        for finding in scan_result['findings']:
            click.echo(f"  • {Fore.RED}{finding['pattern']}{Style.RESET_ALL} "
                      f"({finding['severity']}): {finding['description']}")
            click.echo(f"    Matches: {finding['match_count']}, "
                      f"Examples: {', '.join(finding['examples'])}")
    
    audit_logger.log_action(filepath=filepath, action='refactor', status='blocked',
                            reason=scan_result['reason'], findings=scan_result['findings'],
                            target_description=target)
    return
```

**Output if blocked**:
```
🚫 BLOCKED: Sensitive content detected - Critical: aws_keys, credit_cards
File size: 1234 bytes

Sensitive patterns detected:
  • aws_keys (critical): AWS access keys
    Matches: 1, Examples: AKIA0000000000000000
  • credit_cards (critical): Credit card numbers
    Matches: 1, Examples: 4532-1234-5678-9010
```

### Step 5: File Passed Security (lines 218-219)

```python
click.echo(f"\n{Fore.GREEN}✅ PASSED: {scan_result['reason']}{Style.RESET_ALL}")
click.echo(f"File size: {scan_result['file_size']} bytes")
```

### Step 6: Handle Dry-Run (lines 221-229)

```python
if dry_run:
    click.echo(f"\n{Fore.YELLOW}Dry run mode - stopping before refactoring{Style.RESET_ALL}")
    audit_logger.log_action(filepath=filepath, action='scan', status='allowed',
                            reason=scan_result['reason'])
    return
```

### Step 7: Ensure API Key (lines 232-234)

```python
if not ensure_api_key():
    click.echo(f"\n{Fore.RED}Cannot proceed without API key{Style.RESET_ALL}")
    return
```

**ensure_api_key() logic** (cli.py:31-107):
1. Check if `ANTHROPIC_API_KEY` env var is set
2. If not, display warning and prompt user
3. Hide input for security
4. Ask where to save: global (~/.config/ai-governance/.env), local (./.env), or session only
5. Save if user chooses

### Step 8: Cost Estimation (lines 244-247)

```python
click.echo(f"\n{Fore.CYAN}Refactoring with AI...{Style.RESET_ALL}")
click.echo(f"Target: {target}")

ai_client = AIClient()
click.echo(f"Model: {ai_client.model}\n")

# Estimate cost first
estimate = ai_client.estimate_cost(scan_result['content'], target)
click.echo(f"{Fore.YELLOW}Estimated cost: ${estimate['estimated_cost']:.4f}{Style.RESET_ALL}")
click.echo(f"Estimated tokens: ~{estimate['estimated_total_tokens']}\n")
```

**estimate_cost() logic** (ai_client.py:206-230):
```python
def estimate_cost(self, code: str, target_description: str) -> Dict:
    # Rough estimation: ~4 characters per token
    estimated_input_tokens = len(code + target_description) // 4
    estimated_output_tokens = len(code) // 4  # Assume similar length output
    
    estimated_cost = self._calculate_cost(
        estimated_input_tokens,
        estimated_output_tokens
    )
    
    return {
        'estimated_input_tokens': estimated_input_tokens,
        'estimated_output_tokens': estimated_output_tokens,
        'estimated_total_tokens': estimated_input_tokens + estimated_output_tokens,
        'estimated_cost': estimated_cost
    }
```

### Step 9: Call AI for Refactoring (lines 250-266)

```python
result = ai_client.refactor_code(
    code=scan_result['content'],
    target_description=target,
    filepath=filepath
)

if not result['success']:
    click.echo(f"{Fore.RED}Error during refactoring: {result['error']}{Style.RESET_ALL}")
    audit_logger.log_action(filepath=filepath, action='refactor', status='error',
                            reason=result['error'], target_description=target,
                            model=result['model'])
    return
```

**refactor_code() logic** (ai_client.py:32-101):
```python
def refactor_code(self, code: str, target_description: str, filepath: str) -> Dict:
    try:
        # Build prompt
        prompt = self._build_refactor_prompt(code, target_description, filepath)
        
        # Call Claude API
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract refactored code
        refactored_code = message.content[0].text
        
        # Calculate tokens and cost
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        total_tokens = input_tokens + output_tokens
        
        cost = self._calculate_cost(input_tokens, output_tokens)
        
        return {
            'success': True,
            'refactored_code': refactored_code,
            'tokens_used': {
                'input': input_tokens,
                'output': output_tokens,
                'total': total_tokens
            },
            'cost': cost,
            'model': self.model
        }
    
    except Exception as e:
        error_message = self._parse_api_error(e)
        return {
            'success': False,
            'error': error_message,
            'tokens_used': {'input': 0, 'output': 0, 'total': 0},
            'cost': 0.0,
            'model': self.model
        }
```

**Refactoring Prompt** (ai_client.py:154-189):
```python
prompt = f"""You are an expert code refactoring assistant. Your task is to refactor 
the provided code according to the specified requirements.

Source File: {filepath}
Refactoring Goal: {target_description}

Original Code:
```
{code}
```

Please refactor this code according to the goal. Follow these guidelines:
1. Preserve all functionality while improving code quality
2. Apply modern best practices and patterns
3. Improve readability and maintainability
4. Add appropriate comments where helpful
5. Ensure the refactored code is production-ready

Provide ONLY the refactored code in your response, without explanations or 
markdown code blocks unless they are part of the code itself."""
```

### Step 10: Display Results (lines 269-284)

```python
click.echo(f"{Fore.GREEN}✅ Refactoring completed!{Style.RESET_ALL}\n")
click.echo(f"{Fore.YELLOW}Tokens used: {result['tokens_used']['total']}{Style.RESET_ALL}")
click.echo(f"  Input:  {result['tokens_used']['input']}")
click.echo(f"  Output: {result['tokens_used']['output']}")
click.echo(f"{Fore.YELLOW}Actual cost: ${result['cost']:.6f}{Style.RESET_ALL}\n")

# Show diff
diff_manager.display_diff(
    original=scan_result['content'],
    refactored=result['refactored_code'],
    filepath=filepath
)

# Show stats
stats = diff_manager.get_stats(scan_result['content'], result['refactored_code'])
diff_manager.display_stats(stats)
```

**get_stats() logic** (diff_manager.py:132-161):
```python
def get_stats(self, original: str, refactored: str) -> dict:
    original_lines = original.splitlines()
    refactored_lines = refactored.splitlines()
    
    # Count changes
    diff = list(difflib.unified_diff(
        original_lines,
        refactored_lines,
        lineterm=''
    ))
    
    additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
    
    return {
        'original_lines': len(original_lines),
        'refactored_lines': len(refactored_lines),
        'lines_added': additions,
        'lines_removed': deletions,
        'net_change': len(refactored_lines) - len(original_lines)
    }
```

### Step 11: Audit Log (lines 287-296)

```python
audit_logger.log_action(
    filepath=filepath,
    action='refactor',
    status='success',
    reason='Refactoring completed successfully',
    tokens_used=result['tokens_used']['total'],
    cost=result['cost'],
    model=result['model'],
    target_description=target
)
```

**log_action() stores to SQLite** (audit_logger.py:48-110):
```python
def log_action(self, filepath: str, action: str, status: str, 
               reason: Optional[str] = None, tokens_used: int = 0,
               cost: float = 0.0, findings: Optional[List[Dict]] = None,
               model: Optional[str] = None, 
               target_description: Optional[str] = None) -> int:
    
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
        timestamp, filepath, action, status, reason,
        tokens_used, cost, findings_str, model, target_description
    ))
    
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return row_id
```

### Step 12: Confirm & Apply Changes (lines 299-312)

```python
if apply or click.confirm(f"\n{Fore.CYAN}Apply changes to {filepath}?{Style.RESET_ALL}"):
    # Create backup
    if not no_backup:
        backup_path = diff_manager.create_backup(filepath)
        if backup_path:
            click.echo(f"{Fore.GREEN}Backup created: {backup_path}{Style.RESET_ALL}")
    
    # Save refactored code
    if diff_manager.save_refactored(filepath, result['refactored_code']):
        click.echo(f"{Fore.GREEN}✅ Changes applied to {filepath}{Style.RESET_ALL}")
    else:
        click.echo(f"{Fore.RED}❌ Failed to save changes{Style.RESET_ALL}")
else:
    click.echo(f"{Fore.YELLOW}Changes not applied{Style.RESET_ALL}")
```

**create_backup() logic** (diff_manager.py:25-46):
```python
def create_backup(self, filepath: str) -> Optional[str]:
    if not self.create_backups:
        return None
    
    file_path = Path(filepath)
    if not file_path.exists():
        return None
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"
    
    shutil.copy2(file_path, backup_path)
    return str(backup_path)
```

**save_refactored() logic** (diff_manager.py:183-199):
```python
def save_refactored(self, filepath: str, refactored_code: str) -> bool:
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(refactored_code)
        return True
    except Exception as e:
        print(f"{Fore.RED}Error saving file: {e}{Style.RESET_ALL}")
        return False
```

---

## 2. POLICY ENGINE SECURITY SCANNING

### Load Policy (policy_engine.py:37-45)

```python
def _load_policy(self) -> Dict:
    """Load policy from YAML file."""
    if not self.policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {self.policy_path}")
    
    with open(self.policy_path, 'r') as f:
        policy = yaml.safe_load(f)
    
    return policy
```

### Compile Patterns (policy_engine.py:47-59)

```python
def _compile_patterns(self):
    """Compile regex patterns for efficient matching."""
    self.compiled_patterns = {}
    
    for pattern_name, pattern_info in self.policy.get('sensitive_patterns', {}).items():
        try:
            self.compiled_patterns[pattern_name] = {
                'regex': re.compile(pattern_info['pattern'], re.IGNORECASE),
                'description': pattern_info['description'],
                'severity': pattern_info.get('severity', 'medium')
            }
        except re.error as e:
            print(f"Warning: Invalid regex pattern for {pattern_name}: {e}")
```

### Check File Path Blocked (policy_engine.py:61-76)

```python
def is_file_blocked(self, filepath: str) -> Tuple[bool, Optional[str]]:
    """Check if a file path matches any blocked patterns."""
    blocked_patterns = self.policy.get('blocked_file_patterns', [])
    
    for pattern in blocked_patterns:
        if fnmatch(filepath, pattern):
            return True, f"File path matches blocked pattern: {pattern}"
    
    return False, None
```

### Scan Content (policy_engine.py:78-107)

```python
def scan_content(self, content: str) -> List[Dict]:
    """Scan content for sensitive patterns."""
    findings = []
    
    for pattern_name, pattern_data in self.compiled_patterns.items():
        matches = pattern_data['regex'].findall(content)
        
        if matches:
            # Redact matches for logging
            redacted_matches = [
                match[:10] + "..." if len(match) > 10 else match
                for match in matches[:3]  # Show max 3 examples
            ]
            
            findings.append({
                'pattern': pattern_name,
                'description': pattern_data['description'],
                'severity': pattern_data['severity'],
                'match_count': len(matches),
                'examples': redacted_matches
            })
    
    return findings
```

---

## 3. AUDIT LOGGER QUERYING

### Get Statistics (audit_logger.py:162-205)

```python
def get_statistics(self) -> Dict:
    """Get audit statistics."""
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
```

---

## 4. ERROR HANDLING

### API Error Parsing (ai_client.py:103-152)

```python
def _parse_api_error(self, error: Exception) -> str:
    """Parse API errors into user-friendly messages."""
    error_str = str(error)
    
    if 'rate_limit_error' in error_str or '429' in error_str:
        return (
            "Rate limit exceeded. You're making requests too quickly. "
            "Please wait a moment and try again."
        )
    
    elif 'insufficient_quota' in error_str or 'quota' in error_str.lower():
        return (
            "API quota exceeded. Your account has run out of credits. "
            "Please check your usage at https://console.anthropic.com/"
        )
    
    elif 'invalid_api_key' in error_str or 'authentication_error' in error_str:
        return (
            "Invalid API key. Please check your API key is correct. "
            "Run 'ai-governance init' to reconfigure."
        )
    
    # ... more error types
    
    return f"API error: {error_str}"
```

---

## 5. DIFFERENTIAL DISPLAY

### Generate Diff (diff_manager.py:48-81)

```python
def generate_diff(self, original: str, refactored: str,
                  filepath: str, colored: bool = True) -> str:
    """Generate a diff between original and refactored code."""
    original_lines = original.splitlines(keepends=True)
    refactored_lines = refactored.splitlines(keepends=True)
    
    # Generate unified diff
    diff = difflib.unified_diff(
        original_lines,
        refactored_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm=''
    )
    
    if colored:
        return self._colorize_diff(list(diff))
    else:
        return ''.join(diff)
```

### Colorize Diff (diff_manager.py:83-106)

```python
def _colorize_diff(self, diff_lines: list) -> str:
    """Add colors to diff output."""
    colored_lines = []
    
    for line in diff_lines:
        if line.startswith('+++') or line.startswith('---'):
            colored_lines.append(Fore.CYAN + Style.BRIGHT + line)
        elif line.startswith('@@'):
            colored_lines.append(Fore.MAGENTA + Style.BRIGHT + line)
        elif line.startswith('+'):
            colored_lines.append(Fore.GREEN + line)
        elif line.startswith('-'):
            colored_lines.append(Fore.RED + line)
        else:
            colored_lines.append(line)
    
    return '\n'.join(colored_lines)
```

---

## SUMMARY: Component Interaction Map

```
CLI (cli.py:refactor)
  ├─ Creates: PolicyEngine(policy)
  │   └─ Loads: profiles/default-secure.yaml
  │   └─ Compiles: regex patterns
  │
  ├─ Creates: Scanner(policy_engine)
  │   └─ Uses: policy_engine.is_file_blocked()
  │   └─ Uses: policy_engine.scan_content()
  │
  ├─ Creates: AIClient()
  │   └─ Initializes: Anthropic client with API key
  │   └─ Model: claude-sonnet-4-5-20250929
  │
  ├─ Creates: DiffManager()
  │   └─ Methods: create_backup(), save_refactored(), display_diff()
  │
  ├─ Creates: AuditLogger()
  │   └─ Database: .ai-governance-audit.db
  │   └─ Methods: log_action(), get_statistics()
  │
  ├─ Calls: scanner.scan_file(filepath)
  │   ├─ Returns: {allowed, reason, findings, file_size, error, content}
  │   └─ If blocked: logs and stops
  │
  ├─ Calls: ai_client.refactor_code()
  │   ├─ Builds prompt with filepath, target, code
  │   ├─ Calls Claude API
  │   └─ Returns: {success, refactored_code, tokens_used, cost}
  │
  ├─ Calls: diff_manager methods
  │   ├─ display_diff()
  │   ├─ get_stats()
  │   ├─ create_backup()
  │   └─ save_refactored()
  │
  └─ Calls: audit_logger.log_action()
     └─ Inserts into SQLite database
```

