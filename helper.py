import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import io
import os
import networkx as nx



def create_stats_file(sorted_stats):
    sorted_stats.to_csv("tdf_stats.csv", index=False, header=True, sep=";")

    
def guess_stage_type_and_length(stage_title):
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

def not_restday(stage):
    return type(stage) == str and ("Stage" in stage or "Prologue" in stage)

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

def tts(time_str):
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
