"""Reading the plan, docs/PLAN.md: its milestones and their task checkboxes."""

import re
from dataclasses import dataclass, field

MILESTONE_HEADING = re.compile(r"^## Milestone (\d+)\b:?\s*(.*)$")
TASK = re.compile(r"^\s*[-*] \[([ xX])\] (.*)$")


@dataclass
class Milestone:
    number: int
    name: str
    tasks: list[tuple[bool, str]] = field(default_factory=list)

    @property
    def done(self) -> int:
        return sum(ticked for ticked, _ in self.tasks)

    @property
    def total(self) -> int:
        return len(self.tasks)


def read_milestones(text: str) -> list[Milestone]:
    """Each "## Milestone N: name" heading with the checkbox tasks under it, up to the next heading."""
    milestones: list[Milestone] = []
    current = None
    for line in text.split("\n"):
        if heading := MILESTONE_HEADING.match(line):
            current = Milestone(int(heading.group(1)), heading.group(2).strip())
            milestones.append(current)
        elif line.startswith("#"):
            current = None
        elif current and (task := TASK.match(line)):
            current.tasks.append((task.group(1) != " ", task.group(2).strip()))
    return milestones
