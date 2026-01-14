package com.example.gujihuohua.controller;

import com.alibaba.fastjson.JSONObject;
import com.example.gujihuohua.service.EriService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 古籍事件关系识别 API 控制器
 * 负责处理事件关系识别相关的请求
 */
@RestController
@RequestMapping("/api/analysis/event-relation")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
@Slf4j
public class EriController {

    private final EriService eriService;

    /**
     * 单个事件关系预测
     *
     * @param request 包含 text, head_trigger, tail_trigger 的请求
     * @return 预测结果
     */
    @PostMapping("/predict")
    public ResponseEntity<Map<String, Object>> predictSingle(@RequestBody JSONObject request) {
        Map<String, Object> response = new HashMap<>();

        try {
            String text = request.getString("text");
            String headTrigger = request.getString("head_trigger");
            String tailTrigger = request.getString("tail_trigger");

            if (text == null || text.trim().isEmpty()) {
                response.put("status", "error");
                response.put("error", "文本不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            if (headTrigger == null || headTrigger.trim().isEmpty()) {
                response.put("status", "error");
                response.put("error", "头部触发词不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            if (tailTrigger == null || tailTrigger.trim().isEmpty()) {
                response.put("status", "error");
                response.put("error", "尾部触发词不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            log.info("收到事件关系预测请求: text={}, head={}, tail={}", text, headTrigger, tailTrigger);

            // 调用服务层
            Map<String, Object> result = eriService.predictSingle(text, headTrigger, tailTrigger);

            if ("success".equals(result.get("status"))) {
                return ResponseEntity.ok(result);
            } else {
                return ResponseEntity.internalServerError().body(result);
            }

        } catch (Exception e) {
            log.error("预测失败", e);
            response.put("status", "error");
            response.put("error", "预测失败: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 批量事件关系预测
     *
     * @param request 包含 samples 数组的请求
     * @return 批量预测结果
     */
    @PostMapping("/predict_batch")
    public ResponseEntity<Map<String, Object>> predictBatch(@RequestBody JSONObject request) {
        Map<String, Object> response = new HashMap<>();

        try {
            @SuppressWarnings("unchecked")
            List<Map<String, String>> samples = (List<Map<String, String>>) request.get("samples");

            if (samples == null || samples.isEmpty()) {
                response.put("status", "error");
                response.put("error", "样本列表不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            log.info("收到事件关系批量预测请求: 样本数={}", samples.size());

            // 调用服务层
            Map<String, Object> result = eriService.predictBatch(samples);

            if ("success".equals(result.get("status"))) {
                return ResponseEntity.ok(result);
            } else {
                return ResponseEntity.internalServerError().body(result);
            }

        } catch (Exception e) {
            log.error("批量预测失败", e);
            response.put("status", "error");
            response.put("error", "批量预测失败: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 启动异步批量分析任务
     *
     * @param request 包含 corpus_id 的请求
     * @return 启动结果
     */
    @PostMapping("/run_batch")
    public ResponseEntity<Map<String, Object>> runBatchAnalysis(@RequestBody JSONObject request) {
        Map<String, Object> response = new HashMap<>();

        try {
            Long corpusId = request.getLong("corpus_id");

            if (corpusId == null || corpusId <= 0) {
                response.put("status", "error");
                response.put("error", "corpus_id 不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            log.info("启动批量分析任务: corpusId={}", corpusId);

            // 异步启动分析
            eriService.runBatchAnalysisAsync(corpusId);

            response.put("status", "success");
            response.put("message", "分析任务已启动");
            response.put("corpus_id", corpusId);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("启动分析任务失败", e);
            response.put("status", "error");
            response.put("error", "启动分析失败: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 查询分析进度
     *
     * @param corpusId 语料库ID
     * @return 进度信息
     */
    @GetMapping("/progress/{corpus_id}")
    public ResponseEntity<Map<String, Object>> getProgress(@PathVariable("corpus_id") Long corpusId) {
        Map<String, Object> response = new HashMap<>();

        try {
            Integer progress = eriService.getProgress(corpusId);

            response.put("status", "success");
            response.put("corpus_id", corpusId);
            response.put("progress", progress);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("获取进度失败", e);
            response.put("status", "error");
            response.put("error", "获取进度失败: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 获取分析结果
     *
     * @param corpusId 语料库ID
     * @param page 分页页码（从1开始）
     * @param size 每页大小
     * @return 分析结果
     */
    @GetMapping("/results/{corpus_id}")
    public ResponseEntity<Map<String, Object>> getResults(
            @PathVariable("corpus_id") Long corpusId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "50") int size) {
        Map<String, Object> response = new HashMap<>();

        try {
            List<Map<String, Object>> allResults = eriService.getResults(corpusId);

            // 手动分页
            int total = allResults.size();
            int fromIndex = (page - 1) * size;
            int toIndex = Math.min(fromIndex + size, total);

            List<Map<String, Object>> pageRecords = new ArrayList<>();
            if (fromIndex < total && fromIndex >= 0) {
                pageRecords = allResults.subList(fromIndex, toIndex);
            }

            response.put("status", "success");
            response.put("records", pageRecords);
            response.put("total", total);
            response.put("size", size);
            response.put("current", page);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("获取结果失败", e);
            response.put("status", "error");
            response.put("error", "获取结果失败: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 健康检查
     *
     * @return 健康状态
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "ok");
        response.put("service", "event-relation-identification");
        response.put("timestamp", System.currentTimeMillis());
        return ResponseEntity.ok(response);
    }
}
