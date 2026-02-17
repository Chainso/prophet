from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .models import Ontology


ONTOLOGY_HEADER_RE = re.compile(r"^ontology\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{$")
ID_LINE_RE = re.compile(r'^id\s+\".*\"$')

BLOCK_START_PATTERNS = [
    re.compile(r"^ontology\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^type\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^object\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^struct\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^action\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^signal\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^trigger\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^field\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^state\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^transition\s+[A-Za-z_][A-Za-z0-9_]*\s*\{$"),
    re.compile(r"^input\s*\{$"),
    re.compile(r"^output\s*\{$"),
]


def _is_block_start(stripped: str) -> bool:
    return any(pattern.match(stripped) for pattern in BLOCK_START_PATTERNS)


def _scan_block_id_presence(lines: List[str]) -> Dict[int, bool]:
    block_stack: List[int] = []
    has_id_by_line: Dict[int, bool] = {}
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _is_block_start(stripped):
            block_stack.append(idx)
            has_id_by_line[idx] = False
            continue
        if stripped == "}":
            if block_stack:
                block_stack.pop()
            continue
        if ID_LINE_RE.match(stripped) and block_stack:
            has_id_by_line[block_stack[-1]] = True
    return has_id_by_line


def _find_ontology_header_line(lines: List[str]) -> int:
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ONTOLOGY_HEADER_RE.match(stripped):
            return idx
    return 1


def _build_id_map(ontology: Ontology, source_lines: List[str]) -> Dict[int, str]:
    id_map: Dict[int, str] = {}
    id_map[_find_ontology_header_line(source_lines)] = ontology.id

    for item in ontology.types:
        id_map[item.line] = item.id

    for item in ontology.objects:
        id_map[item.line] = item.id
        for field in item.fields:
            id_map[field.line] = field.id
        for state in item.states:
            id_map[state.line] = state.id
        for transition in item.transitions:
            id_map[transition.line] = transition.id

    for item in ontology.structs:
        id_map[item.line] = item.id
        for field in item.fields:
            id_map[field.line] = field.id

    for item in ontology.action_inputs:
        id_map[item.line] = item.id
        for field in item.fields:
            id_map[field.line] = field.id

    for item in ontology.actions:
        id_map[item.line] = item.id

    for item in ontology.events:
        id_map[item.line] = item.id
        for field in item.fields:
            id_map[field.line] = field.id

    for item in ontology.triggers:
        id_map[item.line] = item.id

    return id_map


def materialize_missing_ids(text: str, ontology: Ontology) -> Tuple[str, bool]:
    lines = text.splitlines()
    has_trailing_newline = text.endswith("\n")
    has_id_by_line = _scan_block_id_presence(lines)
    id_map = _build_id_map(ontology, lines)

    insertions: List[Tuple[int, str]] = []
    for start_line, id_value in sorted(id_map.items()):
        if not id_value:
            continue
        if has_id_by_line.get(start_line, False):
            continue
        if start_line < 1 or start_line > len(lines):
            continue
        header_line = lines[start_line - 1]
        indent = re.match(r"^\s*", header_line).group(0)  # type: ignore[union-attr]
        insertions.append((start_line, f'{indent}  id "{id_value}"'))

    if not insertions:
        return text, False

    for line_no, insert_line in sorted(insertions, reverse=True):
        lines.insert(line_no, insert_line)

    out = "\n".join(lines)
    if has_trailing_newline:
        out += "\n"
    return out, True
