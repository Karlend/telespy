import io
import os
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from telespy.tracked import log_path
from telespy.globals import DATETIME_FORMAT


def calculate_color(frequency: float) -> str:
    """Calculate color based on frequency (0.0 to 1.0)."""
    red = max(0, min(255, int(frequency * 255)))  # Ensure red is in range [0, 255]
    green = max(0, min(255, int((1 - frequency) * 255)))  # Ensure green is in range [0, 255]
    return f"#{red:02x}{green:02x}00"

def create_monthly_activity_plot(data: dict, days: int) -> bytes:
    """Create activity plot for ``user_id`` grouped by days of the month."""

    days_in_month = data["days_in_month"]
    activity_periods = data["activity_periods_month"]
    frequency_matrix = data["frequency_matrix_month"]
    total_frequency = [sum(hour) for hour in zip(*frequency_matrix)]
    max_days = data["max_days"]  # Use the full period for normalization

    plt.figure(figsize=(10, 10))

    # Main graph: Total online time in hours
    plt.subplot(2, 1, 1)
    plt.bar(range(1, 32), days_in_month, color="skyblue")
    plt.xlabel("Day of Month")
    plt.ylabel("Total Online Hours (max 24)")
    plt.title(f"Total Online Time by Day for last {days} days")
    plt.xticks(range(1, 32))
    plt.ylim(0, 24)  # Set fixed Y-axis limit to 24 hours
    plt.yticks(range(0, 25))  # Display all hours as numbers
    plt.grid(axis="y", linestyle="--", alpha=0.7)  # Add horizontal grid lines

    # Secondary graph: Activity periods
    plt.subplot(2, 1, 2)
    if any(total_frequency):  # Only draw activity periods if there is data
        for day_index, periods in enumerate(activity_periods):
            for start, duration in periods:
                hour_index = int(start)
                frequency = total_frequency[hour_index] / max_days  # Normalize frequency by the full period
                color = calculate_color(frequency)
                plt.bar(day_index + 1, duration, bottom=start, color=color)  # Draw block with frequency-based color
    else:
        plt.text(15, 12, "No activity data available", ha="center", va="center", fontsize=12, color="red")
    plt.xlabel("Day of Month")
    plt.ylabel("Activity Periods (hours)")
    plt.title(f"Activity Periods by Day for last {days} days")
    plt.xticks(range(1, 32))
    plt.ylim(0, 24)  # Set fixed Y-axis limit to 24 hours
    plt.yticks(range(0, 25))  # Display all hours as numbers
    plt.grid(axis="y", linestyle="--", alpha=0.7)  # Add horizontal grid lines

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    buffer.name = "monthly_activity_plot.png"
    return buffer


def create_weekly_activity_plot(data: dict, days: int) -> bytes:
    """Create activity plot for ``user_id`` grouped by days of the week."""

    days_of_week = data["days_of_week"]
    activity_periods = data["activity_periods_week"]
    frequency_matrix = data["frequency_matrix_week"]
    total_frequency = [sum(hour) for hour in zip(*frequency_matrix)]
    max_days = data["max_days"]  # Use the full period for normalization

    plt.figure(figsize=(10, 10))

    # Main graph: Total online time in hours
    plt.subplot(2, 1, 1)
    plt.bar(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], days_of_week, color="skyblue")
    plt.xlabel("Day of Week")
    plt.ylabel("Total Online Hours (max 24)")
    plt.title(f"Total Online Time by Day of Week for last {days} days")
    plt.ylim(0, 24)  # Set fixed Y-axis limit to 24 hours
    plt.yticks(range(0, 25))  # Display all hours as numbers
    plt.grid(axis="y", linestyle="--", alpha=0.7)  # Add horizontal grid lines

    # Secondary graph: Activity periods
    plt.subplot(2, 1, 2)
    if any(total_frequency):  # Only draw activity periods if there is data
        for day_index, periods in enumerate(activity_periods):
            for start, duration in periods:
                hour_index = int(start)
                frequency = total_frequency[hour_index] / max_days  # Normalize frequency by the full period
                color = calculate_color(frequency)
                plt.bar(day_index, duration, bottom=start, color=color)  # Draw block with frequency-based color
    else:
        plt.text(3, 12, "No activity data available", ha="center", va="center", fontsize=12, color="red")
    plt.xlabel("Day of Week")
    plt.ylabel("Activity Periods (hours)")
    plt.title(f"Activity Periods by Day of Week for last {days} days")
    plt.xticks(range(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    plt.ylim(0, 24)  # Set fixed Y-axis limit to 24 hours
    plt.yticks(range(0, 25))  # Display all hours as numbers
    plt.grid(axis="y", linestyle="--", alpha=0.7)  # Add horizontal grid lines

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    buffer.name = "weekly_activity_plot.png"
    return buffer


def create_daily_activity_plot(data: dict, days: int) -> bytes:
    hours = data["hours"]
    activity_periods = data["activity_periods_hour"]
    frequency_matrix = data["frequency_matrix_hour"]
    max_days = data["max_days"]  # Use the full period for normalization

    plt.figure(figsize=(10, 10))

    # Main graph: Total online time in hours
    plt.subplot(2, 1, 1)
    plt.bar(range(24), hours, color="skyblue")
    plt.xlabel("Hour of Day")
    plt.ylabel("Total Online Hours (max 24)")
    plt.title(f"Total Online Time by Hour for last {days} days")
    plt.xticks(range(24))
    plt.ylim(0, 24)  # Set fixed Y-axis limit to 24 hours
    plt.yticks(range(0, 25))  # Display all hours as numbers
    plt.grid(axis="y", linestyle="--", alpha=0.7)  # Add horizontal grid lines

    # Secondary graph: Activity periods
    plt.subplot(2, 1, 2)
    if any(frequency_matrix):  # Only draw activity periods if there is data
        for hour_index, periods in enumerate(activity_periods):
            for start, duration in periods:
                frequency = frequency_matrix[hour_index] / max_days  # Normalize frequency by the full period
                color = calculate_color(frequency)
                plt.bar(hour_index, duration, bottom=start, color=color)  # Draw block with frequency-based color
    else:
        plt.text(12, 12, "No activity data available", ha="center", va="center", fontsize=12, color="red")
    plt.xlabel("Hour of Day")
    plt.ylabel("Activity Periods (hours)")
    plt.title(f"Activity Periods by Hour for last {days} days")
    plt.xticks(range(24))
    plt.ylim(0, 24)  # Set fixed Y-axis limit to 24 hours
    plt.yticks(range(0, 25))  # Display all hours as numbers
    plt.grid(axis="y", linestyle="--", alpha=0.7)  # Add horizontal grid lines

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    buffer.name = "daily_activity_plot.png"
    return buffer

def load_activity_data(user_id: str, days: int) -> dict:
    """Load activity data from the log file."""
    cutoff = datetime.now() - timedelta(days=days)
    
    file_name = log_path(user_id)
    if not os.path.exists(file_name):
        raise FileNotFoundError("Log file not found")
    
    days_in_month = [0.0] * 31
    days_of_week = [0.0] * 7
    hours = [0.0] * 24
    activity_periods_month = [[] for _ in range(31)]
    activity_periods_week = [[] for _ in range(7)]
    activity_periods_hour = [[] for _ in range(24)]
    frequency_matrix_month = [[0] * 24 for _ in range(31)]
    frequency_matrix_week = [[0] * 24 for _ in range(7)]
    frequency_matrix_hour = [0] * 24

    with open(file_name, "r", encoding="utf-8") as f:
        # Skip header
        next(f, None)
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",", 2)]
            if len(parts) < 3:
                continue
            _, stamp, duration = parts
            try:
                ts = datetime.strptime(stamp, DATETIME_FORMAT)
            except Exception:
                continue
            if ts < cutoff:
                continue
            try:
                dur_val = int(duration) / 3600  # Convert seconds to hours
            except Exception:
                continue

            day_index = ts.day - 1
            hour_index = ts.hour
            days_in_month[day_index] += dur_val
            activity_periods_month[day_index].append((ts.hour + ts.minute / 60, dur_val))
            frequency_matrix_month[day_index][hour_index] += 1

            weekday_index = ts.weekday()
            days_of_week[weekday_index] += dur_val
            activity_periods_week[weekday_index].append((ts.hour + ts.minute / 60, dur_val))
            frequency_matrix_week[weekday_index][hour_index] += 1

            hours[hour_index] += dur_val
            activity_periods_hour[hour_index].append((ts.minute / 60, dur_val))
            frequency_matrix_hour[hour_index] += 1

    return {
        "days_in_month": [min(val, 24) for val in days_in_month],
        "days_of_week": [min(val, 24) for val in days_of_week],
        "hours": [min(val, 24) for val in hours],
        "activity_periods_month": activity_periods_month,
        "activity_periods_week": activity_periods_week,
        "activity_periods_hour": activity_periods_hour,
        "frequency_matrix_month": frequency_matrix_month,
        "frequency_matrix_week": frequency_matrix_week,
        "frequency_matrix_hour": frequency_matrix_hour,
        "max_days": days, 
    }

def create_plots(user_id: int, days: int) -> dict[str, bytes]:
    """Create all activity plots for ``user_id`` and return them as a dictionary."""
    data = load_activity_data(user_id, days)
    plots = [
        create_monthly_activity_plot(data, days),
        create_weekly_activity_plot(data, days),
        create_daily_activity_plot(data, days),
    ]
    return plots