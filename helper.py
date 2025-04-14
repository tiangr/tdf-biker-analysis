import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import io
import os
import networkx as nx

def time_to_seconds(time_str):
    time_str = time_str.strip("+ ")
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

def standardize_name(name):
    parts = name.strip().split()
    if len(parts) < 2:
        return name.strip()

    *last_middle, first = parts
    last_middle = [p.upper() for p in last_middle]
    return " ".join(last_middle + [first])

def input_handler(inp,table,pts,pct):
    if inp == "":
        return table
    elif inp == "flip":
        return input_handler(input("\nOG table changes? Row/Year Stage:"),pts,table,pct)
    else:
        inp = inp.split()
        if len(inp) == 1:
            corrected_time = input(f"What is new time for contestant {inp}? ")
            table.loc[int(inp[0]), "Time"] = int(corrected_time)
            print(table)
            return input_handler(input("\nRow/Year Stage: "),table,pts,pct)
        try:
            return scrape_1stcycling(inp[0], inp[1], pts, pct)
        except:
            return input_handler(input("\nRow/Year Stage: "),table,pts,pct)

def scrape_1stcycling(year,stage,pts,pct_stage):
    # TODO: Some tables are wrong - Here we need to redirect to firstcycling.com and scrape the CORRECT data
    # Points are not present on the firstcycling.com, either we put points to first 20 as 
    # is standard by hard coding the points OR just keep procyclingstats.com table and provide points like that.
    url = f"https://firstcycling.com/race.php?r=17&y={year}&e={stage}"
    response = BeautifulSoup(requests.get(url).content, 'html.parser').prettify()
    start = response.rfind("<table")
    end = response.rfind("</table>")
    table = pd.read_html(io.StringIO(response[start:end]))[0]
    try:
        table = table.drop(["Unnamed: 2","Team"], axis=1)
        if "Unnamed: 5" in table.columns:
            table = table.drop(["Unnamed: 5"], axis=1)
        if "Unnamed: 1" in table.columns:
            table = table.drop(["Unnamed: 1"], axis=1)
        if "Unnamed: 3" in table.columns:
            table = table.drop(["Unnamed: 3"], axis=1)
        if "UCI" in table.columns:
            table = table.drop(["UCI"], axis=1)
    except:
        return scrape_1stcycling(year,stage+1,pts,pct_stage)
    table.loc[0, "Time"] = "0"
    table = table.dropna(subset=["Time"])
    table["Time"] = table["Time"].apply(time_to_seconds)
    table["Time"] = pd.to_numeric(table["Time"], errors="coerce")
    print(f"OG Table {year}, {pct_stage}:\n", pts)
    print(f"\nNew Table {year}, {stage}:\n", table)
    input_return = input_handler(input("\nRow/Year Stage: "),table,pts,pct_stage)
    print(input_return)
    if type(input_return) != None:
        pts["Time"] = input_return["Time"]
        
        pts = pts.dropna(subset="Time")
        
        return pts
    else:
        return None