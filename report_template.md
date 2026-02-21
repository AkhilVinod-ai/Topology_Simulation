# Homework 1 Report Template: Probabilistic Packet Marking (PPM)

## Introduction
This report presents a simulation study of IP traceback using Probabilistic Packet Marking (PPM). Two marking variants are compared:
1. Node Sampling
2. Edge Sampling

The objective is to identify attacker source leaves in a tree-like router topology under mixed legitimate and attack traffic.

## Topology and Traffic Model
- Victim node: `V`
- Router count: `N = 16` (`R1` ... `R16`)
- Branches from victim: `B = 4`
- Maximum attacker-to-victim hop distance constraint: `d <= 15`
- Topology shape: tree-like graph rooted at `V`

Traffic model:
- Normal user rate: `1` packet per timestep
- Attacker rate: `x` packets per timestep per attacker
- Tested attack intensity: `x in {10, 100, 1000}`
- Marking probability sweep: `p in {0.2, 0.4, 0.5, 0.6, 0.8}`
- Trials per setting: `RUNS = 10`

Experiments:
1. Single attacker + one normal user
2. Two attackers + one normal user, with attackers on distinct branches

## PPM Algorithms (Node vs Edge)
### Node Sampling
Each router marks a packet with its own node ID with probability `p`, resetting mark distance to `0`. Otherwise, if the packet already has a mark, distance increments by one per hop.

### Edge Sampling
Each traversed edge marks a packet with edge ID `(u, v)` with probability `p`, resetting distance to `0`. Otherwise, existing marked distance increments by one per hop.

Reconstruction at victim:
- For each observed distance bucket, the most frequent mark is selected.
- Candidate attacker leaves are scored by how strongly their source-to-victim paths match observed mark counts.

## Accuracy Metric
Single attacker accuracy:
- `accuracy = 1` if predicted attacker leaf equals true attacker leaf, else `0`.

Double attacker accuracy:
- `accuracy = 1` if predicted set of two attacker leaves equals true attacker set, else `0`.

Reported metric:
- Average accuracy over all `RUNS` trials for each `(p, x)` pair.

## Results
Include and discuss:
- `plots/single_x10.png`
- `plots/single_x100.png`
- `plots/single_x1000.png`
- `plots/double_x10.png`
- `plots/double_x100.png`
- `plots/double_x1000.png`

Also summarize trends from:
- `results_single.csv`
- `results_double.csv`

## Physical Significance
Interpretation guidance:
- Effect of `p`:
  - Very low `p` yields sparse traceback marks and weak reconstruction.
  - Very high `p` causes frequent re-marking near victim, which can suppress far upstream information.
  - Mid-range `p` often balances upstream visibility and mark availability.
- Effect of attack intensity `x`:
  - Larger `x` increases attacker signal relative to normal traffic and should improve attacker identifiability.
- Two attackers case:
  - Mixed attack streams can overlap in shared near-victim segments.
  - Distinct-branch attackers remain more separable than same-branch sources.
  - Ambiguity rises with topology overlap and insufficient packet evidence.

## Conclusion
State which method performed better across settings and why, referencing signal richness, distance information, and branch separability. Mention limitations (tree simplification, fixed rates, finite trials) and possible extensions (dynamic routing, noisy links, varied packet loss, larger topologies).
