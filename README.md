# 🚴 Tour de France Stage Analysis Using Network Analysis

This project analyzes the complete Tour de France dataset to explore the greatest cyclists in the history of the event using network analysis techniques, specifically PageRank.

## TODO's
- [x] Scraping tables from ProCyclingStats
- [x] Correct scraped data (Too many skipped stages due to wrong data in source)
    - [x] Migrate helper functions
    - [x] Editions of stages by letters fix, only a and b so far
    - [x] Fix stages with wrong time data
- [x] Construct various MultiDiGraphs:
    - [x] With no weights
    - [x] Weights are time differences
    - [x] Weights are normalized time differences
    - [x] Weights are normalized time differences scaled by type of stage & stage length
    - [x] Weights are points obtained after stage
- [x] Perform PageRank on all graphs
- [🛠️] Create a table of data, from which we can perform basic statistics to evaluate the best riders based on number of stage wins, overall wins, etc.
- [x] Perform network analysis 
    - [x] PageRank
    - [ ] Combine Community detection with PageRank? We may require more analysis
    - [ ] Visualize results
- [🛠️] Write a report
    - [x] Abstract
    - [x] Introduction
    - [ ] Related work
    - [ ] Results
    - [ ] Discussion
    - [ ] References
