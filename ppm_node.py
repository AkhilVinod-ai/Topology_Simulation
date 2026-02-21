"""Node Sampling implementation for PPM."""

from __future__ import annotations

from collections import defaultdict
from typing import DefaultDict, Dict, Optional

NodeCounts = DefaultDict[int, DefaultDict[str, int]]


def init_node_counts() -> NodeCounts:
    """Create nested counters counts[dist][node] += 1."""
    return defaultdict(lambda: defaultdict(int))


def node_marking_step(
    packet: dict,
    router_id: str,
    p: float,
    rng,
) -> None:
    """Apply one router's node-sampling marking action to a packet."""
    if rng.random() < p:
        packet["mark"] = router_id
        packet["dist"] = 0
    elif packet["mark"] is not None:
        packet["dist"] += 1


def node_victim_collect(packet: dict, counts: NodeCounts) -> None:
    """Store packet mark observed at victim."""
    mark = packet.get("mark")
    dist = packet.get("dist")
    if mark is None or dist is None:
        return
    counts[int(dist)][str(mark)] += 1


def node_reconstruct(counts: NodeCounts, max_hops: int) -> Dict[int, Optional[str]]:
    """For each distance d, choose the most frequent node mark."""
    recon: Dict[int, Optional[str]] = {}
    for d in range(max_hops + 1):
        bucket = counts.get(d)
        if not bucket:
            recon[d] = None
            continue
        # Per-distance majority vote used as the reconstructed mark.
        recon[d] = max(bucket.items(), key=lambda kv: kv[1])[0]
    return recon


def node_predict_attackers(counts: NodeCounts, k: int) -> list[str]:
    """Predict top-k attacker nodes using farthest-dist dominance heuristic.

    Heuristic:
    - Aggregate score per node as weighted count by (dist+1).
    - Farthest marks are weighted more because they indicate upstream routers/leaves.
    - Return highest-scoring k unique nodes.
    """
    if k <= 0:
        return []

    score: Dict[str, float] = {}
    farthest_seen = -1
    for dist, bucket in counts.items():
        if not bucket:
            continue
        farthest_seen = max(farthest_seen, dist)
        # Larger distance marks are weighted up to emphasize upstream evidence.
        weight = float(dist + 1)
        for node, cnt in bucket.items():
            score[node] = score.get(node, 0.0) + (weight * cnt)

    if not score:
        return []

    ranked = sorted(score.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    return [node for node, _ in ranked[:k]]
