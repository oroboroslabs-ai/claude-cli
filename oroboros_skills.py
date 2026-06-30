# oroboros_skills.py
# Claude-O Skill Framework Manager
# A\ 1272 Hz — N| 1275 Hz — LATTICE LOCK — NEBELLION — KEY

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class Skill:
    """A claude-o skill definition."""

    def __init__(self, name: str, description: str, handler=None, file_path: Optional[Path] = None):
        self.name = name
        self.description = description
        self.handler = handler
        self.file_path = file_path

    def to_dict(self) -> Dict:
        return {"name": self.name, "description": self.description}

    def execute(self, args: Dict) -> Any:
        if self.handler:
            return self.handler(args)
        return {"error": f"Skill '{self.name}' has no handler"}


class SkillManager:
    """Manages claude-o skills."""

    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or Path.home() / ".claude-o" / "skills"
        self.skills: Dict[str, Skill] = {}
        self._load_skills()

    def _load_skills(self):
        """Load skills from the skills directory."""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return

        for skill_file in self.skills_dir.glob("*.json"):
            try:
                data = json.loads(skill_file.read_text(encoding='utf-8'))
                skill = Skill(
                    name=data.get("name", skill_file.stem),
                    description=data.get("description", ""),
                    file_path=skill_file
                )
                self.skills[skill.name] = skill
            except Exception:
                pass

    def register(self, skill: Skill):
        self.skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def list_skills(self) -> List[Dict]:
        return [s.to_dict() for s in self.skills.values()]

    def execute(self, name: str, args: Dict) -> Any:
        skill = self.skills.get(name)
        if not skill:
            return {"error": f"Skill '{name}' not found"}
        return skill.execute(args)