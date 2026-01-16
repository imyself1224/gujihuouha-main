package com.example.gujihuohua.entity.graph;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GraphEdge {
    private String source;
    private String target;
    private String relation_type;
    private String direction; // incoming, outgoing
    private List<String> source_labels;
    private List<String> target_labels;
    private Map<String, Object> properties;
}
