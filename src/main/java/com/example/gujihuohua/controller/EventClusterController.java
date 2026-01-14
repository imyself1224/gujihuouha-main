package com.example.gujihuohua.controller;

import com.alibaba.fastjson.JSONObject;
import com.example.gujihuohua.entity.ClusteringHistory;
import com.example.gujihuohua.service.EventClusteringService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * 事件聚类分析 API 控制器
 * 处理事件时空聚类相关的请求
 */
@RestController
@RequestMapping("/api/analysis/event-cluster")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
@Slf4j
public class EventClusterController {

    private final EventClusteringService clusteringService;

    /**
     * 执行事件聚类分析
     *
     * @param request 包含 locationData 和 eventsData 的请求
     *                locationData: CSV格式, 字段: ancient_name,modern_name,latitude,longitude
     *                eventsData: JSON格式, 结构: {"events": [{"id": "1", "year": 220, "location": "长安", "description": "..."}]}
     * @return 聚类分析结果
     */
    @PostMapping("/cluster")
    public ResponseEntity<Map<String, Object>> performClustering(@RequestBody JSONObject request) {
        Map<String, Object> response = new HashMap<>();

        try {
            String locationData = request.getString("locationData");
            String eventsData = request.getString("eventsData");
            String locationFileName = request.getString("locationFileName");
            String eventsFileName = request.getString("eventsFileName");

            // 使用默认文件名如果没有提供
            if (locationFileName == null || locationFileName.isEmpty()) {
                locationFileName = "locations.csv";
            }
            if (eventsFileName == null || eventsFileName.isEmpty()) {
                eventsFileName = "events.json";
            }

            // 验证输入参数
            if (locationData == null || locationData.trim().isEmpty()) {
                response.put("status", "error");
                response.put("message", "地名数据不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            if (eventsData == null || eventsData.trim().isEmpty()) {
                response.put("status", "error");
                response.put("message", "事件数据不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            // 验证数据格式
            if (!clusteringService.validateLocationData(locationData)) {
                response.put("status", "error");
                response.put("message", "地名数据格式无效，应包含: ancient_name,latitude,longitude");
                return ResponseEntity.badRequest().body(response);
            }

            if (!clusteringService.validateEventsData(eventsData)) {
                response.put("status", "error");
                response.put("message", "事件数据格式无效，应为JSON，包含events数组");
                return ResponseEntity.badRequest().body(response);
            }

            log.info("接收到聚类请求: locationFileName={}, eventsFileName={}", locationFileName, eventsFileName);

            // 执行聚类分析并保存历史记录
            Map<String, Object> clusteringResult = clusteringService.performClusteringWithHistory(
                    locationData, eventsData, locationFileName, eventsFileName);

            if ("success".equals(clusteringResult.get("status"))) {
                // 增强响应信息
                response.put("status", "success");
                response.put("message", clusteringResult.get("message"));
                response.put("data", clusteringResult.get("data"));
                response.put("analysisId", clusteringResult.get("analysisId"));
                
                // 添加文件保存路径信息
                if (clusteringResult.containsKey("locationFilePath")) {
                    response.put("locationFilePath", clusteringResult.get("locationFilePath"));
                }
                if (clusteringResult.containsKey("eventsFilePath")) {
                    response.put("eventsFilePath", clusteringResult.get("eventsFilePath"));
                }
                
                log.info("✓ 聚类分析成功: analysisId={}, locationFile={}, eventsFile={}", 
                        clusteringResult.get("analysisId"), 
                        clusteringResult.get("locationFilePath"),
                        clusteringResult.get("eventsFilePath"));
                
                return ResponseEntity.ok(response);
            } else {
                // 错误响应
                response.put("status", "error");
                response.put("message", clusteringResult.get("message"));
                response.put("error", clusteringResult.get("error"));
                response.put("analysisId", clusteringResult.get("analysisId"));
                
                // 即使出错也返回文件保存路径，便于调试
                if (clusteringResult.containsKey("locationFilePath")) {
                    response.put("locationFilePath", clusteringResult.get("locationFilePath"));
                }
                if (clusteringResult.containsKey("eventsFilePath")) {
                    response.put("eventsFilePath", clusteringResult.get("eventsFilePath"));
                }
                
                log.error("✗ 聚类分析失败: {}", clusteringResult.get("error"));
                return ResponseEntity.internalServerError().body(response);
            }

        } catch (Exception e) {
            log.error("聚类分析异常", e);
            response.put("status", "error");
            response.put("message", "聚类分析异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 获取所有聚类分析历史记录
     *
     * @return 历史记录列表
     */
    @GetMapping("/history")
    public ResponseEntity<Map<String, Object>> getClusteringHistory() {
        Map<String, Object> response = new HashMap<>();

        try {
            List<ClusteringHistory> historyList = clusteringService.getClusteringHistory();
            
            response.put("status", "success");
            response.put("message", "获取历史记录成功");
            response.put("data", historyList);
            response.put("total", historyList.size());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("获取历史记录异常", e);
            response.put("status", "error");
            response.put("message", "获取历史记录异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 获取最近的聚类分析记录
     *
     * @param limit 限制数量，默认10条
     * @return 历史记录列表
     */
    @GetMapping("/history/recent")
    public ResponseEntity<Map<String, Object>> getRecentClusteringHistory(
            @RequestParam(value = "limit", defaultValue = "10") int limit) {
        Map<String, Object> response = new HashMap<>();

        try {
            if (limit <= 0) {
                limit = 10;
            }
            if (limit > 100) {
                limit = 100;
            }

            List<ClusteringHistory> historyList = clusteringService.getRecentClusteringHistory(limit);
            
            response.put("status", "success");
            response.put("message", "获取最近历史记录成功");
            response.put("data", historyList);
            response.put("total", historyList.size());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("获取最近历史记录异常", e);
            response.put("status", "error");
            response.put("message", "获取最近历史记录异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 获取所有分析日期列表
     *
     * @return 日期列表
     */
    @GetMapping("/history/dates")
    public ResponseEntity<Map<String, Object>> getAnalysisDates() {
        Map<String, Object> response = new HashMap<>();

        try {
            List<String> dates = clusteringService.getAnalysisDates();
            
            response.put("status", "success");
            response.put("message", "获取日期列表成功");
            response.put("data", dates);
            response.put("total", dates.size());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("获取日期列表异常", e);
            response.put("status", "error");
            response.put("message", "获取日期列表异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 获取指定日期的所有聚类分析记录
     *
     * @param date 日期字符串 (格式: yyyy-MM-dd)
     * @return 该日期的记录列表
     */
    @GetMapping("/history/date/{date}")
    public ResponseEntity<Map<String, Object>> getRecordsByDate(@PathVariable String date) {
        Map<String, Object> response = new HashMap<>();

        try {
            List<Map<String, Object>> records = clusteringService.getRecordsByDate(date);
            
            response.put("status", "success");
            response.put("message", "获取" + date + "的记录成功");
            response.put("date", date);
            response.put("data", records);
            response.put("total", records.size());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("获取日期记录异常", e);
            response.put("status", "error");
            response.put("message", "获取日期记录异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 获取按日期分组的聚类分析历史记录
     *
     * @return 按日期分组的历史记录
     */
    @GetMapping("/history/grouped")
    public ResponseEntity<Map<String, Object>> getClusteringHistoryGroupedByDate() {
        Map<String, Object> response = new HashMap<>();

        try {
            Map<String, List<ClusteringHistory>> historyByDate = clusteringService.getClusteringHistoryGroupedByDate();
            
            response.put("status", "success");
            response.put("message", "获取分组历史记录成功");
            response.put("data", historyByDate);
            response.put("total", historyByDate.values().stream().mapToInt(List::size).sum());

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("获取分组历史记录异常", e);
            response.put("status", "error");
            response.put("message", "获取分组历史记录异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 根据历史记录重新运行聚类分析
     *
     * @param request 包含 locationFilePath 和 eventsFilePath 的请求
     * @return 重新运行的聚类分析结果
     */
    @PostMapping("/rerun")
    public ResponseEntity<Map<String, Object>> rerunClustering(@RequestBody JSONObject request) {
        Map<String, Object> response = new HashMap<>();

        try {
            String locationFilePath = request.getString("locationFilePath");
            String eventsFilePath = request.getString("eventsFilePath");
            String locationFileName = request.getString("locationFileName");
            String eventsFileName = request.getString("eventsFileName");

            // 验证输入参数
            if (locationFilePath == null || locationFilePath.trim().isEmpty()) {
                response.put("status", "error");
                response.put("message", "地点文件路径不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            if (eventsFilePath == null || eventsFilePath.trim().isEmpty()) {
                response.put("status", "error");
                response.put("message", "事件文件路径不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            log.info("重新运行聚类分析: locationFilePath={}, eventsFilePath={}", locationFilePath, eventsFilePath);

            // 调用Service重新运行分析
            Map<String, Object> clusteringResult = clusteringService.rerunClusteringAnalysis(
                    locationFilePath, eventsFilePath, locationFileName, eventsFileName);

            if ("success".equals(clusteringResult.get("status"))) {
                return ResponseEntity.ok(clusteringResult);
            } else {
                return ResponseEntity.internalServerError().body(clusteringResult);
            }

        } catch (Exception e) {
            log.error("重新运行聚类分析异常", e);
            response.put("status", "error");
            response.put("message", "重新运行聚类分析异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 删除聚类分析历史记录
     * 
     * @param analysisId 分析ID
     * @return 操作结果
     */
    @DeleteMapping("/history/{analysisId}")
    public ResponseEntity<Map<String, Object>> deleteAnalysisHistory(@PathVariable String analysisId) {
        Map<String, Object> response = new HashMap<>();

        try {
            boolean success = clusteringService.deleteAnalysisHistory(analysisId);
            
            if (success) {
                response.put("status", "success");
                response.put("message", "历史记录删除成功");
                return ResponseEntity.ok(response);
            } else {
                response.put("status", "error");
                response.put("message", "历史记录未找到或删除失败");
                return ResponseEntity.badRequest().body(response);
            }
        } catch (Exception e) {
            log.error("删除历史记录异常", e);
            response.put("status", "error");
            response.put("message", "删除历史记录异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 根据分析ID获取聚类分析记录详情
     *
     * @param analysisId 分析ID
     * @return 历史记录详情
     */
    @GetMapping("/history/{analysisId}")
    public ResponseEntity<Map<String, Object>> getClusteringHistoryDetail(@PathVariable String analysisId) {
        Map<String, Object> response = new HashMap<>();

        try {
            Optional<ClusteringHistory> history = clusteringService.getClusteringHistoryById(analysisId);
            
            if (history.isPresent()) {
                response.put("status", "success");
                response.put("message", "获取历史记录详情成功");
                response.put("data", history.get());
            } else {
                response.put("status", "error");
                response.put("message", "未找到指定的分析记录");
                return ResponseEntity.status(404).body(response);
            }

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("获取历史记录详情异常", e);
            response.put("status", "error");
            response.put("message", "获取历史记录详情异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 获取聚类分析统计信息
     *
     * @return 统计信息
     */
    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getClusteringStatistics() {
        Map<String, Object> response = new HashMap<>();

        try {
            Map<String, Object> statistics = clusteringService.getClusteringStatistics();
            
            response.put("status", "success");
            response.put("message", "获取统计信息成功");
            response.put("data", statistics);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("获取统计信息异常", e);
            response.put("status", "error");
            response.put("message", "获取统计信息异常: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 获取聚类分析API文档
     */
    @GetMapping("/info")
    public ResponseEntity<Map<String, Object>> getInfo() {
        Map<String, Object> info = new HashMap<>();
        
        info.put("service", "事件时空聚类分析服务");
        info.put("version", "2.0");
        info.put("endpoints", new Object[]{
            new Object[]{
                "POST /api/analysis/event-cluster/cluster",
                "执行事件聚类分析"
            },
            new Object[]{
                "GET /api/analysis/event-cluster/history",
                "获取所有聚类分析历史记录"
            },
            new Object[]{
                "GET /api/analysis/event-cluster/history/recent",
                "获取最近的聚类分析记录"
            },
            new Object[]{
                "GET /api/analysis/event-cluster/history/{analysisId}",
                "根据分析ID获取聚类分析记录详情"
            },
            new Object[]{
                "GET /api/analysis/event-cluster/statistics",
                "获取聚类分析统计信息"
            }
        });
        
        Map<String, Object> requestExample = new HashMap<>();
        requestExample.put("locationData", "ancient_name,modern_name,latitude,longitude\n长安,西安,34.5,108.9\n洛阳,洛阳,34.6,112.4");
        requestExample.put("eventsData", "{\"events\": [{\"id\": \"1\", \"year\": 220, \"location\": \"长安\", \"description\": \"某历史事件\"}]}");
        requestExample.put("locationFileName", "locations.csv");
        requestExample.put("eventsFileName", "events.json");
        
        info.put("requestExample", requestExample);
        
        return ResponseEntity.ok(info);
    }

    /**
     * 健康检查
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> health = new HashMap<>();
        health.put("status", "up");
        health.put("service", "event-cluster");
        return ResponseEntity.ok(health);
    }
}
