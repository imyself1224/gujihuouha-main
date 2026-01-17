package com.example.gujihuohua.controller;

import com.example.gujihuohua.entity.graph.GraphApiResponse;
import com.example.gujihuohua.service.GraphService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import java.util.List;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class GraphController {

    private final GraphService graphService;

    @GetMapping("/health")
    public Map<String, Object> checkHealth() {
        return graphService.checkHealth();
    }

    @GetMapping("/node/{name}")
    public GraphApiResponse<Object> getNodeDetails(@PathVariable String name) {
        Map<String, Object> result = graphService.getNodeDetails(name);
        if (result != null) {
            return GraphApiResponse.success(result.get("data")); // Service wraps in data? No check service code.
            // Service.getNodeDetails returns Map("data", node)
            // But ApiResponse expects generic T data.
            // Let's check service again.
            // getNodeDetails returns Collections.singletonMap("data", graphNode);
            // So result.get("data") is GraphNode.
        }
        return GraphApiResponse.error("Node not found");
    }

    // --- Search Person ---
    @GetMapping("/search/person")
    public GraphApiResponse<Object> searchPersonGet(@RequestParam String name) {
        return searchPersonInternal(name);
    }
    @PostMapping("/search/person")
    public GraphApiResponse<Object> searchPersonPost(@RequestBody Map<String, String> body) {
        return searchPersonInternal(body.get("name"));
    }
    private GraphApiResponse<Object> searchPersonInternal(String name) {
        Map<String, Object> res = graphService.searchPerson(name);
        return res != null ? GraphApiResponse.success(res) : GraphApiResponse.error("Not found");
    }

    // --- Relations ---
    @GetMapping("/edge/relations")
    public GraphApiResponse<Object> getRelationsGet(@RequestParam String source, @RequestParam String target) {
        return getRelationsInternal(source, target);
    }
    @PostMapping("/edge/relations")
    public GraphApiResponse<Object> getRelationsPost(@RequestBody Map<String, String> body) {
        return getRelationsInternal(body.get("source"), body.get("target"));
    }
    private GraphApiResponse<Object> getRelationsInternal(String source, String target) {
        Map<String, Object> res = graphService.getRelations(source, target);
        return GraphApiResponse.success(res);
    }

    // --- Edges By Type ---
    @GetMapping("/edge/by-type/{type}")
    public GraphApiResponse<Object> getEdgesByType(@PathVariable String type, @RequestParam(defaultValue = "50") int limit) {
        // If type is "ALL", we delegate to getEdgesByType but service handles logic or we add separate method
        // But service signature uses specific strings.
        // Let's rely on Service to handle "ALL" or add separate endpoint?
        // Let's add separate endpoint for clarity or modify logic here.
        Map<String, Object> res = graphService.getEdgesByType(type, limit);
        return GraphApiResponse.success(res);
    }
    
    @GetMapping("/edge/all")
    public GraphApiResponse<Object> getAllEdges(@RequestParam(defaultValue = "2000") int limit) {
         Map<String, Object> res = graphService.getAllEdges(limit);
         return GraphApiResponse.success(res);
    }

    // --- Neighbors ---
    @GetMapping("/graph/neighbors")
    public GraphApiResponse<Object> getNeighborsGet(@RequestParam String name, @RequestParam(defaultValue = "20") int limit) {
        return getNeighborsInternal(name, limit);
    }
    @PostMapping("/graph/neighbors")
    public GraphApiResponse<Object> getNeighborsPost(@RequestBody Map<String, Object> body) {
        String name = (String) body.get("name");
        int limit = body.containsKey("limit") ? (Integer) body.get("limit") : 20;
        return getNeighborsInternal(name, limit);
    }
    private GraphApiResponse<Object> getNeighborsInternal(String name, int limit) {
        Map<String, Object> res = graphService.getNeighbors(name, limit);
        return GraphApiResponse.success(res);
    }

    // --- Subgraph ---
    @GetMapping("/graph/subgraph")
    public GraphApiResponse<Object> getSubgraphGet(@RequestParam String center, @RequestParam(defaultValue = "2") int depth, @RequestParam(defaultValue = "50") int limit) {
        return getSubgraphInternal(center, depth, limit);
    }
    @PostMapping("/graph/subgraph")
    public GraphApiResponse<Object> getSubgraphPost(@RequestBody Map<String, Object> body) {
        String center = (String) body.get("center");
        int depth = body.containsKey("depth") ? (Integer) body.get("depth") : 2;
        int limit = body.containsKey("limit") ? (Integer) body.get("limit") : 50;
        return getSubgraphInternal(center, depth, limit);
    }
    private GraphApiResponse<Object> getSubgraphInternal(String center, int depth, int limit) {
        Map<String, Object> res = graphService.getSubgraph(center, depth, limit);
        return GraphApiResponse.success(res);
    }

    // --- Path ---
    @GetMapping("/graph/path")
    public GraphApiResponse<Object> getPathGet(@RequestParam String source, @RequestParam String target, @RequestParam(defaultValue = "5") int max_length) {
        return getPathInternal(source, target, max_length);
    }
    @PostMapping("/graph/path")
    public GraphApiResponse<Object> getPathPost(@RequestBody Map<String, Object> body) {
        String source = (String) body.get("source");
        String target = (String) body.get("target");
        int max_length = body.containsKey("max_length") ? (Integer) body.get("max_length") : 5;
        return getPathInternal(source, target, max_length);
    }
    private GraphApiResponse<Object> getPathInternal(String source, String target, int max_length) {
        Map<String, Object> res = graphService.getShortestPath(source, target, max_length);
        return res != null ? GraphApiResponse.success(res) : GraphApiResponse.error("Path not found");
    }

    // --- Location ---
    @GetMapping("/search/location")
    public GraphApiResponse<Object> searchLocationGet(@RequestParam String name) {
        return searchLocationInternal(name);
    }
    @PostMapping("/search/location")
    public GraphApiResponse<Object> searchLocationPost(@RequestBody Map<String, String> body) {
        return searchLocationInternal(body.get("name"));
    }
    private GraphApiResponse<Object> searchLocationInternal(String name) {
        Map<String, Object> res = graphService.searchLocation(name);
        return res != null ? GraphApiResponse.success(res) : GraphApiResponse.error("Not found");
    }

    // --- Search All ---
    @GetMapping("/search/all")
    public GraphApiResponse<Object> searchAllGet(@RequestParam String keyword) {
        return searchAllInternal(keyword);
    }
    @PostMapping("/search/all")
    public GraphApiResponse<Object> searchAllPost(@RequestBody Map<String, String> body) {
        return searchAllInternal(body.get("keyword"));
    }
    private GraphApiResponse<Object> searchAllInternal(String keyword) {
        Object res = graphService.searchAll(keyword);
        if (res instanceof List) {
            return GraphApiResponse.success(res, ((List<?>) res).size());
        }
        return GraphApiResponse.success(res);
    }

    // --- Whole Graph ---
    @GetMapping("/graph/whole")
    public GraphApiResponse<Object> getWholeGraph(@RequestParam(defaultValue = "300") int limit) {
        Map<String, Object> res = graphService.getWholeGraph(limit);
        return GraphApiResponse.success(res);
    }
    
    @GetMapping("/graph/nodes-by-label")
    public GraphApiResponse<Map<String, Object>> getNodesByLabel(@RequestParam String label, @RequestParam(defaultValue = "1000") int limit) {
         return GraphApiResponse.success(graphService.getNodesByLabel(label, limit));
    }

    // --- Stats ---
    @GetMapping("/graph/stats")
    public GraphApiResponse<Object> getStats() {
        Map<String, Object> res = graphService.getStats();
        return GraphApiResponse.success(res);
    }
}
