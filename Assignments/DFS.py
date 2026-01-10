def dfs(graph,start,visited = None):
  if visited is None:
    visited = set()
  visited.add(start)
  print(start)
  for neighbor in graph[start]:
    if neighbor not in visited:
      dfs(graph,neighbor,visited)
  return visited

if __name__=="__main__":
  graph = {
      'A':['B','C'],
      'B':['A','D','E'],
      'C':['A','F','G'],
      'D':['B'],
      'E':['B'],
      'F':['C'],
      'G':['C']
  }

  print("DFS traversal starting from node A:")
  dfs(graph,'A')