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
public class GraphNode {
    private String id;
    private String name;
    private List<String> labels;
    private Map<String, Object> properties;
    private Boolean is_center;
}
