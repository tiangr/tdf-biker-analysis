import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import io
import networkx as nx
import matplotlib.pyplot as plt

columns = ["Rider", "1st", "2nd", "3rd", "Total Wins"]
stats_df = pd.DataFrame(columns=columns)

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
    # Add a new rider to the stats_df DataFrame
    global stats_df
    new_row = pd.DataFrame({"Rider": [rider], "1st": [0], "2nd": [0], "3rd": [0], "Total Wins": [0]})
    stats_df = pd.concat([stats_df, new_row], ignore_index=True)

def add_podiums(table):
    # Add podiums to the stats_df DataFrame
    global stats_df
    for i in range(3):
        rider = table.loc[i, "Rider"]
        if rider not in stats_df["Rider"].values:
            add_new_rider(rider)
        stats_df.loc[stats_df["Rider"] == rider, columns[i+1]] += 1

def get_overall_winner(response):
    # Extract the overall winner from the response
    global stats_df
    try:
        overall_winner = pd.read_html(io.StringIO(response))[1]
        overall_winner = overall_winner.loc[0, "Rider"].replace(f" {overall_winner.loc[0, 'Team']}", "")
    except:
        return

    if overall_winner not in stats_df["Rider"].values:
        add_new_rider(overall_winner)
    stats_df.loc[stats_df["Rider"] == overall_winner, "Total Wins"] += 1

G = nx.MultiDiGraph()
edition = "a"
for year in range(1903,2025):
    # First check for number of stages
    url = f"https://www.procyclingstats.com/race/tour-de-france/{year}/gc"
    response = BeautifulSoup(requests.get(url).content, 'html.parser').prettify()

    no_stages = response.find("Stage ")
    no_stages = response[no_stages+5 : no_stages+8]
    try:
        no_stages = int(no_stages)
    except:
        continue

    # Get the overall winner
    get_overall_winner(response)

    for stage in range(1,no_stages+1):
        stage_url = f"https://www.procyclingstats.com/race/tour-de-france/{year}/stage-{stage}"
        print(year, stage)
        response = BeautifulSoup(requests.get(stage_url).content, 'html.parser').prettify()
        try: # Some stages are made of two sub-stages, a and b.
            table = pd.read_html(io.StringIO(response))[0]
        except:
            response = BeautifulSoup(requests.get(stage_url + edition).content, 'html.parser').prettify()
            table = pd.read_html(io.StringIO(response))[0]
            if edition == "a":
                stage -= 1
                edition = "b"
            else:
                edition = "a"
        columns_to_keep = ["Rnk","Rider", "Team", "Pnt", "Time"]
        try: # Gets rid of Team time trials
            table = table[columns_to_keep]
        except:
            print("NOT ",year, stage)
            continue
        # Drop false rows (disqualifications)
        table = table.dropna(subset="Rnk")
        table = table[table["Rnk"] != "DSQ"]
        # Format time properly
        table["Time"] = table["Time"].str.split(" ").str[0]
        table.loc[0, "Time"] = "0"
        table["Time"] = table["Time"].replace(",,", None).ffill()
        table["Time"] = table["Time"].apply(time_to_seconds)
        table = table.dropna(subset="Time")
        try: # If first rider is relegated, then we must skip the team name removal
            # Remove the team name from the rider's name (error in data)
            table["Rider"] = table.apply(lambda row: row["Rider"].replace(f" {row['Team']}", ""), axis=1)
        except:
            table.loc[0, "Time"] = "0"
        # Table cleaning
        table = table.drop(columns=["Team","Rnk"])
        table = table.reset_index(drop=True)
        
        # Adding podiums
        if len(table) >= 3:
            add_podiums(table)
        
        # Constructing/Adding to - Multigraph
        for i, row in table.iterrows():
            G.add_node(row["Rider"], time=row["Time"])

        for i in range(1, len(table)):
            current_rider = table.loc[i, "Rider"]
            current_time = int(table.loc[i, "Time"])
            
            for j in range(i):
                prev_rider = table.loc[j, "Rider"]
                prev_time = int(table.loc[j, "Time"])
                weight = max(current_time - prev_time, 1)
                G.add_edge(current_rider, prev_rider, weight=weight)
nx.write_pajek(G, f"TDF")

# Sort the DataFrame by Total Wins, 1st, 2nd, and 3rd podiums
stats_df = stats_df.sort_values(by=["Total Wins", "1st", "2nd", "3rd"], ascending=False).reset_index(drop=True)
create_stats_file(stats_df)