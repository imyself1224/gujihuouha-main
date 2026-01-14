package com.example.gujihuohua.controller;

import com.example.gujihuohua.service.ExeService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 事件抽取控制器
 * 提供古文事件抽取的 REST API 接口
 */
@RestController
@RequestMapping("/api/analysis/event-extraction")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
@Slf4j
public class ExeController {

    private final ExeService eventExtractionService;

    /**
     * 根据文本查询事件抽取结果（核心接口）
     * POST /api/analysis/event-extraction/query-by-text
     *
     * @param params 请求参数，包含 text 和 dataset
     * @return 事件抽取结果
     */
    @PostMapping("/query-by-text")
    public ResponseEntity<Map<String, Object>> queryEventByText(@RequestBody Map<String, String> params) {
        String text = params.get("text");
        String dataset = params.getOrDefault("dataset", "Hangaozubenji");

        if (text == null || text.trim().isEmpty()) {
            Map<String, Object> error = new java.util.HashMap<>();
            error.put("status", "error");
            error.put("message", "文本内容不能为空");
            error.put("found", false);
            return ResponseEntity.badRequest().body(error);
        }

        log.info("收到事件抽取查询请求: text={}, dataset={}", text, dataset);
        Map<String, Object> result = eventExtractionService.queryEventByText(text, dataset);

        // 如果找到结果，返回 200；否则返回 404
        if ((Boolean) result.getOrDefault("found", false)) {
            return ResponseEntity.ok(result);
        } else if ("success".equals(result.get("status"))) {
            return ResponseEntity.status(404).body(result);
        } else {
            return ResponseEntity.status(500).body(result);
        }
    }

    /**
     * 获取所有可用的数据集列表
     * GET /api/analysis/event-extraction/datasets
     *
     * @return 数据集列表
     */
    @GetMapping("/datasets")
    public ResponseEntity<Map<String, Object>> getDatasets() {
        log.info("获取数据集列表");
        Map<String, Object> result = eventExtractionService.getDatasets();
        return ResponseEntity.ok(result);
    }

    /**
     * 获取指定数据集的统计信息
     * GET /api/analysis/event-extraction/stats/{datasetName}
     *
     * @param datasetName 数据集名称
     * @return 统计信息
     */
    @GetMapping("/stats/{datasetName}")
    public ResponseEntity<Map<String, Object>> getDatasetStats(@PathVariable String datasetName) {
        log.info("获取数据集统计: {}", datasetName);
        Map<String, Object> result = eventExtractionService.getDatasetStats(datasetName);
        return ResponseEntity.ok(result);
    }

    /**
     * 分页获取训练数据
     * POST /api/analysis/event-extraction/training-data
     *
     * @param params 请求参数
     * @return 训练数据列表
     */
    @PostMapping("/training-data")
    public ResponseEntity<Map<String, Object>> getTrainingData(@RequestBody Map<String, Object> params) {
        String dataset = (String) params.get("dataset");
        Integer limit = (Integer) params.get("limit");
        Integer offset = (Integer) params.get("offset");

        if (dataset == null || dataset.isEmpty()) {
            Map<String, Object> error = new java.util.HashMap<>();
            error.put("status", "error");
            error.put("message", "数据集名称不能为空");
            return ResponseEntity.badRequest().body(error);
        }

        log.info("获取训练数据: dataset={}, limit={}, offset={}", dataset, limit, offset);
        Map<String, Object> result = eventExtractionService.getTrainingData(dataset, limit, offset);
        return ResponseEntity.ok(result);
    }

    /**
     * 检查 Flask API 服务健康状态
     * GET /api/analysis/event-extraction/health
     *
     * @return 健康检查结果
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> checkHealth() {
        log.info("检查服务健康状态");
        Map<String, Object> result = eventExtractionService.checkHealth();
        return ResponseEntity.ok(result);
    }
}
