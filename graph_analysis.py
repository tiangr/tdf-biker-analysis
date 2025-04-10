import networkx as nx

def read_pajek(name, path = "."):
    G = nx.MultiDiGraph()
    with open(path + "/" + name + ".net", 'r', encoding="utf-8") as file:
        file.readline()

        for line in file:
            if line.startswith("*"):
                break
            else:
                node = line.split("\"")
                G.add_node(int(node[0]) - 1, label = node[1])

        for line in file:
            i, j, w = map(int, line.split())
            i -= 1
            j -= 1
            G.add_edge(i, j, weight=float(w))
      
    return G


if __name__ == "__main__":
    mode = "time_diff"
    G = read_pajek(f"TDF_{mode}", "output_graphs")
    print(G.number_of_nodes())
    print(G.number_of_edges())