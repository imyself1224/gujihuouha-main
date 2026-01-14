package com.example.gujihuohua.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.example.gujihuohua.entity.AncientText;
import com.example.gujihuohua.mapper.AncientTextMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 古籍事件关系识别服务实现
 * 调用 Flask 端口 5004 的 ERI 模型
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class EriServiceImpl implements EriService {

    private final RestTemplate restTemplate;
    private final AncientTextMapper ancientTextMapper;
    private final NerService nerService; // 用于获取触发词

    @Value("${app.storage.root-path}")
    private String storageRoot;

    // Flask ERI 服务地址
    private static final String ERI_SERVICE_URL = "http://localhost:5004";

    // 进度缓存
    private final ConcurrentHashMap<Long, Integer> progressMap = new ConcurrentHashMap<>();

    // 结果缓存（内存存储）
    private final ConcurrentHashMap<Long, List<Map<String, Object>>> resultMap = new ConcurrentHashMap<>();

    /**
     * 单个事件关系预测
     */
    @Override
    public Map<String, Object> predictSingle(String text, String headTrigger, String tailTrigger) {
        Map<String, Object> result = new HashMap<>();

        try {
            // 准备请求数据
            JSONObject requestData = new JSONObject();
            requestData.put("text", text);
            requestData.put("head_trigger", headTrigger);
            requestData.put("tail_trigger", tailTrigger);

            log.info("调用 ERI 预测: text={}, head={}, tail={}", text, headTrigger, tailTrigger);

            // 调用 Flask 服务
            Map<String, Object> flaskResult = callFlaskService("/predict", requestData.toJSONString());

            if ("success".equals(flaskResult.get("status"))) {
                result.put("status", "success");
                result.put("predicted_relation", flaskResult.get("predicted_relation"));
                result.put("probabilities", flaskResult.get("probabilities"));
                result.put("text", text);
                result.put("head_trigger", headTrigger);
                result.put("tail_trigger", tailTrigger);
            } else {
                result.put("status", "error");
                result.put("error", flaskResult.get("error"));
            }

            return result;

        } catch (Exception e) {
            log.error("ERI 单个预测失败", e);
            result.put("status", "error");
            result.put("error", "调用 ERI 服务失败: " + e.getMessage());
            return result;
        }
    }

    /**
     * 批量事件关系预测
     */
    @Override
    public Map<String, Object> predictBatch(List<Map<String, String>> samples) {
        Map<String, Object> result = new HashMap<>();

        try {
            // 准备批量请求数据
            JSONObject requestData = new JSONObject();
            requestData.put("samples", samples);

            log.info("调用 ERI 批量预测: 样本数={}", samples.size());

            // 调用 Flask 服务
            Map<String, Object> flaskResult = callFlaskService("/predict_batch", requestData.toJSONString());

            if ("success".equals(flaskResult.get("status"))) {
                result.put("status", "success");
                result.put("results", flaskResult.get("results"));
                result.put("total", samples.size());
            } else {
                result.put("status", "error");
                result.put("error", flaskResult.get("error"));
            }

            return result;

        } catch (Exception e) {
            log.error("ERI 批量预测失败", e);
            result.put("status", "error");
            result.put("error", "调用 ERI 服务失败: " + e.getMessage());
            return result;
        }
    }

    /**
     * 异步批量分析任务
     */
    @Override
    @Async
    public void runBatchAnalysisAsync(Long corpusId) {
        progressMap.put(corpusId, 0);
        resultMap.remove(corpusId);

        try {
            // 1. 获取语料信息
            AncientText textInfo = ancientTextMapper.selectById(corpusId);
            if (textInfo == null) {
                progressMap.put(corpusId, 100);
                return;
            }

            // 2. 读取文件
            String targetPath = (textInfo.getJsonPath() != null && !textInfo.getJsonPath().isEmpty())
                    ? textInfo.getJsonPath() : textInfo.getRawPath();
            Path filePath = Paths.get(storageRoot, targetPath);

            if (!Files.exists(filePath)) {
                filePath = Paths.get(storageRoot, textInfo.getRawPath());
            }

            if (!Files.exists(filePath)) {
                log.error("文件不存在: {}", filePath);
                progressMap.put(corpusId, 100);
                return;
            }

            // 3. 读取并解析内容
            String content = new String(Files.readAllBytes(filePath), StandardCharsets.UTF_8).trim();
            List<String> sentences = parseSentences(content);

            int total = sentences.size();
            List<Map<String, Object>> analysisResults = new ArrayList<>();

            // 4. 逐句分析：先进行 NER 得到触发词，再进行 ERI
            for (int i = 0; i < total; i++) {
                String sent = sentences.get(i);
                if (sent.length() < 2) continue;

                try {
                    // 先调用 NER 获取事件触发词
                    Map<String, Object> nerResult = nerService.extractEntitiesForSingle(sent);
                    
                    // 从 NER 结果中提取可能的事件触发词（这里简化处理，实际可能需要更复杂的逻辑）
                    List<String> triggers = extractTriggers(nerResult);

                    // 对每对触发词进行关系预测
                    for (int j = 0; j < triggers.size() - 1; j++) {
                        for (int k = j + 1; k < triggers.size(); k++) {
                            String headTrigger = triggers.get(j);
                            String tailTrigger = triggers.get(k);

                            Map<String, Object> prediction = predictSingle(sent, headTrigger, tailTrigger);
                            
                            if ("success".equals(prediction.get("status"))) {
                                prediction.put("index", i + 1);
                                prediction.put("sentence", sent);
                                analysisResults.add(prediction);
                            }
                        }
                    }
                } catch (Exception e) {
                    log.warn("处理第 {} 个句子失败: {}", i + 1, e.getMessage());
                }

                // 更新进度
                int percent = (int) (((double) (i + 1) / total) * 100);
                progressMap.put(corpusId, percent);
            }

            // 5. 存入内存
            resultMap.put(corpusId, analysisResults);
            log.info("批量分析完成: corpusId={}, 总关系数={}", corpusId, analysisResults.size());

        } catch (Exception e) {
            log.error("批量分析异常", e);
        } finally {
            progressMap.put(corpusId, 100);
        }
    }

    /**
     * 获取分析进度
     */
    @Override
    public Integer getProgress(Long corpusId) {
        return progressMap.getOrDefault(corpusId, 0);
    }

    /**
     * 获取分析结果
     */
    @Override
    public List<Map<String, Object>> getResults(Long corpusId) {
        return resultMap.getOrDefault(corpusId, new ArrayList<>());
    }

    // ==================== 辅助方法 ====================

    /**
     * 调用 Flask ERI 服务
     */
    @SuppressWarnings("null")
    private Map<String, Object> callFlaskService(String endpoint, String requestData) {
        Map<String, Object> result = new HashMap<>();

        try {
            // 准备请求头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(new MediaType("application", "json", StandardCharsets.UTF_8));

            // 创建请求体
            HttpEntity<String> request = new HttpEntity<>(requestData, headers);

            // 发送 POST 请求
            ResponseEntity<String> response = restTemplate.postForEntity(
                    ERI_SERVICE_URL + endpoint,
                    request,
                    String.class
            );

            // 解析响应
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                JSONObject responseJson = JSONObject.parseObject(response.getBody());
                result.putAll(responseJson);
                log.info("Flask 服务返回成功: {}", responseJson.get("status"));
            } else {
                log.warn("Flask 服务返回非 2xx 状态码: {}", response.getStatusCode());
                result.put("status", "error");
                result.put("error", "服务返回失败状态: " + response.getStatusCode());
            }

        } catch (Exception e) {
            log.error("调用 Flask 服务失败: {}", e.getMessage());
            result.put("status", "error");
            result.put("error", e.getMessage());
        }

        return result;
    }

    /**
     * 解析句子
     */
    private List<String> parseSentences(String content) {
        List<String> list = new ArrayList<>();
        if (content.startsWith("[")) {
            try {
                List<JSONObject> jsonList = JSON.parseArray(content, JSONObject.class);
                for (JSONObject obj : jsonList) {
                    String s = obj.containsKey("content") ? obj.getString("content") : obj.getString("text");
                    if (s != null && !s.isEmpty()) list.add(s);
                }
            } catch (Exception e) {
                String[] lines = content.split("\n");
                for (String s : lines) {
                    if (!s.trim().isEmpty()) list.add(s.trim());
                }
            }
        } else {
            String[] lines = content.split("\n");
            for (String s : lines) {
                if (!s.trim().isEmpty()) list.add(s.trim());
            }
        }
        return list;
    }

    /**
     * 从 NER 结果中提取事件触发词
     * （简化实现，可根据实际需求调整）
     */
    @SuppressWarnings("unchecked")
    private List<String> extractTriggers(Map<String, Object> nerResult) {
        List<String> triggers = new ArrayList<>();

        try {
            if (nerResult != null && nerResult.containsKey("entities")) {
                Object entitiesObj = nerResult.get("entities");
                
                if (entitiesObj instanceof Map) {
                    Map<String, Object> entities = (Map<String, Object>) entitiesObj;
                    
                    // 从所有实体类型中提取实体作为触发词
                    for (Object values : entities.values()) {
                        if (values instanceof List) {
                            List<?> list = (List<?>) values;
                            for (Object item : list) {
                                if (item instanceof Map) {
                                    Map<String, Object> entity = (Map<String, Object>) item;
                                    String text = (String) entity.get("text");
                                    if (text != null && !text.isEmpty()) {
                                        triggers.add(text);
                                    }
                                } else if (item instanceof String) {
                                    triggers.add((String) item);
                                }
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.warn("提取触发词失败: {}", e.getMessage());
        }

        // 如果没有提取到触发词，返回空列表
        return triggers;
    }
}
