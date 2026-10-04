from benchmark.run_official_three_way_benchmark import get_connection, graph_previous_olympics

q = "Who won the gold medal in the men's 20 kilometres walk athletics event at the Summer Olympics held immediately before 2016?"

c = get_connection()

result = graph_previous_olympics(c, q)

print(result)