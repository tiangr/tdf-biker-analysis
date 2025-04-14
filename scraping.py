import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import io
import os
import networkx as nx
import helper

pd.set_option('display.max_rows', None)      # Show all rows

# GC - overall winner (Yellow Jersey), POINTS - points classification (Green Jersey), KOM - King of the Mountains (Polka Dot Jersey), YOUTH - best young rider (White Jersey)
columns = ["Rider", "1st", "2nd", "3rd", "GC", "POINTS", "KOM", "YOUTH"]
stats_df = pd.DataFrame(columns=columns)

# ------------------------ Helpers ------------------------
def time_to_seconds(time_str):
    parts = time_str.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
    elif len(parts) == 2:
        hours, minutes, seconds = 0, *map(int, parts)
    elif time_str == "-":
        return None
    else:
        parts2 = time_str.split(".")
        if len(parts2) == 1:
            return time_str
        hours, minutes, seconds = 0, *map(int, parts2)
    return hours * 3600 + minutes * 60 + seconds

def create_stats_file(sorted_stats):
    sorted_stats.to_csv("tdf_stats.csv", index=False, header=True, sep=";")

def add_new_rider(rider):
    global stats_df
    new_row = pd.DataFrame({"Rider": [rider], "1st": [0], "2nd": [0], "3rd": [0], "GC": [0], "POINTS": [0], "KOM": [0], "YOUTH": [0]})
    stats_df = pd.concat([stats_df, new_row], ignore_index=True)

def add_podiums(table):
    global stats_df
    for i in range(3):
        rider = table.loc[i, "Rider"]
        if rider not in stats_df["Rider"].values:
            add_new_rider(rider)
        stats_df.loc[stats_df["Rider"] == rider, columns[i+1]] += 1

def get_categories_for_year(year):
    if 1903 <= year <= 1932:
        return {"GC": 1}
    elif 1933 <= year <= 1952:
        return {"GC": 1, "KOM": 2}
    elif 1953 <= year <= 1974:
        return {"GC": 1, "POINTS": 2, "KOM": 3}
    elif 1975 <= year <= 2024:
        return {"GC": 1, "POINTS": 2, "KOM": 3, "YOUTH": 4}
    else:
        return {}
    
def get_overall_winner_of_category(response, category, number_of_categorie):
    global stats_df
    try:
        winner = pd.read_html(io.StringIO(response))[number_of_categorie]
        winner = winner.loc[0, "Rider"].replace(f" {winner.loc[0, 'Team']}", "")
    except:
        return
    if winner not in stats_df["Rider"].values:
        add_new_rider(winner)
    stats_df.loc[stats_df["Rider"] == winner, category] += 1

def guess_stage_type_and_length(stage_title):
    #CHATGPT nepreverjeno
    title = stage_title.lower()
    if "itt" in title or "individual time trial" in title:
        return "itt", 25
    elif "ttt" in title or "team time trial" in title:
        return "ttt", 30
    elif "mountain" in title:
        return "mountain", 180
    elif "hill" in title or "hilly" in title:
        return "hilly", 160
    elif "flat" in title:
        return "flat", 200
    else:
        return "unknown", 160 

def scaling_factor(stage_type, length_km):
    base = {
        "itt": 1.5,
        "ttt": 1.2,
        "mountain": 2.0,
        "hilly": 1.4,
        "flat": 1.0,
        "unknown": 1.0
    }
    return base.get(stage_type, 1.0) * (length_km / 100)

# ----------------------- Main -------------------------

# Graphs modes
graph_modes = ["no_weights", "time_diff", "normalized_time_diff", "scaled_time_diff", "points", "pure_points"]
graphs = {mode: nx.MultiDiGraph() for mode in graph_modes}

edition = "a" # TODO: Add edition = "c", debug properly. ALSO include Prologue stages
eddy = 0 # Delete when Eddy stats are fixed
# For Eddy Merckx do range(1968, 1979)
# 1903 - 2025
for year in range(2009, 2025):
    print(f"Processing year: {year}")
    url = f"https://www.procyclingstats.com/race/tour-de-france/{year}/gc"
    try:
        response = BeautifulSoup(requests.get(url).content, 'html.parser').prettify()
    except:
        print(f"Skipped year {year}")
        continue

    extended_stage = 0
    no_stages = response.find("Stage ")
    no_stages = response[no_stages+5 : no_stages+8]
    try:
        no_stages = int(no_stages)
    except:
        print(f"Skipped year {year}")
        continue

    categories = get_categories_for_year(year)
    for category, index in categories.items():
        get_overall_winner_of_category(response, category, index)

    for stage in range(1, no_stages+1):
        extended_stage += 1
        if stage == 20 and year == 1979:
            continue
        true_stage = stage
        stage_url = f"https://www.procyclingstats.com/race/tour-de-france/{year}/stage-{stage}"
        try:
            response = BeautifulSoup(requests.get(stage_url).content, 'html.parser')
            html = response.prettify()
            table = pd.read_html(io.StringIO(html))[0]
        except:
            try:
                # TODO: Add edition = "c", debug properly. ALSO include Prologue stages
                response = BeautifulSoup(requests.get(stage_url + edition).content, 'html.parser')
                html = response.prettify()
                table = pd.read_html(io.StringIO(html))[0]
                if edition == "a":
                    stage -= 1
                    edition = "b"
                    true_stage = f"{true_stage}a"
                else:
                    edition = "a"
                    true_stage = f"{true_stage}b"
            except:
                print(f"    Failed to load stage {true_stage}")
                continue

        columns_to_keep = ["Rnk", "Rider", "Team", "Pnt", "Time"]
        try:
            table = table[columns_to_keep]
        except:
            print(f"    Skipping team stage at {year} stage {true_stage}")
            continue

        table = table.dropna(subset=["Rnk"])
        table = table[(table["Rnk"] != "DSQ") & (table["Rnk"] != "OTL") & (table["Rnk"] != "DNF")]
        table["Time"] = table["Time"].str.split(" ").str[0]
        table.loc[0, "Time"] = "0"
        table["Time"] = table["Time"].replace(",,", None).ffill()
        table["Time"] = table["Time"].apply(time_to_seconds)
        table["Pnt"] = pd.to_numeric(table["Pnt"], errors="coerce").fillna(0)
        table = table.dropna(subset=["Time", "Rnk"])
        try:
            table["Rider"] = table.apply(lambda row: row["Rider"].replace(f" {row['Team']}", "").strip(), axis=1)
        except:
            table.loc[0, "Time"] = "0"
        table = table.drop(columns=["Team", "Rnk"])
        table = table.reset_index(drop=True)
        
        table["Time"] = pd.to_numeric(table["Time"], errors="coerce")
        while not table["Time"].is_monotonic_increasing:
            table = helper.scrape_1stcycling(year,extended_stage,table[["Rider","Pnt","Time"]],true_stage)
            if type(table) == None:
                print(f"    Skipping {year} stage {true_stage} because not monotonic increasing time")
                break

        if "MERCKX Eddy" in table.loc[0,"Rider"]: # TODO: Delete when fixed, needs 34 wins.
            eddy += 1
            print(f"Eddy Merckx at {year} - {true_stage} win #{eddy}")

        if len(table) >= 3:
            add_podiums(table)

        loser_time = int(table.loc[len(table)-1, "Time"])

        stage_title_tag = response.find("title")
        stage_title = stage_title_tag.text if stage_title_tag else ""
        stage_type, length_km = guess_stage_type_and_length(stage_title)
        scale = scaling_factor(stage_type, length_km)

        for mode in graph_modes:
            for i, row in table.iterrows():
                graphs[mode].add_node(row["Rider"], time=row["Time"])

        for i in range(1, len(table)):
            current_rider = table.loc[i, "Rider"]
            current_time = int(table.loc[i, "Time"])

            for j in range(i):
                prev_rider = table.loc[j, "Rider"]
                prev_time = int(table.loc[j, "Time"])
                points = table.loc[j, "Pnt"]
                time_diff = current_time - prev_time
                normalized_diff = time_diff / max(loser_time, 1)
                scaled_diff = normalized_diff * scale

                # Depending on graph mode we add different weights
                for mode in graph_modes:
                    if mode == "no_weights":
                        weight = 1
                    elif mode == "time_diff":
                        weight = max(time_diff, 1)
                    elif mode == "normalized_time_diff":
                        weight = normalized_diff
                    elif mode == "scaled_time_diff":
                        weight = scaled_diff
                    elif mode == "points":
                        weight = points if points > 0 else 1
                    elif mode == "pure_points": # TODO: Should have much less edges, check it. 
                        weight = points
                    graphs[mode].add_edge(current_rider, prev_rider, weight=weight)
                    

# ---------------------- Output --------------------------
os.makedirs("output_graphs", exist_ok=True)
for mode in graph_modes:
    filename = f"output_graphs/TDF_{mode}.net"
    print(f"Saving graph: {filename}")
    nx.write_pajek(graphs[mode], filename)

# Save podiums
stats_df = stats_df.sort_values(by=["GC", "1st", "2nd", "3rd"], ascending=False).reset_index(drop=True)
create_stats_file(stats_df)
print("All graphs and stats saved.")
