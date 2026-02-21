# Homework 1: PPM IP Traceback Simulation

This project implements a Probabilistic Packet Marking (PPM) simulation comparing:
- Node Sampling
- Edge Sampling

It supports two experiments:
1. Single attacker + one normal user
2. Two attackers + one normal user (attackers constrained to different branches)

## Requirements
- Python 3.10+
- `matplotlib`

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install matplotlib
```

## Run Simulation
```powershell
python simulate.py
```
This generates:
- `topology.txt`
- `results_single.csv`
- `results_double.csv`

## Generate Plots
```powershell
python plot_results.py
```
This generates 6 plots under `plots/`:
- `plots/single_x10.png`
- `plots/single_x100.png`
- `plots/single_x1000.png`
- `plots/double_x10.png`
- `plots/double_x100.png`
- `plots/double_x1000.png`

## Project Files
- `topology.py`: topology generation, reading, BFS/path utilities, endpoint selection helpers
- `ppm_node.py`: node sampling packet marking, collection, reconstruction, attacker prediction heuristic
- `ppm_edge.py`: edge sampling packet marking, collection, reconstruction, attacker prediction heuristic
- `simulate.py`: experiment runner, traffic model, evaluation, CSV export, runtime summary
- `plot_results.py`: plotting from CSV to PNG files
- `report_template.md`: writeup template with required sections
- `README.md`: usage instructions

## Accuracy Metrics
- Single attacker: `1` if predicted leaf equals true attacker leaf, else `0`
- Double attacker: `1` if predicted set of two leaves exactly matches true set, else `0`
- Final reported accuracy is average over trials.
