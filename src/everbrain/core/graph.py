"""Graph logic: Build a Rich Tree from task dependency relationships.

Constructs a visual hierarchy of tasks based on parent_id linkage.
"""

from collections import defaultdict
from typing import Any

from rich.text import Text
from rich.tree import Tree


# Status icons for visual clarity
_STATUS_ICONS: dict[str, str] = {
    "open": "🔵",
    "active": "🟡",
    "blocked": "🔴",
    "completed": "✅",
    "deferred": "⏸️",
}


def _clean_id(val: Any) -> str | None:
    """Normalize IDs to handle SQLite whitespace or 'None' string quirks."""
    if not val:
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "none":
        return None
    return s


def build_task_tree(tasks: list[dict[str, Any]]) -> Tree:
    """Build a Rich Tree from a flat list of tasks with parent_id relationships.

    Identifies root tasks (no parent_id) and recursively attaches children
    beneath them, producing a visual dependency graph.

    Args:
        tasks: List of task dicts, each containing at least
               'id', 'title', 'status', and 'parent_id'.

    Returns:
        A rich.tree.Tree object ready for console printing.
    """
    # Index children by normalized parent_id
    children_map: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        clean_pid = _clean_id(task.get("parent_id"))
        children_map[clean_pid].append(task)

    # Root tasks have a normalized parent_id of None
    root_tasks = children_map[None]

    tree = Tree("📊 [bold cyan]EverBrain Task Graph[/bold cyan]")

    if not root_tasks:
        tree.add("[dim]No tasks found. Use [bold]eb task add[/bold] to create one.[/dim]")
        return tree

    def _add_children(parent_node: Tree, parent_id_val: str | None) -> None:
        """Recursively attach child tasks using fuzzy ID matching."""
        if not parent_id_val:
            return
            
        # Normalize the ID we are looking for
        p_id = str(parent_id_val).strip().lower()

        for child in tasks:
            child_pid = _clean_id(child.get("parent_id"))
            if not child_pid:
                continue
                
            # FUZZY MATCH: Check if the child's parent_id starts with our parent ID
            # This fixes the "8-char vs full-UUID" mismatch
            if child_pid.startswith(p_id) or p_id.startswith(child_pid):
                icon = _STATUS_ICONS.get(child.get("status", "open"), "❓")
                label = (
                    f"{icon}  [cyan]{child['id'][:8]}[/cyan] "
                    f"[white]{child['title']}[/white] "
                    f"[dim]({child.get('status', 'open')})[/dim]"
                )
                child_node = parent_node.add(label)
                # Recurse using the child's ID
                _add_children(child_node, child.get("id"))

    for task in root_tasks:
        icon = _STATUS_ICONS.get(task.get("status", "open"), "❓")
        label = (
            f"{icon}  [cyan]{task['id'][:8]}[/cyan] "
            f"[bold white]{task['title']}[/bold white] "
            f"[dim]({task.get('status', 'open')})[/dim]"
        )
        node = tree.add(label)
        _add_children(node, _clean_id(task.get("id")))

    return tree