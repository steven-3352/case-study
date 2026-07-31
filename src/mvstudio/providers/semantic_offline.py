"""Explicitly non-semantic placeholders for offline structural Animatic tests."""

from __future__ import annotations

from mvstudio.director.drafting import ModelResult, ModelTask


class OfflineStructuralPort:
    """Satisfy bounded task shapes without claiming model-derived meaning."""

    model = "offline-structural-v1"

    def run(self, task: ModelTask) -> ModelResult:
        if not isinstance(task, ModelTask):
            raise ValueError("offline structural port requires a bounded ModelTask")
        if task.model != self.model:
            raise ValueError("offline structural port requires its fixed model identifier")
        if task.event_type == "lyrics.semantic_segment.requested":
            lines = task.payload.get("lines")
            if not isinstance(lines, list) or not lines:
                raise ValueError("offline structural lyrics require timed lines")
            groups = []
            for index, line in enumerate(lines, 1):
                if not isinstance(line, dict) or not isinstance(line.get("id"), str):
                    raise ValueError("offline structural lyric line is invalid")
                groups.append({
                    "id": f"structural_{index:03d}",
                    "line_ids": [line["id"]],
                    "semantic_type": "unclassified_lyric",
                    "emotion": "unclassified",
                    "summary": f"Timed lyric placeholder {index}; no semantic claim.",
                })
            return ModelResult({"groups": groups}, 0, 0)
        if task.event_type == "relationship_map.draft_requested":
            characters = task.payload.get("characters")
            groups = task.payload.get("semantic_groups")
            if not isinstance(characters, list) or not characters:
                raise ValueError("offline structural relationship task requires characters")
            if not isinstance(groups, list) or not groups:
                raise ValueError("offline structural relationship task requires lyric groups")
            profiles = []
            for index, character in enumerate(characters):
                if not isinstance(character, dict) or not isinstance(character.get("id"), str):
                    raise ValueError("offline structural character is invalid")
                profiles.append({
                    "id": character["id"],
                    "director_function": (
                        "structural lead by declared order"
                        if index == 0 else "structural counterpart by declared order"
                    ),
                    "traits": list(character.get("traits", [])),
                    "symbols": ["unassigned"],
                })
            relationships = []
            if len(profiles) > 1:
                relationships.append({
                    "pair": [profiles[0]["id"], profiles[1]["id"]],
                    "dramatic_function": "unclassified structural relationship placeholder",
                    "reveal_group": groups[-1]["id"],
                })
            return ModelResult(
                {"characters": profiles, "relationships": relationships},
                0,
                0,
            )
        raise ValueError("offline structural task is not allowlisted")
