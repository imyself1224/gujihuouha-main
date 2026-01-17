package com.example.gujihuohua.service;

import com.example.gujihuohua.entity.graph.GraphEdge;
import com.example.gujihuohua.entity.graph.GraphNode;
import lombok.RequiredArgsConstructor;
import org.neo4j.driver.types.Node;
import org.neo4j.driver.types.Path;
import org.neo4j.driver.types.Relationship;
import org.springframework.data.neo4j.core.Neo4jClient;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;
import java.util.Objects;

@Service
@RequiredArgsConstructor
public class GraphServiceImpl implements GraphService {

    private final Neo4jClient neo4jClient;

    private GraphNode mapNode(Node node, String centerName) {
        if (node == null) return null;
        List<String> labels = StreamSupport.stream(node.labels().spliterator(), false)
                .collect(Collectors.toList());
        String nodeName = node.get("name").asString(null);
        return GraphNode.builder()
                .id(String.valueOf(node.elementId())) // Neo4j 5+ uses elementId, older uses id()
                .name(nodeName)
                .labels(labels)
                .properties(node.asMap())
                .is_center(Objects.equals(centerName, nodeName))
                .build();
    }

    private GraphEdge mapEdge(Relationship rel, Node source, Node target) {
        if (rel == null) return null;
        String relationType = rel.type();
        String srcName = source != null ? source.get("name").asString() : null;
        String tgtName = target != null ? target.get("name").asString() : null;

        List<String> srcLabels = source != null ? StreamSupport.stream(source.labels().spliterator(), false).collect(Collectors.toList()) : Collections.emptyList();
        List<String> tgtLabels = target != null ? StreamSupport.stream(target.labels().spliterator(), false).collect(Collectors.toList()) : Collections.emptyList();
        
        // Determine direction relative to source/target passed in? 
        // For generic edge listing, we just return source/target names
        
        return GraphEdge.builder()
                .source(srcName)
                .target(tgtName)
                .relation_type(relationType)
                .source_labels(srcLabels)
                .target_labels(tgtLabels)
                .properties(rel.asMap())
                .build();
    }

    @Override
    public Map<String, Object> checkHealth() {
        try {
            Long result = neo4jClient.query("RETURN 1").fetchAs(Long.class).one().orElse(0L);
            if (result == 1) {
                return Map.of("status", "success", "message", "Neo4j 连接正常");
            }
        } catch (Exception e) {
            return Map.of("status", "error", "message", e.getMessage());
        }
        return Map.of("status", "error", "message", "Unknown error");
    }

    @Override
    public Map<String, Object> getNodeDetails(String name) {
        Optional<Node> nodeOpt = neo4jClient.query("MATCH (n) WHERE n.name = $name RETURN n")
                .bind(name).to("name")
                .fetchAs(Node.class).one();

        if (nodeOpt.isPresent()) {
            GraphNode graphNode = mapNode(nodeOpt.get(), null);
            return Collections.singletonMap("data", graphNode); // Wrapper handled in controller? No, method returns Map
            // The Flask service returns {"name":..., "labels":..., "properties":...} directly in "data"
        }
        return null;
    }

    @Override
    public Map<String, Object> searchPerson(String name) {
        // MATCH (n:Person {name: $name}) OPTIONAL MATCH (n)-[r]-(m) RETURN n, r, m
        Collection<Map<String, Object>> results = neo4jClient.query("MATCH (n:Person {name: $name}) OPTIONAL MATCH (n)-[r]-(m) RETURN n, r, m")
                .bind(name).to("name")
                .fetch().all();

        if (results.isEmpty()) return null;

        Node centerNode = (Node) results.iterator().next().get("n");
        if (centerNode == null) return null;

        GraphNode node = mapNode(centerNode, null);
        List<GraphEdge> edges = new ArrayList<>();

        for (Map<String, Object> row : results) {
            Relationship r = (Relationship) row.get("r");
            Node m = (Node) row.get("m");
            if (r != null && m != null) {
                // Check direction
                String direction = r.startNodeElementId().equals(centerNode.elementId()) ? "outgoing" : "incoming";
                List<String> targetLabels = StreamSupport.stream(m.labels().spliterator(), false).collect(Collectors.toList());
                
                GraphEdge edge = GraphEdge.builder()
                        .source(r.startNodeElementId().equals(centerNode.elementId()) ? node.getName() : m.get("name").asString())
                        .target(r.endNodeElementId().equals(centerNode.elementId()) ? node.getName() : m.get("name").asString())
                        .relation_type(r.type())
                        .direction(direction)
                        .target_labels(targetLabels)
                        .properties(r.asMap())
                        .build();
                edges.add(edge);
            }
        }

        Map<String, Object> data = new HashMap<>();
        data.put("node", node);
        data.put("edges", edges);
        data.put("edge_count", edges.size());
        return data;
    }

    @Override
    public Map<String, Object> getRelations(String source, String target) {
        Collection<Map<String, Object>> results = neo4jClient.query("MATCH (a {name: $source})-[r]-(b {name: $target}) RETURN a, r, b")
                .bind(source).to("source")
                .bind(target).to("target")
                .fetch().all();
        
        // This query might return duplicates if we don't specify direction. 
        // Flask example: "source": "高祖", "target": "吕后", "edges": [...]
        
        List<GraphEdge> edges = new ArrayList<>();
        for (Map<String, Object> row : results) {
            Relationship r = (Relationship) row.get("r");
            Node a = (Node) row.get("a");
            Node b = (Node) row.get("b");
            
            edges.add(mapEdge(r, a, b));
        }
        
        Map<String, Object> data = new HashMap<>();
        data.put("source", source);
        data.put("target", target);
        data.put("edges", edges);
        data.put("edge_count", edges.size());
        return data;
    }

    @Override
    public Map<String, Object> getEdgesByType(String type, int limit) {
        Collection<Map<String, Object>> results = neo4jClient.query("MATCH (a)-[r]->(b) WHERE type(r) = $type RETURN a, r, b LIMIT $limit")
                .bind(type).to("type")
                .bind(limit).to("limit")
                .fetch().all();
        
        List<GraphEdge> edges = new ArrayList<>();
        for (Map<String, Object> row : results) {
            Relationship r = (Relationship) row.get("r");
            Node a = (Node) row.get("a");
            Node b = (Node) row.get("b");
            edges.add(mapEdge(r, a, b));
        }
        
        Map<String, Object> data = new HashMap<>();
        data.put("relation_type", type);
        data.put("edges", edges);
        data.put("total_count", edges.size()); // This is just page count, assumes total logic elsewhere? Flask example: limit=50, total keys in example says 1.
        return data;
    }

    @Override
    public Map<String, Object> getAllEdges(int limit) {
        Collection<Map<String, Object>> results = neo4jClient.query("MATCH (a)-[r]->(b) RETURN a, r, b LIMIT $limit")
                .bind(limit).to("limit")
                .fetch().all();
        
        List<GraphEdge> edges = new ArrayList<>();
        for (Map<String, Object> row : results) {
            Relationship r = (Relationship) row.get("r");
            Node a = (Node) row.get("a");
            Node b = (Node) row.get("b");
            edges.add(mapEdge(r, a, b));
        }
        
        Map<String, Object> data = new HashMap<>();
        data.put("relation_type", "ALL");
        data.put("edges", edges);
        return data;
    }

    @Override
    public Map<String, Object> getNeighbors(String name, int limit) {
        // GET /api/graph/neighbors?name=高祖&limit=20
        Collection<Map<String, Object>> results = neo4jClient.query("MATCH (n {name: $name})-[r]-(m) RETURN n, r, m LIMIT $limit")
                .bind(name).to("name")
                .bind(limit).to("limit")
                .fetch().all();

        Set<GraphNode> nodes = new HashSet<>();
        List<GraphEdge> edges = new ArrayList<>();
        
        if (!results.isEmpty()) {
            Node center = (Node) results.iterator().next().get("n");
            nodes.add(mapNode(center, name));
            
            for (Map<String, Object> row : results) {
                Node m = (Node) row.get("m");
                Relationship r = (Relationship) row.get("r");
                Node n = (Node) row.get("n");
                
                nodes.add(mapNode(m, name));
                edges.add(mapEdge(r, n, m)); // Assuming n is always source of query but might be target of rel
            }
        } else {
             Optional<Node> nodeOpt = neo4jClient.query("MATCH (n {name: $name}) RETURN n").bind(name).to("name").fetchAs(Node.class).one();
             nodeOpt.ifPresent(node -> nodes.add(mapNode(node, name)));
        }

        Map<String, Object> data = new HashMap<>();
        data.put("nodes", nodes);
        data.put("edges", edges);
        data.put("node_count", nodes.size());
        data.put("edge_count", edges.size());
        return data;
    }

    @Override
    public Map<String, Object> getSubgraph(String center, int depth, int limit) {
        // MATCH p=(n {name: $center})-[*1..depth]-(m) RETURN p LIMIT $limit
        String query = String.format("MATCH p=(n {name: $center})-[*1..%d]-(m) RETURN p LIMIT $limit", depth > 5 ? 5 : depth);
        
        Collection<Path> paths = neo4jClient.query(query)
                .bind(center).to("center")
                .bind(limit).to("limit")
                .fetchAs(Path.class)
                .all();
        
        Map<String, GraphNode> nodeMap = new HashMap<>();
        List<GraphEdge> edgeList = new ArrayList<>();
        Set<String> processedEdges = new HashSet<>();

        // Add center node if exists even if no paths? (if path length 0 allowed? No range is 1..depth)
        // If paths empty, fetch center?
        
        for (Path path : paths) {
            for (Node node : path.nodes()) {
                if (node != null) {
                    String id = String.valueOf(node.elementId());
                    if (!nodeMap.containsKey(id)) {
                        nodeMap.put(id, mapNode(node, center));
                    }
                }
            }
            for (Relationship rel : path.relationships()) {
                String id = String.valueOf(rel.elementId());
                if (!processedEdges.contains(id)) {
                    // Find start/end nodes in map?
                    // Relationships in path have implicit start/end
                    // But we need to map them with names.
                    // The path.nodes() contains them.
                    
                    // Or simpler: access start/end from rel, query nodes from map?
                    // rel.startNodeElementId()
                    // The nodes map is keyed by elementId
                    // BUT: path.relationships() gives relationships. We need to look up their start/end nodes to get names for mapEdge.
                    // mapEdge (rel, src, tgt)
                    
                    // Usually in paths, segments contain start/end.
                    // Or simplify: Just map generic props and source/target NAMES (which we might not have efficiently without lookup).
                    // Actually rel.startNodeElementId() and we have map.
                    
                    // Let's assume map has them because path.nodes() includes all nodes in path.
                    String source = getNameFromMap(nodeMap, rel.startNodeElementId());
                    String target = getNameFromMap(nodeMap, rel.endNodeElementId());
                    if (source != null && target != null) {
                        edgeList.add(GraphEdge.builder()
                                .source(source)
                                .target(target)
                                .relation_type(rel.type())
                                .properties(rel.asMap())
                                .build());
                    }
                    processedEdges.add(id);
                }
            }
        }
        
        // If empty, try to get just center
        if (nodeMap.isEmpty()) {
             Optional<Node> nodeOpt = neo4jClient.query("MATCH (n {name: $name}) RETURN n").bind(center).to("name").fetchAs(Node.class).one();
             nodeOpt.ifPresent(node -> nodeMap.put(String.valueOf(node.elementId()), mapNode(node, center)));
        }

        Map<String, Object> data = new HashMap<>();
        data.put("center", center);
        data.put("depth", depth);
        data.put("nodes", nodeMap.values());
        data.put("edges", edgeList);
        data.put("node_count", nodeMap.size());
        data.put("edge_count", edgeList.size());
        return data;
    }
    
    private String getNameFromMap(Map<String, GraphNode> map, String elementId) {
        // elementId is string in v5 driver
        // In previous versions id() was long. elementId() returns generic ID.
        // We stored key as String.
        GraphNode n = map.get(elementId);
        return n != null ? n.getName() : null;
    }

    @Override
    public Map<String, Object> getShortestPath(String source, String target, int maxLength) {
        String query = String.format("MATCH p=shortestPath((a {name: $source})-[*..%d]-(b {name: $target})) RETURN p", maxLength);
        Optional<Path> pathOpt = neo4jClient.query(query)
                .bind(source).to("source")
                .bind(target).to("target")
                .fetchAs(Path.class).one();
        
        if (pathOpt.isPresent()) {
            Path path = pathOpt.get();
            List<GraphNode> nodes = new ArrayList<>();
            List<GraphEdge> edges = new ArrayList<>();
            
            for (Node n : path.nodes()) nodes.add(mapNode(n, null));
            
            // For path edges, we need names.
            Map<String, String> idToName = nodes.stream().collect(Collectors.toMap(GraphNode::getId, GraphNode::getName));
            
            for (Relationship r : path.relationships()) {
                String edgeSource = idToName.get(r.startNodeElementId());
                String edgeTarget = idToName.get(r.endNodeElementId());
                if (edgeSource != null && edgeTarget != null) {
                    edges.add(GraphEdge.builder()
                            .source(edgeSource)
                            .target(edgeTarget)
                            .relation_type(r.type())
                            .properties(r.asMap())
                            .build());
                }
            }
            
            Map<String, Object> data = new HashMap<>();
            data.put("source", source);
            data.put("target", target);
            data.put("path_length", path.length());
            data.put("nodes", nodes);
            data.put("edges", edges);
            return data;
        }
        return null;
    }

    @Override
    public Map<String, Object> searchLocation(String name) {
        Collection<Map<String, Object>> results = neo4jClient.query("MATCH (n:Location {name: $name}) OPTIONAL MATCH (n)-[r]-(m) RETURN n, r, m")
                .bind(name).to("name")
                .fetch().all();
        
        if (results.isEmpty()) return null;
        
        Node center = (Node) results.iterator().next().get("n");
        List<String> labels = StreamSupport.stream(center.labels().spliterator(), false).collect(Collectors.toList());

        // Actually, let's just construct the 'data' map directly.
        // relationships: [{target:..., relation_type:..., target_labels: [...]}]
        
        List<Map<String, Object>> relList = new ArrayList<>();
         for (Map<String, Object> row : results) {
            Relationship r = (Relationship) row.get("r");
            Node m = (Node) row.get("m");
            if (r != null && m != null) {
                 List<String> mLabels = StreamSupport.stream(m.labels().spliterator(), false).collect(Collectors.toList());
                 Map<String, Object> item = new HashMap<>();
                 item.put("target", m.get("name").asString());
                 item.put("relation_type", r.type());
                 item.put("target_labels", mLabels);
                 relList.add(item);
            }
         }

        Map<String, Object> data = new HashMap<>();
        data.put("name", center.get("name").asString());
        data.put("labels", labels);
        data.put("relations", relList);
        return data;
    }

    @Override
    public Object searchAll(String keyword) {
        Collection<Node> nodes = neo4jClient.query("MATCH (n) WHERE n.name CONTAINS $keyword RETURN n")
                .bind(keyword).to("keyword")
                .fetchAs(Node.class).all();
        
        List<Map<String, Object>> list = new ArrayList<>();
        for (Node n : nodes) {
            Map<String, Object> map = new HashMap<>();
            map.put("name", n.get("name").asString());
            map.put("labels", StreamSupport.stream(n.labels().spliterator(), false).collect(Collectors.toList()));
            list.add(map);
        }
        return list; // And Controller will assume it's list
    }

    @Override
    public Map<String, Object> getWholeGraph(int limit) {
        // Use OPTIONAL MATCH to ensure isolated nodes (like Events) are included
        // MATCH (n) WITH n LIMIT $limit allows picking 'limit' nodes first, then finding their edges.
        String query = "MATCH (n) WITH n LIMIT $limit OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m";
        Collection<Map<String, Object>> result = neo4jClient.query(query)
                .bind(limit).to("limit")
                .fetch().all();

        Map<String, GraphNode> nodeMap = new HashMap<>();
        List<GraphEdge> edgeList = new ArrayList<>();
        Set<String> processedEdges = new HashSet<>();

        for (Map<String, Object> row : result) {
            Node n = (Node) row.get("n");
            Node m = (Node) row.get("m");
            Relationship r = (Relationship) row.get("r");

            if (n != null && !nodeMap.containsKey(String.valueOf(n.elementId()))) {
                nodeMap.put(String.valueOf(n.elementId()), mapNode(n, null));
            }
            if (m != null && !nodeMap.containsKey(String.valueOf(m.elementId()))) {
                nodeMap.put(String.valueOf(m.elementId()), mapNode(m, null));
            }
            if (r != null && !processedEdges.contains(String.valueOf(r.elementId()))) {
                if (n != null && m != null) {
                    edgeList.add(GraphEdge.builder()
                            .source(n.get("name").asString())
                            .target(m.get("name").asString())
                            .relation_type(r.type())
                            .properties(r.asMap())
                            .build());
                    processedEdges.add(String.valueOf(r.elementId()));
                }
            }
        }
        
        Map<String, Object> data = new HashMap<>();
        data.put("nodes", nodeMap.values());
        data.put("edges", edgeList);
        return data;
    }

    @Override
    public Map<String, Object> getNodesByLabel(String label, int limit) {
        // Query to fetch nodes by label AND their validation relationships
        // Using (n)-[r]-(m) to get all connected edges (incoming/outgoing)
        String query = String.format("MATCH (n:`%s`) WITH n LIMIT $limit OPTIONAL MATCH (n)-[r]-(m) RETURN n, r, m", label.replace("`", ""));
        
        Collection<Map<String, Object>> results = neo4jClient.query(query)
                .bind(limit).to("limit")
                .fetch().all();
        
        Map<String, GraphNode> nodeMap = new HashMap<>();
        List<GraphEdge> edges = new ArrayList<>();
        Set<String> processedEdgeIds = new HashSet<>();
        
        for (Map<String, Object> row : results) {
            Node n = (Node) row.get("n");
            if (n != null) {
                String nId = n.elementId();
                if (!nodeMap.containsKey(nId)) {
                    nodeMap.put(nId, mapNode(n, null));
                }
                
                Object rObj = row.get("r");
                if (rObj instanceof Relationship) {
                    Relationship r = (Relationship) rObj;
                    Node m = (Node) row.get("m");
                    
                    if (m != null) {
                        String mId = m.elementId();
                        if (!nodeMap.containsKey(mId)) {
                            nodeMap.put(mId, mapNode(m, null));
                        }
                        
                        if (!processedEdgeIds.contains(r.elementId())) {
                            // Start/End check
                            Node startNode = r.startNodeElementId().equals(nId) ? n : m;
                            Node endNode = r.endNodeElementId().equals(nId) ? n : m;
                            
                            edges.add(mapEdge(r, startNode, endNode));
                            processedEdgeIds.add(r.elementId());
                        }
                    }
                }
            }
        }
        
        Map<String, Object> result = new HashMap<>();
        result.put("nodes", nodeMap.values());
        result.put("relationships", edges);
        return result;
    }

    @Override
    public Map<String, Object> getStats() {
        // Run two queries
        Collection<Map<String, Object>> nodeStats = neo4jClient.query("MATCH (n) RETURN labels(n) as l, count(*) as c").fetch().all();
        Collection<Map<String, Object>> relStats = neo4jClient.query("MATCH ()-[r]->() RETURN type(r) as t, count(*) as c").fetch().all();

        Map<String, Long> nodesByLabel = new HashMap<>();
        for (Map<String, Object> row : nodeStats) {
             // labels(n) returns a List
             @SuppressWarnings("unchecked")
             List<String> lbls = (List<String>) row.get("l");
             Long count = (Long) row.get("c");
             for (String l : lbls) {
                 nodesByLabel.put(l, nodesByLabel.getOrDefault(l, 0L) + count); 
                 // Note: if node has multiple labels, it counts for both. 
                 // Flask implementation might be: MATCH (n:Label) count(*)? No, that's many queries.
                 // The displayed output "Person: 25, Location: 15" suggests grouping by primary label or all labels.
             }
        }
        
        Map<String, Long> relsByType = new HashMap<>();
        for (Map<String, Object> row : relStats) {
            String type = (String) row.get("t");
            Long count = (Long) row.get("c");
            relsByType.put(type, count);
        }

        Map<String, Object> data = new HashMap<>();
        data.put("nodes_by_label", nodesByLabel);
        data.put("relations_by_type", relsByType);
        return data;
    }
}
