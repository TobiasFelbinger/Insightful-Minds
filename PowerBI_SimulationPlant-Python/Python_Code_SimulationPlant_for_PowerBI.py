#####################################################################
# Python Script: Simulation of 3 Machines in a Production Line
#####################################################################

# This script simulates production data for three machines over the past month.
# The machines are named Machine 1, Machine 2, and Machine 3.
# Each machine has different productivity levels depending on the shift.
# The shifts have different productivity levels.
# The Data generate Data 30 days in the past from the current time. 
# There are different Alarm descriptions, which are typical for a production machine. 
# The Data from a machine are collected every minute in every day. 24/7.

import pandas as pd
import random
from datetime import datetime, timedelta

# Dynamically calculate the start and end times for the past 30 days
now = datetime.now()
start_time_live = now - timedelta(days=30)
end_time_live = now

# Generate timestamps at 1-minute intervals
live_intervals = pd.date_range(start=start_time_live, end=end_time_live, freq="T")

########################################################################
# Generate all machine data into one DataFram (raw data)
########################################################################
# Alarm Names
# Definition of typical alarms encountered in production environments

alarm_names = [
    "Alarms.Overheating_of_Rolls",
    "Alarms.Overload_in_Motor",
    "Alarms.Pressure_Drop_in_Hydraulics",
    "Alarms.Material_Jam",
    "Alarms.Low_Oil_Level",
    "Alarms.Sensor_Error",
    "Alarms.Emergency_Stop_Triggered"
]

# Function to determine the production shift based on the hour

def efficient_determine_shift(hour):
    if 6 <= hour <= 13:
        return "Early Shift"
    elif 14 <= hour <= 21:
        return "Late Shift"
    else:
        return "Night Shift"

# Function to simulate machine data over time

def generate_Machine_data(Machine_name, live_intervals):
    data = []
    active_alarm = None
    remaining_alarm_duration = 0

    for time_point in live_intervals:
        # Determine the current shift (the shifts destigue in productivity)
        hour = time_point.hour
        if 6 <= hour <= 13:  # Early Shift
            production_chance = 0.9
        elif 14 <= hour <= 21:  # Late Shift
            production_chance = 0.8
        else:  # Night Shift
            production_chance = 0.6

        # Adjust production probability based on the specific machine
        if Machine_name == "Machine 2":
            production_chance *= 0.7  # 30% less productive
        elif Machine_name == "Machine 3":
            production_chance *= 0.85  # 15% less productive

        # Simulate production and alarms
        if remaining_alarm_duration > 0:
            alarm_values = [1 if i == active_alarm else 0 for i in range(len(alarm_names))]
            remaining_alarm_duration -= 1
        else:
            active_alarm = None
            alarm_values = [0] * len(alarm_names)

            if random.random() < production_chance:  # Production probability
                counter_value = random.randint(55, 65) + random.randint(-5, 5)  # Variations
            else:
                counter_value = 0  # Machine downtime

            # Occasional alarms during downtime
            if counter_value == 0 and random.random() > 0.9:
                active_alarm = random.randint(0, len(alarm_names) - 1)
                alarm_values[active_alarm] = 1
                remaining_alarm_duration = random.randint(10, 30)  # Alarm duration

        execute_value = 1 if counter_value > 0 else 0
        error_value = 1 if any(alarm_values) else 0

        # Append data entries
        data.append({"Date": time_point.strftime("%d.%m.%Y"), "Time": time_point.strftime("%H:%M"), "Name": "Counter", "Value": float(counter_value)})
        data.append({"Date": time_point.strftime("%d.%m.%Y"), "Time": time_point.strftime("%H:%M"), "Name": "Execute", "Value": float(execute_value)})
        data.append({"Date": time_point.strftime("%d.%m.%Y"), "Time": time_point.strftime("%H:%M"), "Name": "Error", "Value": float(error_value)})

        for i, alarm_name in enumerate(alarm_names):
            data.append({"Date": time_point.strftime("%d.%m.%Y"), "Time": time_point.strftime("%H:%M"), "Name": alarm_name, "Value": float(alarm_values[i])})

        standing_value = 1.0 if counter_value == 0 and error_value == 0 else 0.0
        data.append({"Date": time_point.strftime("%d.%m.%Y"), "Time": time_point.strftime("%H:%M"), "Name": "Standing", "Value": standing_value})

    # Convert data into a DataFrame
    df = pd.DataFrame(data)
    df['Machine'] = Machine_name
    df['Shift'] = pd.to_datetime(df['Time'], format='%H:%M').dt.hour.map(efficient_determine_shift)
    return df

# Generate data for each machine

df_machine1 = generate_Machine_data("Machine 1", live_intervals)
df_machine2 = generate_Machine_data("Machine 2", live_intervals)
df_machine3 = generate_Machine_data("Machine 3", live_intervals)

# Combine all machine data into one DataFrame
df_combined = pd.concat([df_machine1, df_machine2, df_machine3])
df_combined.sort_values(by=["Date", "Time", "Name", "Machine"], inplace=True)

####################################################################
# Alarm Table: Filtering Active Alarms
####################################################################

df_alarm = df_combined[
    (df_combined['Name'].str.contains("Alarms")) &  # Filter: Name contains "Alarms"
    (df_combined['Value'] == 1)                     # Only active alarms
]
df_alarm['Name'] = df_alarm['Name'].str.replace("Alarms.", "", regex=False)  # Remove prefix

##################################################################
# MDE Table: Filtering, Pivoting, and Calculations
##################################################################

valid_variablen = ['Error', 'Execute', 'Standing', 'Counter']
df_mde = df_combined[df_combined['Name'].isin(valid_variablen)]
df_mde = df_mde.pivot_table(index=['Machine', 'Date', 'Time', 'Shift'], columns='Name', values='Value').fillna(0)
df_mde.reset_index(inplace=True)

# Calculating key performance indicators
df_mde['Error'] = ((df_mde['Error'] == 1) & (df_mde['Execute'] == 0)).astype(int)
df_mde['Production'] = ((df_mde['Error'] == 0) & (df_mde['Execute'] == 1)).astype(int)
df_mde['Downtime'] = ((df_mde['Error'] == 0) & (df_mde['Execute'] == 0)).astype(int)
df_mde['Warning'] = ((df_mde['Error'] == 1) & (df_mde['Execute'] == 1)).astype(int)

# Detecting error transitions for calculating the amount of Errors
df_mde = df_mde.sort_values(by=["Machine", "Time"])
df_mde['Previous_Error'] = df_mde.groupby('Machine')['Error'].shift(1)
df_mde['Error_Transition'] = ((df_mde['Error'] == 1) & (df_mde['Previous_Error'] == 0)).astype(int)
df_mde = df_mde.drop(columns=['Previous_Error'])

##################################################################
# Exporting DataFrames for Analysis (e.g., Power BI)
##################################################################
# Export for Power BI
df_combined, df_alarm, df_mde

# Export Data as CSV (no activ, because not needed for Power BI)
df_mde.to_csv('./df_mde-example.csv', index=False, sep=";")
df_combined.to_csv('./df_combined-example.csv', index=False, sep=";")
df_alarm.to_csv('./df_alarm-example.csv', index=False, sep=";")
