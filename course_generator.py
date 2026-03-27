"""
course_generator.py

Core logic for generating orienteering courses.

Coordinate system:
  - Stations sit along the x-axis (y=0), evenly spaced west-to-east.
  - Station 1 is at x=0, Station N is at x=(N-1)*station_distance.
  - North = +y, South = -y, East = +x, West = -x.
  - Azimuths: 0°=North, 90°=East, 180°=South, 270°=West.
"""

import math
import random
from dataclasses import dataclass, field


@dataclass
class Leg:
    """A single leg of a course: azimuth in degrees and distance in feet."""
    azimuth: int   # whole degrees, 0-359
    distance: int  # whole feet


@dataclass
class Course:
    """A generated course with a start station, legs, and destination station."""
    label: str            # e.g. "A", "B", ... "AA"
    start_station: int    # 1-based station number
    destination: int      # 1-based station number
    legs: list            # list of Leg objects


@dataclass
class CourseConfig:
    """All the parameters needed to generate a set of courses."""
    stations: int = 20
    station_distance: float = 5.0
    max_north: float = 100.0
    max_south: float = 100.0
    max_west: float = 20.0
    max_east: float = 20.0
    num_legs: int = 3
    num_courses: int = 20
    min_station_gap: int = 2
    seed: int = None


def course_label(index: int) -> str:
    """Convert a 0-based index to a letter label: 0->A, 25->Z, 26->AA, etc."""
    label = ""
    i = index
    while True:
        label = chr(ord('A') + (i % 26)) + label
        i = i // 26 - 1
        if i < 0:
            break
    return label


def azimuth_distance(x1: float, y1: float, x2: float, y2: float):
    """
    Compute azimuth (degrees, 0=N, clockwise) and distance (feet)
    from point (x1,y1) to point (x2,y2).
    Returns (azimuth_degrees, distance_feet) as floats.
    """
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 0.001:
        return 0.0, 0.0
    # math.atan2 gives angle from +x axis, counter-clockwise.
    # We need angle from +y axis (north), clockwise.
    angle_rad = math.atan2(dx, dy)  # atan2(east, north)
    angle_deg = math.degrees(angle_rad) % 360
    return angle_deg, dist


def move(x: float, y: float, azimuth_deg: int, distance_ft: int):
    """
    Move from (x,y) along the given azimuth for the given distance.
    Returns new (x, y).
    """
    rad = math.radians(azimuth_deg)
    dx = distance_ft * math.sin(rad)
    dy = distance_ft * math.cos(rad)
    return x + dx, y + dy


def station_x(station_num: int, station_distance: float) -> float:
    """Get the x-coordinate for a 1-based station number."""
    return (station_num - 1) * station_distance


def _bounding_box(config: CourseConfig):
    """
    Return (x_min, x_max, y_min, y_max) for the playable area.
    """
    line_length = (config.stations - 1) * config.station_distance
    x_min = -config.max_west
    x_max = line_length + config.max_east
    y_min = -config.max_south
    y_max = config.max_north
    return x_min, x_max, y_min, y_max


def _in_bounds(x: float, y: float, bbox) -> bool:
    """Check if a point is within the bounding box (with a tiny tolerance)."""
    x_min, x_max, y_min, y_max = bbox
    tol = 0.5  # half a foot of tolerance
    return (x_min - tol <= x <= x_max + tol and
            y_min - tol <= y <= y_max + tol)


def _auto_scale_distances(config: CourseConfig):
    """
    Compute reasonable min/max leg distances based on the bounding box.
    Returns (min_leg_dist, max_leg_dist) in feet.
    """
    bbox = _bounding_box(config)
    x_span = bbox[1] - bbox[0]
    y_span = bbox[3] - bbox[2]
    longest = max(x_span, y_span)

    max_leg = max(int(longest * 0.80), 5)
    min_leg = max(int(longest * 0.15), 3)

    # Make sure min < max
    if min_leg >= max_leg:
        min_leg = max(max_leg - 2, 1)

    return min_leg, max_leg


def generate_courses(config: CourseConfig) -> list:
    """
    Generate a list of Course objects based on the given config.
    Returns a list of Course objects.
    """
    if config.seed is not None:
        random.seed(config.seed)

    bbox = _bounding_box(config)
    min_leg, max_leg = _auto_scale_distances(config)

    courses = []

    for course_idx in range(config.num_courses):
        label = course_label(course_idx)
        course = _generate_single_course(
            label, config, bbox, min_leg, max_leg
        )
        courses.append(course)

    return courses


def _generate_single_course(label, config, bbox, min_leg, max_leg,
                            max_attempts=500):
    """
    Generate one course. Retries up to max_attempts times to find a valid
    set of legs that stay in bounds.
    """
    for attempt in range(max_attempts):
        # Pick random start station
        start = random.randint(1, config.stations)

        # Pick random destination at least min_station_gap away
        valid_dests = [
            s for s in range(1, config.stations + 1)
            if abs(s - start) >= config.min_station_gap
        ]
        if not valid_dests:
            continue
        dest = random.choice(valid_dests)

        # Starting position
        cx = station_x(start, config.station_distance)
        cy = 0.0

        # Target position
        tx = station_x(dest, config.station_distance)
        ty = 0.0

        legs = []
        valid = True

        # Generate intermediate legs (all but the last)
        for leg_i in range(config.num_legs - 1):
            az = random.randint(0, 359)
            dist = random.randint(min_leg, max_leg)

            nx, ny = move(cx, cy, az, dist)

            if not _in_bounds(nx, ny, bbox):
                valid = False
                break

            legs.append(Leg(azimuth=az, distance=dist))
            cx, cy = nx, ny

        if not valid:
            continue

        # Compute the final leg back to the destination station
        final_az_exact, final_dist_exact = azimuth_distance(cx, cy, tx, ty)
        final_az = round(final_az_exact) % 360
        final_dist = round(final_dist_exact)

        # Skip if final leg is too short (would be trivial) or too long
        if final_dist < max(min_leg // 2, 2):
            continue

        # Check that the final leg path endpoint is in bounds
        fx, fy = move(cx, cy, final_az, final_dist)
        if not _in_bounds(fx, fy, bbox):
            continue

        legs.append(Leg(azimuth=final_az, distance=final_dist))

        return Course(
            label=label,
            start_station=start,
            destination=dest,
            legs=legs,
        )

    raise RuntimeError(
        f"Could not generate course '{label}' after {max_attempts} attempts. "
        "Try relaxing the bounds or reducing min-station-gap."
    )
