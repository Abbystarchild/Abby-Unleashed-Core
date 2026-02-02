"""
Knowledge Base Version Control and Auto-Update System
Tracks changes, versions knowledge files, and keeps skills relevant
"""
import os
import sys
import yaml
import json
import hashlib
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeVersion:
    """Version info for a knowledge file"""
    filename: str
    version: str
    hash: str
    last_modified: str
    line_count: int
    sections: List[str] = field(default_factory=list)
    changelog: List[str] = field(default_factory=list)


@dataclass
class KnowledgeUpdate:
    """Pending update to a knowledge file"""
    filename: str
    update_type: str  # 'add', 'modify', 'deprecate'
    section: str
    content: str
    source: str
    priority: str  # 'critical', 'high', 'medium', 'low'
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    applied: bool = False


class KnowledgeVersionControl:
    """
    Version control system for knowledge bases
    Tracks changes, maintains history, enables rollback
    """
    
    VERSION_FILE = "knowledge_versions.json"
    HISTORY_DIR = "knowledge_history"
    UPDATES_FILE = "pending_updates.json"
    
    def __init__(self, knowledge_dir: str = None):
        """
        Initialize version control
        
        Args:
            knowledge_dir: Path to knowledge directory
        """
        if knowledge_dir is None:
            knowledge_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "agents", "knowledge"
            )
        
        self.knowledge_dir = Path(knowledge_dir)
        self.version_file = self.knowledge_dir / self.VERSION_FILE
        self.history_dir = self.knowledge_dir / self.HISTORY_DIR
        self.updates_file = self.knowledge_dir / self.UPDATES_FILE
        
        # Ensure directories exist
        self.history_dir.mkdir(exist_ok=True)
        
        # Load existing versions
        self.versions: Dict[str, KnowledgeVersion] = {}
        self._load_versions()
        
        # Load pending updates
        self.pending_updates: List[KnowledgeUpdate] = []
        self._load_pending_updates()
    
    def _load_versions(self):
        """Load version information from file"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                for filename, info in data.get('versions', {}).items():
                    self.versions[filename] = KnowledgeVersion(**info)
            except Exception as e:
                logger.warning(f"Could not load versions: {e}")
    
    def _save_versions(self):
        """Save version information to file"""
        data = {
            'last_updated': datetime.now().isoformat(),
            'versions': {
                name: asdict(ver) for name, ver in self.versions.items()
            }
        }
        with open(self.version_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_pending_updates(self):
        """Load pending updates from file"""
        if self.updates_file.exists():
            try:
                with open(self.updates_file, 'r') as f:
                    data = json.load(f)
                self.pending_updates = [
                    KnowledgeUpdate(**u) for u in data.get('updates', [])
                ]
            except Exception as e:
                logger.warning(f"Could not load pending updates: {e}")
    
    def _save_pending_updates(self):
        """Save pending updates to file"""
        data = {
            'last_updated': datetime.now().isoformat(),
            'updates': [asdict(u) for u in self.pending_updates if not u.applied]
        }
        with open(self.updates_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _calculate_hash(self, filepath: Path) -> str:
        """Calculate file hash"""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    
    def _extract_sections(self, filepath: Path) -> List[str]:
        """Extract top-level sections from YAML file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            if isinstance(content, dict):
                return list(content.keys())
        except Exception:
            pass
        return []
    
    def _get_line_count(self, filepath: Path) -> int:
        """Get line count of file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    
    def scan_knowledge_files(self) -> Dict[str, KnowledgeVersion]:
        """
        Scan all knowledge files and update version info
        
        Returns:
            Dictionary of filename to version info
        """
        current_versions = {}
        
        for filepath in self.knowledge_dir.glob("*.yaml"):
            if filepath.name.startswith('_'):
                continue  # Skip internal files
            
            filename = filepath.name
            file_hash = self._calculate_hash(filepath)
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            sections = self._extract_sections(filepath)
            line_count = self._get_line_count(filepath)
            
            # Check if file changed
            existing = self.versions.get(filename)
            if existing and existing.hash == file_hash:
                # No change
                current_versions[filename] = existing
            else:
                # New or modified
                version = "1.0" if not existing else self._increment_version(existing.version)
                changelog = []
                
                if existing:
                    changelog = list(existing.changelog) + [
                        f"{datetime.now().isoformat()}: Updated (hash changed)"
                    ]
                else:
                    changelog = [f"{datetime.now().isoformat()}: Initial version"]
                
                current_versions[filename] = KnowledgeVersion(
                    filename=filename,
                    version=version,
                    hash=file_hash,
                    last_modified=mtime.isoformat(),
                    line_count=line_count,
                    sections=sections,
                    changelog=changelog[-10:]  # Keep last 10 entries
                )
        
        self.versions = current_versions
        self._save_versions()
        return current_versions
    
    def _increment_version(self, version: str) -> str:
        """Increment version number"""
        try:
            major, minor = version.split('.')
            return f"{major}.{int(minor) + 1}"
        except:
            return "1.0"
    
    def create_backup(self, filename: str) -> Optional[Path]:
        """
        Create backup of a knowledge file before modification
        
        Args:
            filename: Name of file to backup
            
        Returns:
            Path to backup file
        """
        source = self.knowledge_dir / filename
        if not source.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{filename}.{timestamp}.bak"
        backup_path = self.history_dir / backup_name
        
        shutil.copy2(source, backup_path)
        logger.info(f"Created backup: {backup_path}")
        
        return backup_path
    
    def rollback(self, filename: str, version: str = None) -> bool:
        """
        Rollback a knowledge file to a previous version
        
        Args:
            filename: Name of file to rollback
            version: Specific version to rollback to (latest if None)
            
        Returns:
            True if successful
        """
        # Find backup files
        pattern = f"{filename}.*.bak"
        backups = sorted(self.history_dir.glob(pattern), reverse=True)
        
        if not backups:
            logger.error(f"No backups found for {filename}")
            return False
        
        # Use latest backup
        backup = backups[0]
        target = self.knowledge_dir / filename
        
        # Backup current version first
        self.create_backup(filename)
        
        # Restore
        shutil.copy2(backup, target)
        logger.info(f"Rolled back {filename} to {backup.name}")
        
        # Update versions
        self.scan_knowledge_files()
        
        return True
    
    def add_pending_update(
        self,
        filename: str,
        section: str,
        content: str,
        source: str,
        update_type: str = 'add',
        priority: str = 'medium'
    ):
        """
        Add a pending update for review
        
        Args:
            filename: Target knowledge file
            section: Section to update
            content: New content
            source: Source of the update
            update_type: Type of update
            priority: Priority level
        """
        update = KnowledgeUpdate(
            filename=filename,
            update_type=update_type,
            section=section,
            content=content,
            source=source,
            priority=priority
        )
        self.pending_updates.append(update)
        self._save_pending_updates()
        logger.info(f"Added pending update for {filename}/{section}")
    
    def get_pending_updates(self, priority: str = None) -> List[KnowledgeUpdate]:
        """Get pending updates, optionally filtered by priority"""
        updates = [u for u in self.pending_updates if not u.applied]
        if priority:
            updates = [u for u in updates if u.priority == priority]
        return sorted(updates, key=lambda u: {
            'critical': 0, 'high': 1, 'medium': 2, 'low': 3
        }.get(u.priority, 4))
    
    def apply_update(self, update: KnowledgeUpdate) -> bool:
        """
        Apply a pending update to knowledge file
        
        Args:
            update: Update to apply
            
        Returns:
            True if successful
        """
        filepath = self.knowledge_dir / update.filename
        
        # Create backup first
        self.create_backup(update.filename)
        
        try:
            # Load existing content
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f) or {}
            else:
                content = {}
            
            # Apply update based on type
            if update.update_type == 'add':
                # Add new section
                if update.section not in content:
                    content[update.section] = yaml.safe_load(update.content)
                else:
                    # Merge into existing section
                    existing = content[update.section]
                    new_content = yaml.safe_load(update.content)
                    if isinstance(existing, dict) and isinstance(new_content, dict):
                        existing.update(new_content)
                    elif isinstance(existing, list) and isinstance(new_content, list):
                        existing.extend(new_content)
            
            elif update.update_type == 'modify':
                content[update.section] = yaml.safe_load(update.content)
            
            elif update.update_type == 'deprecate':
                if update.section in content:
                    # Move to deprecated section
                    if '_deprecated' not in content:
                        content['_deprecated'] = {}
                    content['_deprecated'][update.section] = content.pop(update.section)
            
            # Save updated content
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(content, f, default_flow_style=False, allow_unicode=True)
            
            # Mark update as applied
            update.applied = True
            self._save_pending_updates()
            
            # Update versions
            self.scan_knowledge_files()
            
            logger.info(f"Applied update to {update.filename}/{update.section}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply update: {e}")
            # Restore backup on failure
            self.rollback(update.filename)
            return False
    
    def get_version_report(self) -> str:
        """Generate human-readable version report"""
        self.scan_knowledge_files()
        
        lines = [
            "=" * 60,
            "KNOWLEDGE BASE VERSION REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 60,
            ""
        ]
        
        total_lines = 0
        for filename, version in sorted(self.versions.items()):
            total_lines += version.line_count
            lines.append(f"📚 {filename}")
            lines.append(f"   Version: {version.version}")
            lines.append(f"   Lines: {version.line_count}")
            lines.append(f"   Hash: {version.hash}")
            lines.append(f"   Modified: {version.last_modified}")
            lines.append(f"   Sections: {', '.join(version.sections[:5])}")
            if len(version.sections) > 5:
                lines.append(f"             ... and {len(version.sections) - 5} more")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append(f"Total: {len(self.versions)} files, {total_lines} lines")
        lines.append("=" * 60)
        
        # Pending updates
        pending = self.get_pending_updates()
        if pending:
            lines.append(f"\n⚠️  {len(pending)} PENDING UPDATES:")
            for update in pending[:5]:
                lines.append(f"   [{update.priority}] {update.filename}/{update.section}")
        
        return "\n".join(lines)


class KnowledgeAutoUpdater:
    """
    Automated system to check for and suggest knowledge updates
    """
    
    # Sources to check for updates
    UPDATE_SOURCES = [
        {
            "name": "Python Official",
            "topics": ["python_mastery"],
            "check_interval_days": 30
        },
        {
            "name": "OWASP",
            "topics": ["security_mastery", "security_practices"],
            "check_interval_days": 14
        },
        {
            "name": "React/Frontend",
            "topics": ["frontend_mastery", "javascript_typescript_mastery"],
            "check_interval_days": 30
        },
    ]
    
    def __init__(self, version_control: KnowledgeVersionControl):
        self.vc = version_control
        self.last_check_file = self.vc.knowledge_dir / ".last_update_check"
    
    def _get_last_check(self) -> Optional[datetime]:
        """Get last update check time"""
        if self.last_check_file.exists():
            try:
                with open(self.last_check_file, 'r') as f:
                    return datetime.fromisoformat(f.read().strip())
            except:
                pass
        return None
    
    def _record_check(self):
        """Record current check time"""
        with open(self.last_check_file, 'w') as f:
            f.write(datetime.now().isoformat())
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check if knowledge bases need updates
        
        Returns:
            List of suggested updates
        """
        suggestions = []
        
        # Check version ages
        for filename, version in self.vc.versions.items():
            modified = datetime.fromisoformat(version.last_modified)
            age_days = (datetime.now() - modified).days
            
            # Suggest review for files not updated in 90 days
            if age_days > 90:
                suggestions.append({
                    "filename": filename,
                    "reason": f"Not updated in {age_days} days",
                    "priority": "medium" if age_days < 180 else "high",
                    "action": "review_and_update"
                })
        
        # Check for known outdated patterns
        outdated_patterns = [
            ("python_mastery", "Python 3.10", "Consider Python 3.12+ features"),
            ("frontend_mastery", "React 18", "Consider React 19 features"),
            ("security_mastery", "OWASP 2021", "Update to OWASP 2023/2024"),
        ]
        
        for filename, old_pattern, suggestion in outdated_patterns:
            if filename in self.vc.versions:
                filepath = self.vc.knowledge_dir / filename
                if filepath.exists():
                    content = filepath.read_text()
                    if old_pattern.lower() in content.lower():
                        suggestions.append({
                            "filename": filename,
                            "reason": f"Contains outdated reference: {old_pattern}",
                            "suggestion": suggestion,
                            "priority": "medium",
                            "action": "update_content"
                        })
        
        self._record_check()
        return suggestions
    
    def generate_update_report(self) -> str:
        """Generate update suggestions report"""
        suggestions = self.check_for_updates()
        
        lines = [
            "=" * 60,
            "KNOWLEDGE UPDATE SUGGESTIONS",
            f"Checked: {datetime.now().isoformat()}",
            "=" * 60,
            ""
        ]
        
        if not suggestions:
            lines.append("✅ All knowledge bases are up to date!")
        else:
            for s in suggestions:
                emoji = "🔴" if s.get("priority") == "high" else "🟡"
                lines.append(f"{emoji} {s['filename']}")
                lines.append(f"   Reason: {s['reason']}")
                if 'suggestion' in s:
                    lines.append(f"   Suggestion: {s['suggestion']}")
                lines.append("")
        
        return "\n".join(lines)


def main():
    """CLI for knowledge version control"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Base Version Control")
    parser.add_argument("command", choices=[
        "status", "scan", "backup", "rollback", "check-updates", "report"
    ])
    parser.add_argument("--file", help="Specific file to operate on")
    
    args = parser.parse_args()
    
    vc = KnowledgeVersionControl()
    
    if args.command == "status":
        print(vc.get_version_report())
    
    elif args.command == "scan":
        versions = vc.scan_knowledge_files()
        print(f"Scanned {len(versions)} knowledge files")
    
    elif args.command == "backup":
        if args.file:
            path = vc.create_backup(args.file)
            print(f"Created backup: {path}")
        else:
            print("Please specify --file")
    
    elif args.command == "rollback":
        if args.file:
            success = vc.rollback(args.file)
            print("Rollback successful" if success else "Rollback failed")
        else:
            print("Please specify --file")
    
    elif args.command == "check-updates":
        updater = KnowledgeAutoUpdater(vc)
        print(updater.generate_update_report())
    
    elif args.command == "report":
        print(vc.get_version_report())
        print()
        updater = KnowledgeAutoUpdater(vc)
        print(updater.generate_update_report())


if __name__ == "__main__":
    main()
