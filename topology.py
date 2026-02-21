"""Topology utilities for PPM IP traceback simulation."""

from __future__ import annotations

from collections import deque
from pathlib import Path
import random
from typing import Dict, Iterable, List, Set, Tuple

NodeId = str
Adjacency = Dict[NodeId, Set[NodeId]]


def read_topology(edge_file: str | Path) -> Adjacency:
    """Parse undirected edges from a topology file.

    File format: one edge per line as "A B".
    """
    path = Path(edge_file)
    if not path.exists():
        raise FileNotFoundError(f"Topology file not found: {path}")

    adj: Adjacency = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 2:
                raise ValueError(f"Invalid edge line: {line}")
            u, v = parts
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)
    return adj


def _add_edge(adj: Adjacency, u: NodeId, v: NodeId) -> None:
    adj.setdefault(u, set()).add(v)
    adj.setdefault(v, set()).add(u)


def generate_topology(
    branches: int = 4,
    routers: int = 16,
    max_hops: int = 15,
    seed: int = 42,
    edge_file: str | Path = "topology.txt",
) -> tuple[Adjacency, NodeId, Dict[int, List[NodeId]]]:
    """Generate a rooted tree-like topology centered at victim V.

    Returns:
        (adjacency, victim_id, branch_leaf_map)
    """
    if not (10 <= routers <= 20):
        raise ValueError("routers must be in [10, 20]")
    if not (3 <= branches <= 5):
        raise ValueError("branches must be in [3, 5]")

    rng = random.Random(seed)
    victim = "V"
    router_ids = [f"R{i}" for i in range(1, routers + 1)]

    # Split routers across B branches with at least one router each.
    counts = [1] * branches
    for _ in range(routers - branches):
        counts[rng.randrange(branches)] += 1

    # Build each branch as a path from victim and optionally add short side chains.
    adj: Adjacency = {victim: set()}
    branch_nodes: Dict[int, List[NodeId]] = {}
    idx = 0
    for b in range(branches):
        n_b = counts[b]
        nodes = router_ids[idx : idx + n_b]
        idx += n_b
        branch_nodes[b] = nodes

        if not nodes:
            continue

        # Decide trunk length and side-node distribution.
        trunk_len = max(1, min(len(nodes), 2 + (len(nodes) // 2)))
        trunk = nodes[:trunk_len]
        side_nodes = nodes[trunk_len:]

        prev = victim
        for node in trunk:
            _add_edge(adj, prev, node)
            prev = node

        # Attach side nodes to random trunk nodes, potentially creating depth up to +2.
        for node in side_nodes:
            attach = rng.choice(trunk)
            _add_edge(adj, attach, node)

    # Validate max hops from every router to victim.
    parent, dist = bfs_parent_tree(adj, victim)
    for r in router_ids:
        if r not in dist:
            raise ValueError(f"Disconnected router in generated topology: {r}")
        if dist[r] > max_hops:
            raise ValueError(
                f"Router {r} is {dist[r]} hops from victim, exceeds max_hops={max_hops}"
            )

    # Compute leaves for each branch under victim neighbors.
    leaves_by_branch = leaves_per_branch(adj, victim)

    # Persist edge list.
    out = Path(edge_file)
    edges: list[tuple[str, str]] = []
    for u, nbrs in adj.items():
        for v in nbrs:
            if u < v:
                edges.append((u, v))
    edges.sort()
    with out.open("w", encoding="utf-8") as fh:
        for u, v in edges:
            fh.write(f"{u} {v}\n")

    return adj, victim, leaves_by_branch


def bfs_parent_tree(adj: Adjacency, root: NodeId) -> tuple[Dict[NodeId, NodeId | None], Dict[NodeId, int]]:
    """Build BFS parent and hop distance maps from root."""
    if root not in adj:
        raise ValueError(f"Root node {root} not in topology")

    parent: Dict[NodeId, NodeId | None] = {root: None}
    dist: Dict[NodeId, int] = {root: 0}
    q: deque[NodeId] = deque([root])

    while q:
        u = q.popleft()
        for v in adj[u]:
            if v in dist:
                continue
            dist[v] = dist[u] + 1
            parent[v] = u
            q.append(v)

    return parent, dist


def path_to_root(parent: Dict[NodeId, NodeId | None], node: NodeId) -> List[NodeId]:
    """Return [node, ..., root] from parent mapping."""
    if node not in parent:
        raise ValueError(f"Node {node} missing from parent tree")

    path: List[NodeId] = []
    cur: NodeId | None = node
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return path


def build_paths_to_victim(
    adj: Adjacency,
    victim: NodeId,
    sources: Iterable[NodeId],
) -> Dict[NodeId, List[NodeId]]:
    """Build path [source, ..., victim] for each source."""
    parent, _ = bfs_parent_tree(adj, victim)
    paths: Dict[NodeId, List[NodeId]] = {}
    for src in sources:
        path = path_to_root(parent, src)
        if path[-1] != victim:
            raise ValueError(f"Source {src} not connected to victim {victim}")
        paths[src] = path
    return paths


def leaves_per_branch(adj: Adjacency, victim: NodeId) -> Dict[int, List[NodeId]]:
    """Return leaves grouped by branch index under victim's immediate neighbors."""
    neighbors = sorted(adj[victim])
    branch_map: Dict[int, List[NodeId]] = {}

    for idx, start in enumerate(neighbors):
        leaves: List[NodeId] = []
        stack: list[tuple[NodeId, NodeId]] = [(start, victim)]
        while stack:
            node, parent = stack.pop()
            children = [n for n in adj[node] if n != parent]
            if not children:
                leaves.append(node)
            else:
                for c in children:
                    stack.append((c, node))
        branch_map[idx] = sorted(set(leaves))

    return branch_map


def pick_endpoints(
    adj: Adjacency,
    victim: NodeId,
    num_attackers: int,
    seed: int = 42,
) -> tuple[List[NodeId], NodeId, Dict[NodeId, int]]:
    """Pick attackers on distinct branches and one normal user leaf.

    Returns:
        (attackers, normal_user, branch_of_leaf)
    """
    rng = random.Random(seed)
    leaves_by_branch = leaves_per_branch(adj, victim)
    valid_branches = [b for b, leaves in leaves_by_branch.items() if leaves]

    if len(valid_branches) < num_attackers:
        raise ValueError("Not enough non-empty branches for requested attackers")

    chosen_attack_branches = rng.sample(valid_branches, k=num_attackers)
    attackers = [rng.choice(leaves_by_branch[b]) for b in chosen_attack_branches]

    remaining = [b for b in valid_branches if b not in chosen_attack_branches]
    if not remaining:
        remaining = valid_branches
    normal_branch = rng.choice(remaining)
    normal_user = rng.choice(leaves_by_branch[normal_branch])

    branch_of_leaf: Dict[NodeId, int] = {}
    for b, leaves in leaves_by_branch.items():
        for leaf in leaves:
            branch_of_leaf[leaf] = b

    return attackers, normal_user, branch_of_leaf
