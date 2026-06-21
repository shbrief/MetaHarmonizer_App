"""Active-learning review ordering (G7).

Surfaces the mappings that actually need a human and keeps look-alikes together
so a curator can clear a whole group in one batch action. This is **queue
ordering only** — it never changes, hides, or auto-accepts a mapping.

Design (chosen over classic margin-sampling/diversity, which optimizes a
*model's* information gain by showing the most-different item next — the wrong
goal for a human reviewer):

  - **Risky first:** order by confidence ascending, so the least-certain
    mappings are reviewed first while attention is fresh.
  - **Group similar:** mappings the engine sent to the same target field are
    grouped and kept *adjacent*, so a curator can batch-accept/reject the whole
    look-alike set in one motion instead of re-loading context per row.
  - **Per-curator / per-study:** the queue is computed from one study's
    *pending* mappings, so as the curator clears decisions the queue naturally
    re-ranks (accepted/rejected drop out; the next risky group surfaces).

Pure functions — no DB, no engine — so the ordering is fully testable.
"""

from __future__ import annotations

from typing import Any

# Mappings at/above this confidence are in the auto-accept band. The queue still
# includes them (nothing is hidden), but the risky ones lead.
SAFE_CONFIDENCE = 0.90


def _confidence(m: dict[str, Any]) -> float:
    c = m.get("confidence_score")
    try:
        return float(c) if c is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _group_key(m: dict[str, Any]) -> str:
    """Items sharing a suggested target field form one batchable group.

    Falls back to ``__unmapped__`` so columns with no suggestion cluster
    together (they always need a manual decision and read best as a set).
    """
    target = m.get("curator_field") or m.get("matched_field")
    if not target:
        return "__unmapped__"
    return str(target).strip().lower()


def build_review_queue(mappings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the *pending* mappings, ordered risky-first and grouped.

    Each returned row is the original mapping dict plus:
      - ``group_key``  : the shared target (or ``__unmapped__``);
      - ``group_size`` : how many pending mappings share that group;
      - ``group_min_confidence`` : the group's lowest confidence (its risk).

    Groups are ordered by their riskiest member; within a group, by ascending
    confidence then column name (stable, predictable for keyboard review). The
    grouping keeps look-alikes adjacent so the existing batch accept/reject can
    clear them together.
    """
    pending = [m for m in mappings if m.get("status") == "pending"]

    groups: dict[str, list[dict[str, Any]]] = {}
    for m in pending:
        groups.setdefault(_group_key(m), []).append(m)

    group_min: dict[str, float] = {
        key: min(_confidence(m) for m in members) for key, members in groups.items()
    }

    # Riskiest group (lowest min confidence) first; ties by key for determinism.
    # ``__unmapped__`` members have confidence ~0, so that group leads.
    ordered_keys = sorted(groups, key=lambda k: (group_min[k], k))

    out: list[dict[str, Any]] = []
    for key in ordered_keys:
        members = sorted(
            groups[key],
            key=lambda m: (_confidence(m), str(m.get("raw_column") or "")),
        )
        for m in members:
            out.append(
                {
                    **m,
                    "group_key": key,
                    "group_size": len(members),
                    "group_min_confidence": round(group_min[key], 4),
                }
            )
    return out


def queue_stats(queue: list[dict[str, Any]]) -> dict[str, Any]:
    """Summary for the audit trail / UI: how the queue is shaped.

    ``batchable_groups`` counts groups with more than one pending member — where
    batch accept/reject saves the most time.
    """
    groups: dict[str, int] = {}
    risky = 0
    for m in queue:
        groups[m["group_key"]] = groups.get(m["group_key"], 0) + 1
        if _confidence(m) < SAFE_CONFIDENCE:
            risky += 1
    return {
        "pending": len(queue),
        "groups": len(groups),
        "batchable_groups": sum(1 for n in groups.values() if n > 1),
        "risky": risky,
    }
