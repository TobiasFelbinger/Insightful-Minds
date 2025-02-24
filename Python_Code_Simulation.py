#####################################################################
# Python-Skript Simulation of 3 machines
#####################################################################

# The following Python Skript simulate Data of 3 machines in a Production line
# The Name of the machines are

## Testdatensatz erzeugen. Simulation einer Produktion!
# Es gibt Maschine 1, Maschine 2, Maschine 3
# Maschinen haben eine unterschiedliche Produktivität
# Schichten der Maschinen haben eine unterschiedliche Produktivität

import pandas as pd
import random
from datetime import datetime, timedelta

# Dynamically calculate the start and end times for the past 30 days
now = datetime.now()
start_time_live = now - timedelta(days=30)
end_time_live = now
live_intervals = pd.date_range(start=start_time_live, end=end_time_live, freq="T")

# Alarm names
alarm_names = [
    "Alarme.Ueberhitzung_der_Walzen",
    "Alarme.Ueberlast_im_Motor",
    "Alarme.Druckabfall_in_der_Hydraulik",
    "Alarme.Materialstau",
    "Alarme.Niedriger_Oelstand",
    "Alarme.Sensorfehler",
    "Alarme.Not_Halt_ausgeloest"
]

# Function to determine shifts efficiently
def efficient_determine_shift(hour):
    if 6 <= hour <= 13:
        return "Frühschicht"
    elif 14 <= hour <= 21:
        return "Spätschicht"
    else:
        return "Nachtschicht"

# Function to generate Maschine data
def generate_Maschine_data(Maschine_name, live_intervals):
    data = []
    active_alarm = None
    remaining_alarm_duration = 0

    for time_point in live_intervals:
        # Determine the current shift
        hour = time_point.hour
        if 6 <= hour <= 13:  # Frühschicht
            production_chance = 0.9
        elif 14 <= hour <= 21:  # Spätschicht
            production_chance = 0.8
        else:  # Nachtschicht
            production_chance = 0.6

        # Anpassung der Produktionswahrscheinlichkeit basierend auf der Maschine
        if Maschine_name == "Maschine 2":
            production_chance *= 0.7  # 30% weniger produktiv
        elif Maschine_name == "Maschine 3":
            production_chance *= 0.85  # 15% weniger produktiv

        # Simuliere Produktion basierend auf der angepassten Wahrscheinlichkeit
        if remaining_alarm_duration > 0:
            alarm_values = [1 if i == active_alarm else 0 for i in range(len(alarm_names))]
            remaining_alarm_duration -= 1
        else:
            active_alarm = None
            alarm_values = [0] * len(alarm_names)

            if random.random() < production_chance:  # Produktionswahrscheinlichkeit
                counter_value = random.randint(55, 65) + random.randint(-5, 5)  # Variationen
            else:
                counter_value = 0  # Maschine im Stillstand

            if counter_value == 0 and random.random() > 0.9:  # Gelegentliche Alarme im Stillstand
                active_alarm = random.randint(0, len(alarm_names) - 1)
                alarm_values[active_alarm] = 1
                remaining_alarm_duration = random.randint(10, 30)  # Alarmdauer

        execute_value = 1 if counter_value > 0 else 0
        error_value = 1 if any(alarm_values) else 0

        # Daten hinzufügen
        data.append({"Datum": time_point.strftime("%d.%m.%Y"), "Uhrzeit": time_point.strftime("%H:%M"), "Name": "Counter", "Wert": float(counter_value)})
        data.append({"Datum": time_point.strftime("%d.%m.%Y"), "Uhrzeit": time_point.strftime("%H:%M"), "Name": "Execute", "Wert": float(execute_value)})
        data.append({"Datum": time_point.strftime("%d.%m.%Y"), "Uhrzeit": time_point.strftime("%H:%M"), "Name": "Error", "Wert": float(error_value)})

        for i, alarm_name in enumerate(alarm_names):
            data.append({"Datum": time_point.strftime("%d.%m.%Y"), "Uhrzeit": time_point.strftime("%H:%M"), "Name": alarm_name, "Wert": float(alarm_values[i])})

        standing_value = 1.0 if counter_value == 0 and error_value == 0 else 0.0
        data.append({"Datum": time_point.strftime("%d.%m.%Y"), "Uhrzeit": time_point.strftime("%H:%M"), "Name": "Standing", "Wert": standing_value})

    # Daten in ein DataFrame konvertieren
    df = pd.DataFrame(data)
    df['Maschine'] = Maschine_name
    df['Schicht'] = pd.to_datetime(df['Uhrzeit'], format='%H:%M').dt.hour.map(efficient_determine_shift)
    return df

# Generiere Daten für Maschine 1, Maschine 2 und Maschine 3 mit den neuen Produktivitätsanpassungen
df_tpa1 = generate_Maschine_data("Maschine 1", live_intervals)
df_tpa2 = generate_Maschine_data("Maschine 2", live_intervals)
df_tpa3 = generate_Maschine_data("Maschine 3", live_intervals)

# Kombiniere alle Daten
df_combined = pd.concat([df_tpa1, df_tpa2, df_tpa3])
df_combined.sort_values(by=["Datum", "Uhrzeit", "Name", "Maschine"], inplace=True)

####################################################################
# Alarm Tabelle
# Filtere nur die Alarm-Daten aus dem bestehenden DataFrame
####################################################################

alarme_df = df_combined[
    (df_combined['Name'].str.contains("Alarme")) &  # Filter: Name enthält "Alarme"
    (df_combined['Wert'] == 1)                     # Nur aktive Alarme
]
alarme_df['Name'] = alarme_df['Name'].str.replace("Alarme.", "", regex=False)  # Präfix entfernen

##################################################################
# MDE Tabelle
# Filtern, Pivotisiere, Berechnung
##################################################################

valid_variablen = ['Error', 'Execute', 'Standing', 'Counter']
mde_dataset = df_combined[df_combined['Name'].isin(valid_variablen)]
mde_dataset = mde_dataset.pivot_table(index=['Maschine', 'Datum', 'Uhrzeit', 'Schicht'], columns='Name', values='Wert').fillna(0)
mde_dataset.reset_index(inplace=True)

mde_dataset['Störung'] = ((mde_dataset['Error'] == 1) & (mde_dataset['Execute'] == 0)).astype(int)
mde_dataset['Produktion'] = ((mde_dataset['Error'] == 0) & (mde_dataset['Execute'] == 1)).astype(int)
mde_dataset['Stillstand'] = ((mde_dataset['Error'] == 0) & (mde_dataset['Execute'] == 0)).astype(int)
mde_dataset['Warnung'] = ((mde_dataset['Error'] == 1) & (mde_dataset['Execute'] == 1)).astype(int)

mde_dataset = mde_dataset.sort_values(by=["Maschine", "Uhrzeit"])
mde_dataset['Vorherige_Störung'] = mde_dataset.groupby('Maschine')['Störung'].shift(1)
mde_dataset['Störungsübergang'] = ((mde_dataset['Störung'] == 1) & (mde_dataset['Vorherige_Störung'] == 0)).astype(int)
mde_dataset = mde_dataset.drop(columns=['Vorherige_Störung'])

##################################################################
# Ausgabe der Tabellen für Power BI
##################################################################

df_combined, alarme_df, mde_dataset