#!/usr/bin/env python3
"""
Batch migration script to update all Playwright tests to use the authentication utility.
This handles the most common login patterns across all test files.
"""
import os
import re
from pathlib import Path
import shutil
from datetime import datetime


def backup_file(file_path):
    """Create a backup of the file before modifying."""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    return backup_path


def add_imports_to_file(content):
    """Add necessary imports for the authentication utility."""
    # Check if already has the imports
    if 'from playwright.common.auth import' in content:
        return content
    
    # Find where to insert imports
    lines = content.split('\n')
    import_section_end = 0
    
    for i, line in enumerate(lines):
        if line.strip() and not line.startswith(('import ', 'from ', '#', '"""', "'''")):
            import_section_end = i
            break
        elif line.startswith(('import ', 'from ')):
            import_section_end = i + 1
    
    # Prepare import statements
    imports_to_add = []
    if 'import sys' not in content:
        imports_to_add.append('import sys')
    if 'import os' not in content:
        imports_to_add.append('import os')
    
    imports_to_add.extend([
        '',
        '# Add parent directory to path for imports',
        'sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), \'../../..\')))',
        'from playwright.common.auth import authenticated_page, AuthenticationError',
        ''
    ])
    
    # Insert imports
    lines[import_section_end:import_section_end] = imports_to_add
    return '\n'.join(lines)


def migrate_login_patterns(content):
    """Replace common login patterns with authentication utility usage."""
    
    # Pattern 1: Simple login sequences
    patterns = [
        # Standard login pattern with username field
        (
            r'page\.goto\(["\']([^"\']+login[^"\']*)["\'][^)]*\)\s*\n\s*'
            r'(?:page\.wait_for_[^)]+\)\s*\n\s*)?'
            r'page\.fill\(["\']input\[name=["\']username["\']\]["\']\s*,\s*["\'](\w+)["\']\)\s*\n\s*'
            r'page\.fill\(["\']input\[name=["\']password["\']\]["\']\s*,\s*["\']([^"\']+)["\']\)\s*\n\s*'
            r'page\.click\(["\']button\[type=["\']submit["\']\]["\']\)',
            r'with authenticated_page(page, "\2", "\3") as auth_page:\n            # User is now logged in'
        ),
        # Login pattern with email field
        (
            r'page\.goto\(["\']([^"\']+login[^"\']*)["\'][^)]*\)\s*\n\s*'
            r'(?:page\.wait_for_[^)]+\)\s*\n\s*)?'
            r'page\.fill\(["\']input\[name=["\']email["\']\]["\']\s*,\s*["\'](\w+)["\']\)\s*\n\s*'
            r'page\.fill\(["\']input\[name=["\']password["\']\]["\']\s*,\s*["\']([^"\']+)["\']\)\s*\n\s*'
            r'page\.click\(["\']button\[type=["\']submit["\']\]["\']\)',
            r'with authenticated_page(page, "\2", "\3") as auth_page:\n            # User is now logged in'
        ),
        # Self.page login pattern
        (
            r'self\.page\.goto\(["\']([^"\']+login[^"\']*)["\'][^)]*\)\s*\n\s*'
            r'self\.page\.fill\(["\']input\[name=["\']username["\']\]["\']\s*,\s*["\'](\w+)["\']\)\s*\n\s*'
            r'self\.page\.fill\(["\']input\[name=["\']password["\']\]["\']\s*,\s*["\']([^"\']+)["\']\)\s*\n\s*'
            r'self\.page\.click\(["\']button\[type=["\']submit["\']\]["\']\)',
            r'with authenticated_page(self.page, "\2", "\3") as auth_page:\n            self.page = auth_page'
        ),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content


def migrate_file(file_path):
    """Migrate a single test file."""
    print(f"\nProcessing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if already migrated
        if 'authenticated_page' in content:
            print("  ✓ Already migrated")
            return False
        
        # Skip if no login patterns found
        if not any(pattern in content for pattern in ['login', 'password', 'username', 'email']):
            print("  ✓ No login patterns found")
            return False
        
        # Create backup
        backup_path = backup_file(file_path)
        print(f"  → Created backup: {backup_path}")
        
        # Add imports
        content = add_imports_to_file(content)
        
        # Migrate login patterns
        original_content = content
        content = migrate_login_patterns(content)
        
        # Check if any changes were made
        if content == original_content:
            print("  ℹ No automated migration possible - manual review needed")
            # Remove backup if no changes
            os.remove(backup_path)
            return False
        
        # Write migrated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✓ Migration complete")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def find_test_files(root_dir):
    """Find all Playwright test files."""
    test_files = []
    exclude_dirs = {'venv', '__pycache__', 'node_modules', '.git'}
    exclude_files = {'test_auth_utility.py', 'example_refactored_test.py', 'test_cielo_auth_flow_refactored.py'}
    
    for root, dirs, files in os.walk(root_dir):
        # Remove excluded directories from search
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # Skip common directory
        if 'playwright/common' in root:
            continue
        
        for file in files:
            if file.startswith('test_') and file.endswith('.py') and file not in exclude_files:
                test_files.append(os.path.join(root, file))
    
    return sorted(test_files)


def main():
    """Main migration function."""
    playwright_dir = Path(__file__).parent
    
    print("Playwright Test Migration Tool")
    print("=" * 60)
    print(f"Scanning directory: {playwright_dir}")
    
    test_files = find_test_files(playwright_dir)
    print(f"\nFound {len(test_files)} test files to process")
    
    migrated_count = 0
    manual_review_needed = []
    
    for test_file in test_files:
        relative_path = os.path.relpath(test_file, playwright_dir)
        if migrate_file(test_file):
            migrated_count += 1
        elif 'login' in open(test_file).read().lower():
            manual_review_needed.append(relative_path)
    
    print("\n" + "=" * 60)
    print("Migration Summary:")
    print(f"  ✓ Successfully migrated: {migrated_count} files")
    print(f"  ℹ Already migrated: {len([f for f in test_files if 'authenticated_page' in open(f).read()])}")
    print(f"  ⚠ Manual review needed: {len(manual_review_needed)} files")
    
    if manual_review_needed:
        print("\nFiles requiring manual review:")
        for file in manual_review_needed[:10]:  # Show first 10
            print(f"  - {file}")
        if len(manual_review_needed) > 10:
            print(f"  ... and {len(manual_review_needed) - 10} more")
    
    print("\nIMPORTANT:")
    print("1. Review all migrated files to ensure correctness")
    print("2. Run tests to verify they still work")
    print("3. Backups created with .backup_TIMESTAMP extension")
    print("4. Delete backups after verification")


if __name__ == "__main__":
    main()