#!/usr/bin/env python3
"""
Demo script for AI Governance Tool
Demonstrates security controls by scanning all demo files
"""

import os
from pathlib import Path
from colorama import Fore, Style, init

from ai_governance.policy_engine import PolicyEngine
from ai_governance.scanner import Scanner
from ai_governance.audit_logger import AuditLogger

# Initialize colorama
init(autoreset=True)


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 70}")
    print(f"{text}")
    print(f"{'=' * 70}{Style.RESET_ALL}\n")


def print_section(text):
    """Print a formatted section"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    print(f"{'-' * 70}")


def demo_security_scanning():
    """Demonstrate security scanning on all demo files"""
    print_header("AI Governance Tool - Security Scanning Demo")

    # Initialize components
    print(f"{Fore.CYAN}Initializing components...{Style.RESET_ALL}")
    policy_engine = PolicyEngine()
    scanner = Scanner(policy_engine)
    audit_logger = AuditLogger()

    # Show policy info
    policy_info = policy_engine.get_policy_info()
    print(f"\n{Fore.YELLOW}Security Policy:{Style.RESET_ALL}")
    print(f"  Name: {policy_info['name']}")
    print(f"  Version: {policy_info['version']}")
    print(f"  Description: {policy_info['description']}")
    print(f"  Blocked patterns: {policy_info['blocked_patterns_count']}")
    print(f"  Sensitive patterns: {policy_info['sensitive_patterns_count']}")

    # Demo files
    demo_dir = Path(__file__).parent / "demo" / "legacy_code"
    demo_files = [
        ("user_service.py", "Should be BLOCKED - contains API key and password"),
        ("email_handler.py", "Should be BLOCKED - contains SMTP password and emails"),
        ("payment_processor.py", "Should be BLOCKED - contains credit card data"),
        ("utils.py", "Should be ALLOWED - clean code, no sensitive data"),
        ("helper_functions.py", "Should be ALLOWED - clean code, no sensitive data"),
    ]

    results = []

    print_section("Scanning Demo Files")

    for filename, description in demo_files:
        filepath = demo_dir / filename
        print(f"\n{Fore.CYAN}File: {filename}{Style.RESET_ALL}")
        print(f"Expected: {description}")

        if not filepath.exists():
            print(f"{Fore.RED}ERROR: File not found{Style.RESET_ALL}")
            continue

        # Scan file
        scan_result = scanner.scan_file(str(filepath))

        # Display result
        if scan_result.get('error'):
            print(f"{Fore.RED}❌ ERROR: {scan_result['reason']}{Style.RESET_ALL}")
            status = 'error'
        elif scan_result['allowed']:
            print(f"{Fore.GREEN}✅ ALLOWED: {scan_result['reason']}{Style.RESET_ALL}")
            print(f"File size: {scan_result['file_size']} bytes")
            status = 'allowed'
        else:
            print(f"{Fore.RED}🚫 BLOCKED: {scan_result['reason']}{Style.RESET_ALL}")
            print(f"File size: {scan_result['file_size']} bytes")

            if scan_result['findings']:
                print(f"\n{Fore.YELLOW}Security Findings:{Style.RESET_ALL}")
                for finding in scan_result['findings']:
                    severity_color = Fore.RED if finding['severity'] == 'critical' else Fore.YELLOW
                    print(f"  • {severity_color}{finding['pattern']}{Style.RESET_ALL} "
                          f"({finding['severity']}): {finding['description']}")
                    print(f"    Matches: {finding['match_count']}")
                    if finding['examples']:
                        print(f"    Examples: {', '.join(finding['examples'])}")

            status = 'blocked'

        # Log to audit
        audit_logger.log_action(
            filepath=str(filepath),
            action='demo_scan',
            status=status,
            reason=scan_result.get('reason'),
            findings=scan_result.get('findings', [])
        )

        results.append({
            'filename': filename,
            'allowed': scan_result['allowed'],
            'error': scan_result.get('error', False)
        })

    # Summary
    print_section("Summary")

    blocked_count = sum(1 for r in results if not r['allowed'] and not r['error'])
    allowed_count = sum(1 for r in results if r['allowed'])
    error_count = sum(1 for r in results if r['error'])

    print(f"\n{Fore.GREEN}Files allowed: {allowed_count}{Style.RESET_ALL}")
    print(f"{Fore.RED}Files blocked: {blocked_count}{Style.RESET_ALL}")
    if error_count > 0:
        print(f"{Fore.YELLOW}Errors: {error_count}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}Detailed Results:{Style.RESET_ALL}")
    for result in results:
        status_icon = "✅" if result['allowed'] else ("❌" if result['error'] else "🚫")
        status_text = "ALLOWED" if result['allowed'] else ("ERROR" if result['error'] else "BLOCKED")
        status_color = Fore.GREEN if result['allowed'] else (Fore.YELLOW if result['error'] else Fore.RED)

        print(f"  {status_icon} {result['filename']:<30} {status_color}{status_text}{Style.RESET_ALL}")

    # Audit statistics
    print_section("Audit Log Statistics")

    stats = audit_logger.get_statistics()
    print(f"\nTotal requests: {stats['total_requests']}")
    print(f"Total tokens:   {stats['total_tokens']}")
    print(f"Total cost:     ${stats['total_cost']:.4f}")
    print(f"\nStatus breakdown:")
    for status, count in stats['status_counts'].items():
        print(f"  {status}: {count}")

    # Next steps
    print_section("Next Steps")

    print(f"""
{Fore.CYAN}Try refactoring the allowed files:{Style.RESET_ALL}

  ai-governance refactor demo/legacy_code/utils.py --target "modernize to Python 3.10+"
  ai-governance refactor demo/legacy_code/helper_functions.py --target "use modern Python idioms"

{Fore.YELLOW}Try refactoring blocked files (will be rejected):{Style.RESET_ALL}

  ai-governance refactor demo/legacy_code/user_service.py --target "refactor to FastAPI async"
  ai-governance refactor demo/legacy_code/email_handler.py --target "modernize email handling"

{Fore.CYAN}View audit logs:{Style.RESET_ALL}

  ai-governance audit
  ai-governance audit --status blocked
  ai-governance audit --stats
""")


if __name__ == "__main__":
    try:
        demo_security_scanning()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Demo interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
