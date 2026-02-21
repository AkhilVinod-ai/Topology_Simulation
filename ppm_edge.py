"""Edge Sampling implementation for PPM."""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, Optional, Tuple

Edge = Tuple[str, str]
EdgeCounts = DefaultDict[int, DefaultDict[Edge, int]]


def _canon_edge(u: str, v: str) -> Edge:
    return (u, v) if u <= v else (v, u)


def init_edge_counts() -> EdgeCounts:
    """Create nested counters counts_edge[dist][edge] += 1."""
    return defaultdict(lambda: defaultdict(int))


def edge_marking_step(
    packet: dict,
    prev_router: str,
    curr_router: str,
    p: float,
    rng,
) -> None:
    """Apply one hop's edge-sampling marking action to a packet."""
    edge = _canon_edge(prev_router, curr_router)

    if rng.random() < p:
        packet["mark"] = edge
        packet["dist"] = 0
    elif packet["mark"] is not None:
        packet["dist"] += 1


def edge_victim_collect(packet: dict, counts_edge: EdgeCounts) -> None:
    """Store packet edge mark observed at victim."""
    mark = packet.get("mark")
    dist = packet.get("dist")
    if mark is None or dist is None:
        return
    u, v = mark
    counts_edge[int(dist)][_canon_edge(str(u), str(v))] += 1


def edge_reconstruct(counts_edge: EdgeCounts, max_hops: int) -> Dict[int, Optional[Edge]]:
    """For each distance d, choose the most frequent edge mark."""
    recon: Dict[int, Optional[Edge]] = {}
    for d in range(max_hops + 1):
        bucket = counts_edge.get(d)
        if not bucket:
            recon[d] = None
            continue
        # Per-distance majority vote over observed edge marks.
        recon[d] = max(bucket.items(), key=lambda kv: kv[1])[0]
    return recon


def edge_predict_attackers(counts_edge: EdgeCounts, k: int) -> list[str]:
    """Predict top-k attackers from farthest-edge endpoint scoring.

    Heuristic:
    - Each marked edge contributes weighted score (dist+1) * count to both endpoints.
    - Farthest-edge marks emphasize upstream attack source side.
    - Return highest scoring endpoints as attacker candidates.
    """
    if k <= 0:
        return []

    score: Dict[str, float] = {}
    for dist, bucket in counts_edge.items():
        # Farthest marks are weighted more heavily to preserve source-side signal.
        weight = float(dist + 1)
        for (u, v), cnt in bucket.items():
            inc = weight * cnt
            # Edge support contributes to both endpoints before ranking candidates.
            score[u] = score.get(u, 0.0) + inc
            score[v] = score.get(v, 0.0) + inc

    if not score:
        return []

    ranked = sorted(score.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    return [node for node, _ in ranked[:k]]
