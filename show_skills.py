"""Display Abby's current skills in a nice format"""
from skills_display import get_skills_manager

def display_skills():
    sm = get_skills_manager()
    skills = sm.get_all_skills()
    
    print("=" * 65)
    print("                    ABBY - SKILL PROFILE")
    print("=" * 65)
    c = skills['character']
    s = skills['stats']
    print(f"  Name: {c['name']}  |  Title: {c['title']}  |  Class: {c['class']}")
    print(f"  Level: {c['level']}  |  XP: {c['experience']}")
    print(f"  Total Skills: {s['total_skills']}  |  Avg Level: {s['average_level']}")
    print(f"  Mastered: {s['mastered']}  |  Learning: {s['learning']}")
    print("=" * 65)
    
    for cat_name, cat_data in skills['categories'].items():
        if cat_data['skill_count'] > 0:
            print()
            print(f"{cat_data['icon']} {cat_data['name'].upper()} (avg: {cat_data['average_level']}, count: {cat_data['skill_count']})")
            print("-" * 65)
            for skill in cat_data['skills']:
                filled = int(skill['level'] / 10)
                empty = 10 - filled
                bar = "█" * filled + "░" * empty
                tier = skill['mastery_tier'][:3].upper()
                print(f"  {skill['icon']} {skill['name']:28} [{bar}] {skill['level']:5.1f} {tier}")
    
    print()
    print("=" * 65)
    print("RECENT ACTIVITY:")
    for r in skills['recent_acquired'][:5]:
        print(f"  {r['icon']} {r['name']} ({r['category']})")
    print("=" * 65)

if __name__ == "__main__":
    display_skills()
