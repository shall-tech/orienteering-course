#!/usr/bin/env python3
"""
Orienteering Course Generator

Generates compass orienteering courses for Scouts. Creates:
  - Score cards (3x5 index card PDFs) for each course
  - An answer key (letter-size PDF) for the grader

Usage:
  python main.py                          # defaults: 20 stations, 20 courses
  python main.py --stations 10 --courses 10 --max-south 0 --max-north 50
  python main.py --seed 42                # reproducible generation
"""

import argparse
import os
from datetime import datetime

from course_generator import CourseConfig, generate_courses
from pdf_generator import generate_score_cards, generate_answer_key


def main():
    parser = argparse.ArgumentParser(
        description="Generate orienteering compass courses for Scouts."
    )

    parser.add_argument(
        "--stations", type=int, default=20,
        help="Number of stations on the line (default: 20)"
    )
    parser.add_argument(
        "--station-distance", type=float, default=5.0,
        help="Distance in feet between stations (default: 5)"
    )
    parser.add_argument(
        "--max-north", type=float, default=100.0,
        help="Max distance north of station line in feet (default: 100)"
    )
    parser.add_argument(
        "--max-south", type=float, default=100.0,
        help="Max distance south of station line in feet (default: 100)"
    )
    parser.add_argument(
        "--max-west", type=float, default=20.0,
        help="Buffer west of station 1 in feet (default: 20)"
    )
    parser.add_argument(
        "--max-east", type=float, default=20.0,
        help="Buffer east of last station in feet (default: 20)"
    )
    parser.add_argument(
        "--legs", type=int, default=3,
        help="Number of legs per course (default: 3)"
    )
    parser.add_argument(
        "--courses", type=int, default=20,
        help="Number of courses to generate (default: 20)"
    )
    parser.add_argument(
        "--min-station-gap", type=int, default=2,
        help="Minimum station number difference between start and destination (default: 2)"
    )
    parser.add_argument(
        "--min-line-angle", type=int, default=25,
        help="Reject legs within this many degrees of the station line (default: 25)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducible generation"
    )
    parser.add_argument(
        "--output", type=str, default="output",
        help="Output directory (default: output)"
    )

    args = parser.parse_args()

    # Build the config
    config = CourseConfig(
        stations=args.stations,
        station_distance=args.station_distance,
        max_north=args.max_north,
        max_south=args.max_south,
        max_west=args.max_west,
        max_east=args.max_east,
        num_legs=args.legs,
        num_courses=args.courses,
        min_station_gap=args.min_station_gap,
        min_line_angle=args.min_line_angle,
        seed=args.seed,
    )

    # Print summary of the setup
    line_length = (config.stations - 1) * config.station_distance
    print(f"Orienteering Course Generator")
    print(f"  Stations:       {config.stations} (spaced {config.station_distance}' apart)")
    print(f"  Station line:   {line_length}' total")
    print(f"  Bounds:         N={config.max_north}' S={config.max_south}' "
          f"W={config.max_west}' E={config.max_east}'")
    print(f"  Legs/course:    {config.num_legs}")
    print(f"  Courses:        {config.num_courses}")
    print(f"  Min station gap: {config.min_station_gap}")
    if config.seed is not None:
        print(f"  Seed:           {config.seed}")
    print()

    # Generate courses
    print("Generating courses...")
    courses = generate_courses(config)
    print(f"  Generated {len(courses)} courses successfully.")

    # Timestamp for all outputs (display and file naming)
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    file_stamp = now.strftime("%Y%m%d_%H%M%S")

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Generate score cards PDF
    cards_path = os.path.join(args.output, f"score_cards_{file_stamp}.pdf")
    print(f"  Writing score cards to {cards_path}")
    generate_score_cards(courses, cards_path, timestamp=timestamp)

    # Generate answer key PDF
    key_path = os.path.join(args.output, f"answer_key_{file_stamp}.pdf")
    print(f"  Writing answer key to {key_path}")
    generate_answer_key(courses, config.num_legs, key_path, timestamp=timestamp)

    print()
    print("Done! Output files:")
    print(f"  Score cards:  {cards_path}")
    print(f"  Answer key:   {key_path}")


if __name__ == "__main__":
    main()
