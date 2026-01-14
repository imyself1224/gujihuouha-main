package com.example.gujihuohua.service;

import com.alibaba.fastjson.JSON;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * 事件抽取服务
 * 调用 Flask API 进行古文事件抽取
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class ExeService {

    private final RestTemplate restTemplate;

    @Value("${flask.api.event-extraction.url:http://localhost:5003}")
    private String flaskApiUrl;

    /**
     * 根据文本查询事件抽取结果
     *
     * @param text 古文文本
     * @param dataset 数据集名称（可选，默认为 Hangaozubenji）
     * @return 事件抽取结果
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> queryEventByText(String text, String dataset) {
        try {
            log.info("查询文本事件抽取: text={}, dataset={}", text, dataset);

            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("text", text);
            if (dataset == null || dataset.isEmpty()) {
                requestBody.put("dataset", "Hangaozubenji");
            } else {
                requestBody.put("dataset", dataset);
            }

            // 设置请求头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            // 发送请求
            HttpEntity<String> entity = new HttpEntity<>(
                    JSON.toJSONString(requestBody),
                    headers
            );

            String url = flaskApiUrl + "/api/query-by-text";
            log.info("请求 Flask API: {}", url);

            ResponseEntity<String> response = restTemplate.postForEntity(
                    url,
                    entity,
                    String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                Map<String, Object> result = JSON.parseObject(
                        response.getBody(),
                        Map.class
                );
                log.info("事件抽取成功，found={}", result.get("found"));
                return result;
            } else {
                log.error("Flask API 返回错误状态码: {}", response.getStatusCode());
                return buildErrorResponse("Flask API 返回错误");
            }

        } catch (Exception e) {
            log.error("调用事件抽取 API 失败", e);
            return buildErrorResponse("调用事件抽取 API 失败: " + e.getMessage());
        }
    }

    /**
     * 获取所有可用数据集列表
     *
     * @return 数据集列表
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getDatasets() {
        try {
            log.info("获取数据集列表");

            String url = flaskApiUrl + "/api/datasets";
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                return JSON.parseObject(response.getBody(), Map.class);
            } else {
                return buildErrorResponse("获取数据集失败");
            }

        } catch (Exception e) {
            log.error("获取数据集列表失败", e);
            return buildErrorResponse("获取数据集列表失败: " + e.getMessage());
        }
    }

    /**
     * 获取数据集统计信息
     *
     * @param datasetName 数据集名称
     * @return 统计信息
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getDatasetStats(String datasetName) {
        try {
            log.info("获取数据集统计: {}", datasetName);

            String url = flaskApiUrl + "/api/training-stats/" + datasetName;
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                return JSON.parseObject(response.getBody(), Map.class);
            } else {
                return buildErrorResponse("获取统计信息失败");
            }

        } catch (Exception e) {
            log.error("获取统计信息失败", e);
            return buildErrorResponse("获取统计信息失败: " + e.getMessage());
        }
    }

    /**
     * 分页获取训练数据
     *
     * @param dataset 数据集名称
     * @param limit 每页数量
     * @param offset 偏移量
     * @return 训练数据
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getTrainingData(String dataset, Integer limit, Integer offset) {
        try {
            log.info("获取训练数据: dataset={}, limit={}, offset={}", dataset, limit, offset);

            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("dataset", dataset);
            if (limit != null) {
                requestBody.put("limit", limit);
            }
            if (offset != null) {
                requestBody.put("offset", offset);
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> entity = new HttpEntity<>(
                    JSON.toJSONString(requestBody),
                    headers
            );

            String url = flaskApiUrl + "/api/training-data";
            ResponseEntity<String> response = restTemplate.postForEntity(
                    url,
                    entity,
                    String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                return JSON.parseObject(response.getBody(), Map.class);
            } else {
                return buildErrorResponse("获取训练数据失败");
            }

        } catch (Exception e) {
            log.error("获取训练数据失败", e);
            return buildErrorResponse("获取训练数据失败: " + e.getMessage());
        }
    }

    /**
     * 检查 Flask API 健康状态
     *
     * @return 健康检查结果
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> checkHealth() {
        try {
            log.info("检查 Flask API 健康状态");

            String url = flaskApiUrl + "/api/health";
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                return JSON.parseObject(response.getBody(), Map.class);
            } else {
                return buildErrorResponse("API 不可用");
            }

        } catch (Exception e) {
            log.error("健康检查失败", e);
            return buildErrorResponse("无法连接到 Flask API: " + e.getMessage());
        }
    }

    /**
     * 构建错误响应
     */
    private Map<String, Object> buildErrorResponse(String message) {
        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("status", "error");
        errorResponse.put("message", message);
        errorResponse.put("found", false);
        return errorResponse;
    }
}
