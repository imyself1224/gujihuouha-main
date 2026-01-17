package com.example.gujihuohua.service;

import java.util.Map;

public interface GraphService {
    Map<String, Object> checkHealth();
    Map<String, Object> getNodeDetails(String name);
    Map<String, Object> searchPerson(String name);
    Map<String, Object> getRelations(String source, String target);
    Map<String, Object> getEdgesByType(String type, int limit);
    Map<String, Object> getAllEdges(int limit);
    Map<String, Object> getNeighbors(String name, int limit);
    Map<String, Object> getSubgraph(String center, int depth, int limit);
    Map<String, Object> getShortestPath(String source, String target, int maxLength);
    Map<String, Object> searchLocation(String name);
    Map<String, Object> getWholeGraph(int limit);
    Map<String, Object> getNodesByLabel(String label, int limit);
    Object searchAll(String keyword);
    Map<String, Object> getStats();
}
