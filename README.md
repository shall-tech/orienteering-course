# Orienteering Course Generator

A Python tool for generating compass orienteering courses for Scouts. Set up numbered stations in a line, and the tool generates randomized multi-leg compass courses that start at one station and end at another.

## How the Game Works

1. Set up numbered stations in a straight west-to-east line, evenly spaced (e.g., 20 stations, 5 feet apart).
2. Each Scout gets a score card with a starting station and a series of compass bearings and distances.
3. The Scout navigates each leg using a compass and pacing, then identifies which station they landed on.
4. The grader checks against the answer key.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Default: 20 stations, 5' apart, 20 courses, 3 legs each
python3 main.py

# Reproducible generation
python3 main.py --seed 42

# Gym setup: 10 stations on the south wall, 3' apart
python3 main.py --stations 10 --station-distance 3 --max-south 0 --max-north 50 --max-west 5 --max-east 5 --courses 10
```

## Output

- **Score cards** (`score_cards_<timestamp>.pdf`) — 3"×5" pages, one per course. Print directly to index cards.
- **Answer key** (`answer_key_<timestamp>.pdf`) — Letter-size reference for the grader.

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--stations` | 20 | Number of stations on the line |
| `--station-distance` | 5 | Feet between stations |
| `--max-north` | 100 | Max distance north of station line (ft) |
| `--max-south` | 100 | Max distance south of station line (ft) |
| `--max-west` | 20 | Buffer west of station 1 (ft) |
| `--max-east` | 20 | Buffer east of last station (ft) |
| `--legs` | 3 | Legs per course |
| `--courses` | 20 | Number of courses to generate |
| `--min-station-gap` | 2 | Minimum station difference between start and end |
| `--seed` | random | Random seed for reproducibility |
| `--output` | `output/` | Output directory |

## How It Works

Stations are placed along the x-axis. For each course, the generator picks a random start and destination station (at least `--min-station-gap` apart), generates random intermediate legs that stay within the bounding box, then computes the final leg to land back on the destination station. Leg distances auto-scale to fit the configured space.
