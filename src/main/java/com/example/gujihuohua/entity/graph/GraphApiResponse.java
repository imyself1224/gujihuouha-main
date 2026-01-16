package com.example.gujihuohua.entity.graph;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class GraphApiResponse<T> {
    private String status;
    private String message;
    private T data;
    
    // For pagination/stats
    private Integer total;

    public static <T> GraphApiResponse<T> success(T data) {
        return new GraphApiResponse<>("success", null, data, null);
    }
    
    public static <T> GraphApiResponse<T> success(T data, Integer total) {
        return new GraphApiResponse<>("success", null, data, total);
    }

    public static <T> GraphApiResponse<T> error(String message) {
        return new GraphApiResponse<>("error", message, null, null);
    }
}
