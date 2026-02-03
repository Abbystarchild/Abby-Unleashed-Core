"""
Abby's Skills and Knowledge Manager
Provides RPG-style skill tracking and visualization data
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class SkillsManager:
    """Manages Abby's skills and knowledge base for RPG-style display"""
    
    # Skill categories with icons and colors
    SKILL_CATEGORIES = {
        'programming': {
            'icon': '💻',
            'color': '#6366f1',
            'name': 'Programming',
            'description': 'Code mastery and software development'
        },
        'security': {
            'icon': '🔐',
            'color': '#ef4444',
            'name': 'Security',
            'description': 'Offensive and defensive security'
        },
        'devops': {
            'icon': '⚙️',
            'color': '#f59e0b',
            'name': 'DevOps',
            'description': 'Infrastructure and deployment'
        },
        'mind_arts': {
            'icon': '🧠',
            'color': '#8b5cf6',
            'name': 'Mind Arts',
            'description': 'Psychology, influence, and perception'
        },
        'performance': {
            'icon': '🎭',
            'color': '#ec4899',
            'name': 'Performance',
            'description': 'Entertainment and showmanship'
        },
        'data': {
            'icon': '📊',
            'color': '#10b981',
            'name': 'Data',
            'description': 'Databases and data management'
        },
        'engineering': {
            'icon': '🔧',
            'color': '#64748b',
            'name': 'Engineering',
            'description': 'System design and architecture'
        }
    }
    
    # Map knowledge files to categories and skill info
    SKILL_MAPPINGS = {
        'python_mastery.yaml': {
            'category': 'programming',
            'name': 'Python',
            'icon': '🐍',
            'base_level': 85,
            'subskills': ['OOP', 'Async', 'Data Structures', 'Web Frameworks']
        },
        'javascript_typescript_mastery.yaml': {
            'category': 'programming',
            'name': 'JavaScript/TypeScript',
            'icon': '📜',
            'base_level': 75,
            'subskills': ['ES6+', 'React', 'Node.js', 'TypeScript']
        },
        'kotlin_mastery.yaml': {
            'category': 'programming',
            'name': 'Kotlin',
            'icon': '🎯',
            'base_level': 60,
            'subskills': ['Android', 'Coroutines', 'Jetpack Compose']
        },
        'general_programming.yaml': {
            'category': 'programming',
            'name': 'General Programming',
            'icon': '📚',
            'base_level': 80,
            'subskills': ['Algorithms', 'Design Patterns', 'Clean Code']
        },
        'coding_foundations.yaml': {
            'category': 'programming',
            'name': 'Coding Foundations',
            'icon': '🏗️',
            'base_level': 90,
            'subskills': ['SOLID', 'DRY', 'Testing', 'Documentation']
        },
        'hacking_penetration_testing_mastery.yaml': {
            'category': 'security',
            'name': 'Hacking & Pentesting',
            'icon': '💀',
            'base_level': 70,
            'subskills': ['Recon', 'Exploitation', 'Web Attacks', 'Social Engineering', 'Persistence']
        },
        'security_practices.yaml': {
            'category': 'security',
            'name': 'Security Practices',
            'icon': '🛡️',
            'base_level': 75,
            'subskills': ['Authentication', 'Encryption', 'Secure Coding']
        },
        'api_design_mastery.yaml': {
            'category': 'engineering',
            'name': 'API Design',
            'icon': '🔌',
            'base_level': 80,
            'subskills': ['REST', 'GraphQL', 'Versioning', 'Documentation']
        },
        'database_mastery.yaml': {
            'category': 'data',
            'name': 'Databases',
            'icon': '🗄️',
            'base_level': 75,
            'subskills': ['SQL', 'NoSQL', 'Optimization', 'Migrations']
        },
        'docker_mastery.yaml': {
            'category': 'devops',
            'name': 'Docker',
            'icon': '🐳',
            'base_level': 70,
            'subskills': ['Containers', 'Compose', 'Networking', 'Volumes']
        },
        'devops_mastery.yaml': {
            'category': 'devops',
            'name': 'DevOps',
            'icon': '🚀',
            'base_level': 65,
            'subskills': ['CI/CD', 'Monitoring', 'Infrastructure']
        },
        'git_mastery.yaml': {
            'category': 'devops',
            'name': 'Git',
            'icon': '📦',
            'base_level': 85,
            'subskills': ['Branching', 'Merging', 'Workflows', 'History']
        },
        'error_handling_mastery.yaml': {
            'category': 'engineering',
            'name': 'Error Handling',
            'icon': '⚠️',
            'base_level': 80,
            'subskills': ['Exceptions', 'Logging', 'Recovery', 'Debugging']
        },
        'performance_mastery.yaml': {
            'category': 'engineering',
            'name': 'Performance',
            'icon': '⚡',
            'base_level': 70,
            'subskills': ['Profiling', 'Optimization', 'Caching', 'Scaling']
        },
        'testing_mastery.yaml': {
            'category': 'engineering',
            'name': 'Testing',
            'icon': '🧪',
            'base_level': 75,
            'subskills': ['Unit', 'Integration', 'E2E', 'TDD']
        },
        # NEW SKILLS - Phase 5 Knowledge Expansion
        'backend_mastery.yaml': {
            'category': 'programming',
            'name': 'Backend Development',
            'icon': '🖥️',
            'base_level': 85,
            'subskills': ['APIs', 'Microservices', 'Message Queues', 'Caching']
        },
        'frontend_mastery.yaml': {
            'category': 'programming',
            'name': 'Frontend Development',
            'icon': '🎨',
            'base_level': 80,
            'subskills': ['React', 'Vue', 'State Management', 'CSS/Tailwind']
        },
        'security_mastery.yaml': {
            'category': 'security',
            'name': 'Application Security',
            'icon': '🔒',
            'base_level': 80,
            'subskills': ['OWASP Top 10', 'Auth/AuthZ', 'Cryptography', 'Threat Modeling']
        },
        'data_engineering_mastery.yaml': {
            'category': 'data',
            'name': 'Data Engineering',
            'icon': '🔄',
            'base_level': 75,
            'subskills': ['ETL', 'Spark', 'Airflow', 'Data Lakes']
        },
        'ml_engineering_mastery.yaml': {
            'category': 'data',
            'name': 'ML Engineering',
            'icon': '🤖',
            'base_level': 70,
            'subskills': ['MLOps', 'Model Training', 'Feature Engineering', 'Deployment']
        },
        'qa_mastery.yaml': {
            'category': 'engineering',
            'name': 'QA Engineering',
            'icon': '✅',
            'base_level': 75,
            'subskills': ['Test Strategy', 'Automation', 'Performance Testing', 'CI Integration']
        },
        'postgresql_mastery.yaml': {
            'category': 'data',
            'name': 'PostgreSQL',
            'icon': '🐘',
            'base_level': 80,
            'subskills': ['Query Optimization', 'Indexing', 'Replication', 'Extensions']
        },
        'sre_mastery.yaml': {
            'category': 'devops',
            'name': 'Site Reliability',
            'icon': '📡',
            'base_level': 75,
            'subskills': ['SLOs/SLIs', 'Incident Response', 'Capacity Planning', 'Observability']
        },
        'ios_mastery.yaml': {
            'category': 'programming',
            'name': 'iOS Development',
            'icon': '📱',
            'base_level': 65,
            'subskills': ['Swift', 'SwiftUI', 'UIKit', 'Core Data']
        },
        'code_review_mastery.yaml': {
            'category': 'engineering',
            'name': 'Code Review',
            'icon': '👀',
            'base_level': 80,
            'subskills': ['Best Practices', 'Security Review', 'Performance Review', 'Mentoring']
        },
        'debugging_mastery.yaml': {
            'category': 'engineering',
            'name': 'Debugging',
            'icon': '🔍',
            'base_level': 85,
            'subskills': ['Root Cause Analysis', 'Profiling', 'Log Analysis', 'Tracing']
        },
        'technical_writing_mastery.yaml': {
            'category': 'engineering',
            'name': 'Technical Writing',
            'icon': '📝',
            'base_level': 75,
            'subskills': ['Documentation', 'API Docs', 'Tutorials', 'Architecture Docs']
        },
        'illusionism_mastery.yaml': {
            'category': 'performance',
            'name': 'Illusionism',
            'icon': '🎩',
            'base_level': 60,
            'subskills': ['Sleight of Hand', 'Misdirection', 'Card Magic', 'Stage Presence']
        },
        'mentalism_mastery.yaml': {
            'category': 'mind_arts',
            'name': 'Mentalism',
            'icon': '🔮',
            'base_level': 65,
            'subskills': ['Cold Reading', 'Psychological Forces', 'Predictions', 'Dual Reality']
        },
        'hypnotism_mastery.yaml': {
            'category': 'mind_arts',
            'name': 'Hypnotism',
            'icon': '🌀',
            'base_level': 55,
            'subskills': ['Inductions', 'Suggestions', 'Self-Hypnosis', 'Stage Hypnosis']
        },
        # NEW SKILLS - Creative & Project-Specific
        'structured_dreaming_mastery.yaml': {
            'category': 'mind_arts',
            'name': 'Structured Dreaming',
            'icon': '💭',
            'base_level': 70,
            'subskills': ['Divergent Thinking', 'Convergent Filtering', 'HMW Questions', 'Ideation']
        },
        'safeconnect_production_mastery.yaml': {
            'category': 'programming',
            'name': 'SafeConnect Production',
            'icon': '💜',
            'base_level': 60,
            'subskills': ['Ktor Backend', 'Real-time Chat', 'Dating UX', '3D Discovery UI']
        }
    }
    
    def __init__(self, knowledge_path: str = None):
        if knowledge_path is None:
            knowledge_path = Path(__file__).parent / 'agents' / 'knowledge'
        self.knowledge_path = Path(knowledge_path)
        self._cache = None
        self._cache_time = None
    
    def get_all_skills(self) -> Dict[str, Any]:
        """Get all skills organized for RPG display"""
        # Cache for 60 seconds
        if self._cache and self._cache_time:
            if (datetime.now() - self._cache_time).seconds < 60:
                return self._cache
        
        skills_by_category = {cat: [] for cat in self.SKILL_CATEGORIES}
        all_skills = []
        total_level = 0
        skill_count = 0
        
        # Scan knowledge files
        if self.knowledge_path.exists():
            for file in self.knowledge_path.glob('*.yaml'):
                filename = file.name
                if filename in self.SKILL_MAPPINGS:
                    mapping = self.SKILL_MAPPINGS[filename]
                    skill_data = self._load_skill_data(file, mapping)
                    skills_by_category[mapping['category']].append(skill_data)
                    all_skills.append(skill_data)
                    total_level += skill_data['level']
                    skill_count += 1
        
        # Calculate overall stats
        avg_level = total_level / skill_count if skill_count > 0 else 0
        
        # Calculate category averages
        category_stats = {}
        for cat, skills in skills_by_category.items():
            if skills:
                cat_avg = sum(s['level'] for s in skills) / len(skills)
                category_stats[cat] = {
                    **self.SKILL_CATEGORIES[cat],
                    'skill_count': len(skills),
                    'average_level': round(cat_avg, 1),
                    'skills': sorted(skills, key=lambda x: x['level'], reverse=True)
                }
        
        result = {
            'character': {
                'name': 'Abby',
                'title': 'Digital Entity',
                'class': 'AI Assistant',
                'level': self._calculate_character_level(avg_level, skill_count),
                'experience': skill_count * 100,
                'next_level_xp': (self._calculate_character_level(avg_level, skill_count) + 1) * 500
            },
            'stats': {
                'total_skills': skill_count,
                'average_level': round(avg_level, 1),
                'categories': len([c for c in category_stats if category_stats[c]['skill_count'] > 0]),
                'mastered': len([s for s in all_skills if s['level'] >= 80]),
                'learning': len([s for s in all_skills if 40 <= s['level'] < 80]),
                'novice': len([s for s in all_skills if s['level'] < 40])
            },
            'categories': category_stats,
            'top_skills': sorted(all_skills, key=lambda x: x['level'], reverse=True)[:10],
            'recent_acquired': self._get_recent_skills(),
            'last_updated': datetime.now().isoformat()
        }
        
        self._cache = result
        self._cache_time = datetime.now()
        return result
    
    def _load_skill_data(self, file_path: Path, mapping: Dict) -> Dict[str, Any]:
        """Load and analyze a skill file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f) or {}
            
            # Calculate depth score based on content richness
            depth_score = self._calculate_depth(content)
            
            # Adjust level based on content depth
            level = min(100, mapping['base_level'] + depth_score)
            
            return {
                'name': mapping['name'],
                'icon': mapping['icon'],
                'category': mapping['category'],
                'level': round(level, 1),
                'subskills': mapping.get('subskills', []),
                'file': file_path.name,
                'mastery_tier': self._get_mastery_tier(level),
                'content_depth': depth_score
            }
        except Exception as e:
            return {
                'name': mapping['name'],
                'icon': mapping['icon'],
                'category': mapping['category'],
                'level': mapping['base_level'],
                'subskills': mapping.get('subskills', []),
                'file': file_path.name,
                'mastery_tier': self._get_mastery_tier(mapping['base_level']),
                'content_depth': 0,
                'error': str(e)
            }
    
    def _calculate_depth(self, content: Any, depth: int = 0) -> int:
        """Calculate content depth/richness score"""
        if depth > 10:  # Prevent infinite recursion
            return 0
        
        score = 0
        if isinstance(content, dict):
            score += len(content) * 0.5
            for v in content.values():
                score += self._calculate_depth(v, depth + 1)
        elif isinstance(content, list):
            score += len(content) * 0.3
            for item in content[:20]:  # Sample first 20 items
                score += self._calculate_depth(item, depth + 1) * 0.5
        elif isinstance(content, str):
            score += min(len(content) / 500, 2)  # Cap string contribution
        
        return min(score, 15)  # Cap total depth bonus
    
    def _get_mastery_tier(self, level: float) -> str:
        """Get mastery tier name"""
        if level >= 90:
            return 'Legendary'
        elif level >= 80:
            return 'Master'
        elif level >= 70:
            return 'Expert'
        elif level >= 60:
            return 'Proficient'
        elif level >= 40:
            return 'Apprentice'
        else:
            return 'Novice'
    
    def _calculate_character_level(self, avg_skill: float, skill_count: int) -> int:
        """Calculate overall character level"""
        base = avg_skill / 10
        breadth_bonus = min(skill_count / 5, 5)
        return int(base + breadth_bonus)
    
    def _get_recent_skills(self) -> List[Dict]:
        """Get recently added/modified skills"""
        recent = []
        if self.knowledge_path.exists():
            files = list(self.knowledge_path.glob('*.yaml'))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file in files[:5]:
                if file.name in self.SKILL_MAPPINGS:
                    mapping = self.SKILL_MAPPINGS[file.name]
                    recent.append({
                        'name': mapping['name'],
                        'icon': mapping['icon'],
                        'category': mapping['category'],
                        'modified': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    })
        
        return recent
    
    def add_skill_mapping(self, filename: str, mapping: Dict) -> bool:
        """Add a new skill mapping dynamically"""
        if 'category' not in mapping or 'name' not in mapping:
            return False
        
        # Set defaults
        mapping.setdefault('icon', '📄')
        mapping.setdefault('base_level', 50)
        mapping.setdefault('subskills', [])
        
        self.SKILL_MAPPINGS[filename] = mapping
        self._cache = None  # Invalidate cache
        return True


# Singleton instance
_skills_manager = None

def get_skills_manager() -> SkillsManager:
    """Get or create the skills manager singleton"""
    global _skills_manager
    if _skills_manager is None:
        _skills_manager = SkillsManager()
    return _skills_manager
