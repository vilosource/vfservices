#!/usr/bin/env python3
"""
Script to migrate all Playwright tests to use the authentication utility.
This script identifies common login patterns and replaces them with the auth utility.
"""
import os
import re
import sys
from pathlib import Path


def migrate_test_file(file_path):
    """Migrate a single test file to use the authentication utility."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Skip if already migrated
    if 'from playwright.common.auth import' in content or 'authenticated_page' in content:
        print(f"  ✓ Already migrated: {file_path}")
        return False
    
    original_content = content
    
    # Add import statements if not present
    if 'import sys' not in content:
        # Find the first import statement
        import_match = re.search(r'^import\s+\w+', content, re.MULTILINE)
        if import_match:
            insert_pos = import_match.start()
            content = content[:insert_pos] + "import sys\n" + content[insert_pos:]
    
    # Add path setup and auth import after imports
    if 'sys.path' not in content or 'playwright.common.auth' not in content:
        # Find the last import statement
        imports = list(re.finditer(r'^(?:import|from)\s+.*$', content, re.MULTILINE))
        if imports:
            last_import = imports[-1]
            insert_pos = last_import.end()
            
            path_setup = "\n\n# Add parent directory to path for imports\n"
            path_setup += "sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))\n"
            path_setup += "from playwright.common.auth import authenticated_page, AuthenticationError\n"
            
            content = content[:insert_pos] + path_setup + content[insert_pos:]
    
    # Pattern replacements for common login patterns
    replacements = [
        # Pattern 1: Login method with goto, fill, and click
        (
            r'def\s+login[_\w]*\(self[^)]*\):[^}]+?page\.goto\([^)]*login[^)]*\)[^}]+?page\.fill\([^)]*username[^)]*\)[^}]+?page\.fill\([^)]*password[^)]*\)[^}]+?page\.click\([^)]*submit[^)]*\)[^}]+?(?=def|\Z)',
            'def login_user(self, username, password):\n        """Login user using authentication utility."""\n        with authenticated_page(self.page, username, password) as auth_page:\n            return auth_page\n'
        ),
        
        # Pattern 2: Inline login code
        (
            r'page\.goto\([^)]*login[^)]*\)\s*\n\s*page\.fill\([^)]*username[^)]*,\s*["\'](\w+)["\']\)\s*\n\s*page\.fill\([^)]*password[^)]*,\s*["\']([^"\']+)["\']\)\s*\n\s*page\.click\([^)]*submit[^)]*\)',
            r'with authenticated_page(page, "\1", "\2") as auth_page:\n            # User is now logged in'
        ),
        
        # Pattern 3: Self.page login patterns
        (
            r'self\.page\.goto\([^)]*login[^)]*\)\s*\n\s*self\.page\.fill\([^)]*username[^)]*,\s*["\'](\w+)["\']\)\s*\n\s*self\.page\.fill\([^)]*password[^)]*,\s*["\']([^"\']+)["\']\)\s*\n\s*self\.page\.click\([^)]*submit[^)]*\)',
            r'with authenticated_page(self.page, "\1", "\2") as auth_page:\n            self.page = auth_page'
        ),
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Handle specific test patterns
    if 'test_cielo' in str(file_path):
        content = migrate_cielo_tests(content)
    elif 'test_identity_admin' in str(file_path):
        content = migrate_identity_admin_tests(content)
    elif 'test_azure_costs' in str(file_path):
        content = migrate_azure_costs_tests(content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Migrated: {file_path}")
        return True
    else:
        print(f"  ⚠ No changes needed: {file_path}")
        return False


def migrate_cielo_tests(content):
    """Specific migrations for CIELO tests."""
    # Replace CIELO-specific login patterns
    content = re.sub(
        r'page\.goto\("https://cielo\.viloforge\.com/accounts/login/"[^)]*\)\s*\n\s*page\.fill\(\'input\[name="email"\]\',\s*["\'](\w+)["\']\)\s*\n\s*page\.fill\(\'input\[name="password"\]\',\s*["\']([^"\']+)["\']\)\s*\n\s*page\.click\(\'button\[type="submit"\]\'\)',
        r'with authenticated_page(page, "\1", "\2", service_url="https://cielo.viloforge.com") as auth_page:',
        content
    )
    return content


def migrate_identity_admin_tests(content):
    """Specific migrations for Identity Admin tests."""
    # Replace Identity Admin login patterns
    content = re.sub(
        r'page\.goto\("https://identity\.vfservices\.viloforge\.com/login/"[^)]*\)\s*\n\s*[^}]+?page\.fill\("input\[name=\'username\'\]",\s*"(\w+)"\)\s*\n\s*page\.fill\("input\[name=\'password\'\]",\s*"([^"]+)"\)\s*\n\s*page\.click\("button\[type=\'submit\'\]"\)',
        r'with authenticated_page(page, "\1", "\2") as auth_page:',
        content
    )
    return content


def migrate_azure_costs_tests(content):
    """Specific migrations for Azure Costs tests."""
    # Already handled in the main migration
    return content


def find_test_files(root_dir):
    """Find all test files that might need migration."""
    test_files = []
    for path in Path(root_dir).rglob('test_*.py'):
        # Skip venv directories
        if 'venv' in str(path) or '__pycache__' in str(path):
            continue
        # Skip common directory (our utility)
        if 'playwright/common' in str(path):
            continue
        # Skip already refactored files
        if 'refactored' in str(path):
            continue
        test_files.append(path)
    return test_files


def main():
    """Main migration function."""
    print("Starting Playwright test migration...")
    print("=" * 60)
    
    playwright_dir = Path(__file__).parent
    test_files = find_test_files(playwright_dir)
    
    print(f"Found {len(test_files)} test files to check")
    print()
    
    migrated_count = 0
    for test_file in sorted(test_files):
        relative_path = test_file.relative_to(playwright_dir)
        print(f"Checking: {relative_path}")
        if migrate_test_file(test_file):
            migrated_count += 1
    
    print()
    print("=" * 60)
    print(f"Migration complete!")
    print(f"Files migrated: {migrated_count}")
    print(f"Files already migrated or unchanged: {len(test_files) - migrated_count}")
    
    if migrated_count > 0:
        print("\nIMPORTANT: Please review the migrated files and test them!")
        print("Some manual adjustments may be needed for complex login flows.")


if __name__ == "__main__":
    main()