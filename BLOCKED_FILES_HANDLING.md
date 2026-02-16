# Blocked Files Handling

## Overview

The codebase refactoring tool now **continues refactoring even when some files are blocked** by security policies. Blocked files are skipped while allowed files are processed normally.

## New Behavior ✅

### What Happens

1. **All files are scanned** for security violations
2. Files are **separated** into:
   - ✅ **Allowed**: Pass security checks
   - 🚫 **Blocked**: Fail security checks (contain sensitive data, etc.)
3. **Refactoring continues** with only the allowed files
4. Blocked files are **logged and reported** but don't stop the process
5. **Summary shows** successful, blocked, and failed files separately

### Example Output

```
[3/8] Running security scans...
  ⚠  2 file(s) blocked by security policy (will be skipped):
    - src/config/secrets.py
    - src/api/credentials.js

  ✓ 18 file(s) passed security checks and will be refactored
  ℹ  2 file(s) will be skipped

[4/8] Refactoring files (with smart context selection)...
  Processing group 1/3 (6 files)...
  Processing group 2/3 (8 files)...
  Processing group 3/3 (4 files)...
  ✓ Successfully refactored 18/20 files

...

======================================================================
REFACTORING SUMMARY
======================================================================
Total files:     20
Successful:      18
Blocked:         2 (security policy)
File groups:     3
Total cost:      $0.1234
Total tokens:    12,345

Blocked Files (skipped):
  • src/config/secrets.py
  • src/api/credentials.js
======================================================================
```

## Benefits

- ✅ **Doesn't fail entire operation** if one file contains secrets
- ✅ **Allows partial refactoring** of safe files
- ✅ **Maintains visibility** of what was skipped
- ✅ **Logs blocked files** to audit trail
- ✅ **Includes in checkpoint/resume** for tracking

## Technical Details

### What Gets Filtered

When files are blocked, the system:

1. **Removes from refactoring queue** - Only allowed files are processed
2. **Filters dependency graph** - Groups and ordering exclude blocked files
3. **Updates checkpoints** - Blocked files marked as failed in session state
4. **Adds to results** - Blocked files included in final summary with `blocked: true`
5. **Logs to audit** - Blocked files logged with `status='blocked'`

### Dependency Handling

If a blocked file is imported by allowed files:
- ✅ The allowed files are still refactored
- ✅ The AI is aware the blocked file exists (from dependency graph)
- ✅ Import statements remain unchanged
- ⚠️  Changes in allowed files won't be reflected in blocked file

### Example Scenario

```python
# File structure:
src/
  ├── utils.py         ✅ ALLOWED
  ├── models.py        ✅ ALLOWED
  ├── services.py      ✅ ALLOWED
  └── secrets.py       🚫 BLOCKED (contains API keys)

# Imports:
# services.py imports from: utils.py, models.py, secrets.py
```

**What happens:**
1. `secrets.py` is scanned and blocked
2. `utils.py`, `models.py`, `services.py` are refactored normally
3. `services.py` keeps its import from `secrets.py` (unchanged)
4. The AI sees that `secrets.py` exists but doesn't modify it
5. Summary shows 3 successful, 1 blocked

## Command Options

All existing options work with blocked files:

```bash
# Full refactoring with some files blocked
ai-governance codebase-refactor src/ \
  --target "modernize code" \
  --enable-testing

# Blocked files are skipped automatically
# Allowed files continue to be processed
```

## Audit Trail

Blocked files are logged:

```bash
ai-governance audit --status blocked

# Shows:
# timestamp | action            | filepath           | status  | reason
# --------- | ----------------- | ------------------ | ------- | ------------------------
# 14:30:22  | codebase_refactor | src/secrets.py     | blocked | Blocked by security policy
# 14:30:22  | codebase_refactor | src/api/creds.js   | blocked | Blocked by security policy
```

## Resume Support

When resuming a session:
- ✅ Blocked files remain in `failed_files` with reason "Blocked by security policy"
- ✅ Not added back to pending queue
- ✅ Shown in progress summary

```bash
ai-governance sessions --list

# Shows:
# Session: refactor_20250216_143022_abc123
# Completed: 18 files
# Failed: 2 files (blocked by security policy)
# Remaining: 0 files
```

## Best Practices

1. **Review blocked files** before refactoring:
   ```bash
   ai-governance scan src/ --show-blocked
   ```

2. **Use custom policies** if default is too strict:
   ```bash
   ai-governance codebase-refactor src/ \
     --policy my-custom-policy.yaml \
     --target "..."
   ```

3. **Check audit logs** after refactoring:
   ```bash
   ai-governance audit --status blocked
   ```

4. **Handle blocked files separately** if needed:
   - Review and sanitize manually
   - Move to secure location
   - Refactor after removing sensitive content

## Migration from Old Behavior

**Before (v1.0):**
- ❌ ANY blocked file stopped entire operation
- ❌ No visibility into what could have been refactored
- ❌ All-or-nothing approach

**Now (v1.1+):**
- ✅ Blocked files are skipped
- ✅ Allowed files continue to be processed
- ✅ Full visibility into what was skipped and why
- ✅ Graceful degradation

## Security Notes

- 🔒 Security policies are still enforced
- 🔒 Sensitive files are NEVER sent to AI
- 🔒 Blocked files cannot be force-processed
- 🔒 All blocks are logged to audit trail
- 🔒 Blocks persist across resume operations
