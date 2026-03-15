import os
import sys

def bootstrap_skill(skill_name):
    base_path = os.path.join('_agent', 'skills', skill_name)
    subdirs = ['scripts', 'resources', 'examples']
    
    # Create directories
    for subdir in subdirs:
        os.makedirs(os.path.join(base_path, subdir), exist_ok=True)
        print(f"Created: {os.path.join(base_path, subdir)}")
    
    # Create SKILL.md from template if it exists
    template_path = os.path.join('_agent', 'skills', 'skill_architect', 'resources', 'skill_template.md')
    skill_md_path = os.path.join(base_path, 'SKILL.md')
    
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            template = f.read()
        
        with open(skill_md_path, 'w') as f:
            f.write(template.replace('SKILL_NAME', skill_name.replace('_', ' ').title()))
        print(f"Created SKILL.md from template: {skill_md_path}")
    else:
        with open(skill_md_path, 'w') as f:
            f.write(f"# {skill_name.replace('_', ' ').title()}\n\nDescription goes here.")
        print(f"Created default SKILL.md: {skill_md_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bootstrap_skill.py <skill_name>")
    else:
        bootstrap_skill(sys.argv[1])
