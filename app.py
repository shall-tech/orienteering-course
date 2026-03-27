"""
Streamlit UI for the Orienteering Course Generator.

Run with:  streamlit run app.py
"""

import io
import math
import os
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import streamlit as st

from course_generator import CourseConfig, generate_courses, station_x, move
from pdf_generator import generate_score_cards, generate_answer_key


# -- Color palette for course paths -----------------------------------------
COURSE_COLORS = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
    "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990",
    "#dcbeff", "#9A6324", "#800000", "#aaffc3", "#808000",
    "#000075", "#a9a9a9", "#e6beff", "#ffe119", "#000000",
]


def _draw_course_map(courses_to_plot, config):
    """Draw a matplotlib figure showing stations, bounds, and course paths."""
    line_length = (config.stations - 1) * config.station_distance

    # Bounding box
    x_min = -config.max_west
    x_max = line_length + config.max_east
    y_min = -config.max_south
    y_max = config.max_north

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    # Draw bounding box
    rect = patches.Rectangle(
        (x_min, y_min), x_max - x_min, y_max - y_min,
        linewidth=1.5, edgecolor="#999999", facecolor="#f9f9f9",
        linestyle="--", label="Boundary"
    )
    ax.add_patch(rect)

    # Draw station line
    ax.plot([0, line_length], [0, 0], color="#333333", linewidth=2, zorder=3)

    # Draw station markers
    for s in range(1, config.stations + 1):
        sx = station_x(s, config.station_distance)
        ax.plot(sx, 0, marker="s", color="#333333", markersize=6, zorder=4)
        # Label every station for small counts, every other for large counts
        if config.stations <= 25 or s % 2 == 1 or s == config.stations:
            ax.annotate(
                str(s), (sx, 0), textcoords="offset points",
                xytext=(0, -12), ha="center", fontsize=7, color="#333333"
            )

    # Plot each course
    for i, course in enumerate(courses_to_plot):
        color = COURSE_COLORS[i % len(COURSE_COLORS)]
        sx = station_x(course.start_station, config.station_distance)
        cx, cy = sx, 0.0

        # Collect path points
        path_x = [cx]
        path_y = [cy]
        for leg in course.legs:
            cx, cy = move(cx, cy, leg.azimuth, leg.distance)
            path_x.append(cx)
            path_y.append(cy)

        # Draw path with arrows
        for j in range(len(path_x) - 1):
            dx = path_x[j + 1] - path_x[j]
            dy = path_y[j + 1] - path_y[j]
            ax.annotate(
                "", xy=(path_x[j + 1], path_y[j + 1]),
                xytext=(path_x[j], path_y[j]),
                arrowprops=dict(
                    arrowstyle="-|>", color=color, lw=1.5,
                    shrinkA=0, shrinkB=0
                ),
                zorder=5,
            )

        # Mark start with a circle
        ax.plot(path_x[0], path_y[0], "o", color=color, markersize=5, zorder=6)

        # Label the course at the midpoint of the first leg
        mid_x = (path_x[0] + path_x[1]) / 2
        mid_y = (path_y[0] + path_y[1]) / 2
        ax.annotate(
            course.label, (mid_x, mid_y), fontsize=7, fontweight="bold",
            color=color, ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                      edgecolor=color, alpha=0.8),
            zorder=7,
        )

    # Formatting
    ax.set_xlabel("East-West (ft)")
    ax.set_ylabel("North-South (ft)")
    ax.set_aspect("equal")
    margin = max(5, (x_max - x_min) * 0.05)
    ax.set_xlim(x_min - margin, x_max + margin)
    ax.set_ylim(y_min - margin, y_max + margin)
    ax.axhline(y=0, color="#cccccc", linewidth=0.5, zorder=1)
    ax.grid(True, alpha=0.3, zorder=0)

    title = "All Courses" if len(courses_to_plot) > 1 else f"Course {courses_to_plot[0].label}"
    ax.set_title(title, fontsize=12, fontweight="bold")

    fig.tight_layout()
    return fig


st.set_page_config(page_title="Orienteering Course Generator", layout="centered")
st.title("Orienteering Course Generator")
st.markdown("Generate compass orienteering courses for Scouts. "
            "Configure your space, generate courses, and download the PDFs.")

# -- Sidebar: all configuration parameters ----------------------------------
st.sidebar.header("Course Settings")

stations = st.sidebar.number_input("Number of stations", min_value=3, max_value=100, value=20)
station_distance = st.sidebar.number_input("Station distance (ft)", min_value=1.0, max_value=50.0, value=5.0, step=0.5)
courses = st.sidebar.number_input("Number of courses", min_value=1, max_value=100, value=20)
legs = st.sidebar.number_input("Legs per course", min_value=2, max_value=10, value=3)
min_station_gap = st.sidebar.number_input("Min station gap", min_value=1, max_value=10, value=2)

st.sidebar.header("Space Boundaries (ft)")
max_north = st.sidebar.number_input("Max north", min_value=0.0, max_value=500.0, value=100.0, step=5.0)
max_south = st.sidebar.number_input("Max south", min_value=0.0, max_value=500.0, value=100.0, step=5.0)
max_west = st.sidebar.number_input("Max west", min_value=0.0, max_value=100.0, value=20.0, step=5.0)
max_east = st.sidebar.number_input("Max east", min_value=0.0, max_value=100.0, value=20.0, step=5.0)

st.sidebar.header("Advanced")
seed_input = st.sidebar.text_input("Random seed (blank = random)", value="")
seed = int(seed_input) if seed_input.strip().isdigit() else None

# -- Main area: summary and generate button ----------------------------------
line_length = (stations - 1) * station_distance

st.subheader("Setup Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Stations", stations)
col2.metric("Station Line", f"{line_length:.0f} ft")
col3.metric("Courses", courses)
col4.metric("Legs", legs)

col4, col5 = st.columns(2)
col4.metric("N/S Extent", f"{max_north:.0f} / {max_south:.0f} ft")
col5.metric("W/E Buffer", f"{max_west:.0f} / {max_east:.0f} ft")

st.divider()

if st.button("Generate Courses", type="primary", width="stretch"):
    config = CourseConfig(
        stations=stations,
        station_distance=station_distance,
        max_north=max_north,
        max_south=max_south,
        max_west=max_west,
        max_east=max_east,
        num_legs=legs,
        num_courses=courses,
        min_station_gap=min_station_gap,
        seed=seed,
    )

    try:
        with st.spinner("Generating courses..."):
            generated = generate_courses(config)

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")
        file_stamp = now.strftime("%Y%m%d_%H%M%S")

        # Generate PDFs into memory buffers
        cards_buf = io.BytesIO()
        generate_score_cards(generated, cards_buf, timestamp=timestamp)
        cards_buf.seek(0)

        key_buf = io.BytesIO()
        generate_answer_key(generated, config.num_legs, key_buf, timestamp=timestamp)
        key_buf.seek(0)

        # Store everything in session state so it survives reruns
        st.session_state["generated"] = generated
        st.session_state["config"] = config
        st.session_state["timestamp"] = timestamp
        st.session_state["file_stamp"] = file_stamp
        st.session_state["cards_pdf"] = cards_buf.getvalue()
        st.session_state["key_pdf"] = key_buf.getvalue()

    except RuntimeError as e:
        st.error(str(e))

# -- Display results if we have them ----------------------------------------
if "generated" in st.session_state:
    generated = st.session_state["generated"]
    config = st.session_state["config"]
    timestamp = st.session_state["timestamp"]
    file_stamp = st.session_state["file_stamp"]

    st.success(f"Generated {len(generated)} courses!")

    # Show the answer key as a preview table
    st.subheader("Answer Key Preview")
    table_data = []
    for c in generated:
        row = {"Course": c.label, "Start": c.start_station}
        for i, leg in enumerate(c.legs):
            row[f"Leg {i+1}"] = f"{leg.azimuth}° / {leg.distance}'"
        row["Dest."] = c.destination
        table_data.append(row)
    st.dataframe(table_data, width="stretch", hide_index=True)

    # Course map visualization
    st.subheader("Course Map")

    # Dropdown: "All Courses" plus each individual course
    course_options = ["All Courses"] + [
        f"Course {c.label} (Stn {c.start_station} → {c.destination})"
        for c in generated
    ]
    selected = st.selectbox("View", course_options, key="course_select")

    if selected == "All Courses":
        courses_to_plot = generated
    else:
        idx = course_options.index(selected) - 1
        courses_to_plot = [generated[idx]]

    fig = _draw_course_map(courses_to_plot, config)
    st.pyplot(fig)
    plt.close(fig)

    # Download buttons
    st.divider()
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label="Download Score Cards",
            data=st.session_state["cards_pdf"],
            file_name=f"score_cards_{file_stamp}.pdf",
            mime="application/pdf",
            width="stretch",
        )
    with dl2:
        st.download_button(
            label="Download Answer Key",
            data=st.session_state["key_pdf"],
            file_name=f"answer_key_{file_stamp}.pdf",
            mime="application/pdf",
            width="stretch",
        )
