# 🚴 Tour de France Stage Analysis Using Network Analysis

This project analyzes the complete Tour de France dataset to explore the greatest cyclists in the history of the event using network analysis techniques, specifically PageRank.

## TODO's
- [x] Scraping tables from ProCyclingStats
- [🛠️] Correct scraped data (Too many skipped stages due to wrong data in source)
- [x] Construct various MultiDiGraphs:
    - [x] With no weights
    - [x] Weights are time differences
    - [x] Weights are normalized time differences
    - [x] Weights are normalized time differences scaled by type of stage & stage length
    - [x] Weights are points obtained after stage
- [x] Perform PageRank on all graphs
- [🛠️] Create a table of data, from which we can perform basic statistics to evaluate the best riders based on number of stage wins, overall wins, etc.
- [🛠️] Perform statistics
- [ ] Write a report
    - [ ] Abstract
    - [ ] Introduction
    - [ ] Related work
    - [ ] Methods
    - [ ] Results
    - [ ] Conclusion
    - [ ] References