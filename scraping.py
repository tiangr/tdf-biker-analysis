import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import io
import networkx as nx
import matplotlib.pyplot as plt



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