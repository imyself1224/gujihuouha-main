package com.example.gujihuohua.service.pof_impl;

import com.alibaba.fastjson.JSONObject;
import com.example.gujihuohua.service.PofService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * 古籍人物画像服务实现
 * 功能：将数据传入端口 5001，获取返回数据并转发到端口 5002
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class PofServiceImpl implements PofService {

    // RestTemplate 用于调用 5001 端口的外部服务
    private final RestTemplate restTemplate;

    // 简单的内存存储（实际项目可替换为数据库）
    private static final List<Map<String, Object>> history = Collections.synchronizedList(new ArrayList<>());

    // 外部服务地址
    private static final String EXTERNAL_SERVICE_URL = "http://localhost:5001";

    @Override
    public Map<String, Object> generatePortrait(String text) {
        Map<String, Object> result = new HashMap<>();

        try {
            // 确保文本为 UTF-8 编码
            text = new String(text.getBytes(StandardCharsets.UTF_8), StandardCharsets.UTF_8);

            // 1. 准备请求数据
            JSONObject requestData = new JSONObject();
            requestData.put("text", text);

            // 2. 调用端口 5001 的外部服务（获取实体识别结果）
            Map<String, Object> externalResult = callExternalService(requestData.toJSONString());

            // 3. 将 5001 的结果转发到端口 5002 并获取返回结果
            Map<String, Object> port5002Result = sendToPort5002(text, externalResult);

            // 4. 组织返回结果
            result.put("status", "success");
            result.put("entities", externalResult.get("entities"));
            result.put("port5002Response", port5002Result);

            // 5. 记录到历史
            Map<String, Object> record = new HashMap<>();
            record.put("timestamp", System.currentTimeMillis());
            record.put("text", text);
            record.put("entities", externalResult.get("entities"));
            record.put("externalResponse", externalResult);
            record.put("port5002Result", port5002Result);
            history.add(record);

            return result;

        } catch (Exception e) {
            log.error("处理文本异常", e);
            // 降级处理：如果 5001 服务不可用，使用本地处理
            log.warn("端口 5001 服务调用失败");
            return generateLocalPortrait(text);
        }
    }

    @Override
    public List<Map<String, Object>> getHistory() {
        return new ArrayList<>(history);
    }

    /**
     * 调用端口 5001 的外部服务（古文命名实体识别）
     * 将文本传入端口 5001，获取识别结果
     *
     * @param requestData 请求数据的 JSON 字符串
     * @return 外部服务返回的结果
     */
    @SuppressWarnings("null")
    private Map<String, Object> callExternalService(String requestData) {
        Map<String, Object> result = new HashMap<>();

        try {
            // 准备 HTTP 请求头
            HttpHeaders headers = new HttpHeaders();
            // 设置 UTF-8 字符编码
            headers.setContentType(new MediaType("application", "json", StandardCharsets.UTF_8));

            // 创建 HTTP 请求体
            HttpEntity<String> request = new HttpEntity<>(requestData, headers);

            // 发送 POST 请求到端口 5001
            ResponseEntity<String> response = restTemplate.postForEntity(
                    EXTERNAL_SERVICE_URL + "/predict",
                    request,
                    String.class
            );

            // 解析响应数据
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                JSONObject responseJson = JSONObject.parseObject(response.getBody());

                // 提取并返回关键数据
                result.put("code", responseJson.getInteger("code"));
                result.put("msg", responseJson.getString("msg"));
                
                if (responseJson.containsKey("data")) {
                    JSONObject data = responseJson.getJSONObject("data");
                    result.put("text", data.getString("text"));
                    if (data.containsKey("entities")) {
                        result.put("entities", data.getJSONObject("entities"));
                    }
                }

                return result;
            } else {
                log.warn("✗ 端口 5001 返回非 2xx 状态码: {}", response.getStatusCode());
                throw new RuntimeException("外部服务返回失败状态: " + response.getStatusCode());
            }

        } catch (Exception e) {
            log.error("【错误】调用端口 5001 失败: {}", e.getMessage());
            log.error("【错误详情】", e);

            result.put("code", -1);
            result.put("msg", "error");
            result.put("error", e.getMessage());
            throw new RuntimeException("调用外部服务失败: " + e.getMessage(), e);
        }
    }

    /**
     * 本地处理文本（降级方案）
     * 当端口 5001 服务不可用时使用此方案
     *
     * @param text 文本
     * @return 本地处理的结果
     */
    private Map<String, Object> generateLocalPortrait(String text) {
        Map<String, Object> result = new HashMap<>();

        log.info("使用本地处理方案处理: {}", text);

        // 本地简单的关键词提取
        Map<String, String> entities = extractLocalEntities(text);
        
        result.put("status", "local");
        result.put("entities", entities);

        log.info("本地处理完成，识别结果: {}", entities);

        return result;
    }

    /**
     * 本地关键词提取（简单示例）
     *
     * @param text 文本
     * @return 提取的实体
     */
    private Map<String, String> extractLocalEntities(String text) {
        Map<String, String> entities = new HashMap<>();
        
        // 简单的关键词识别
        if (text.contains("高祖")) {
            entities.put("PERSON", "高祖");
        }
        if (text.contains("洛阳")) {
            entities.put("LOC", "洛阳");
        }
        if (text.contains("长安")) {
            entities.put("LOC", "长安");
        }
        
        return entities;
    }

    /**
     * 将 5001 端口的识别结果转发到端口 5002 进行人物画像分析
     * 5001 返回的是实体识别结果，5002 用于进一步的语义相似度分析
     *
     * @param originalText 原始输入文本
     * @param externalResult 5001 端口返回的识别结果
     * @return 5002 端口返回的分析结果
     */
    @SuppressWarnings("null")
    private Map<String, Object> sendToPort5002(String originalText, Map<String, Object> externalResult) {
        Map<String, Object> responseData = new HashMap<>();
        
        try {
            // 准备 HTTP 请求头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(new MediaType("application", "json", StandardCharsets.UTF_8));

            // 构造符合5002接口期望的请求数据，包含5001的完整识别结果
            JSONObject requestPayload = new JSONObject();
            requestPayload.put("text", originalText);
            
            // 将5001的识别结果（实体）添加到请求中
            if (externalResult.containsKey("entities")) {
                requestPayload.put("entities", externalResult.get("entities"));
            }
            
            // 可选：添加人物别名映射
            JSONObject personAliases = new JSONObject();
            requestPayload.put("person_aliases", personAliases);
            
            String jsonData = requestPayload.toJSONString();
            
            // 创建 HTTP 请求体
            HttpEntity<String> request = new HttpEntity<>(jsonData, headers);

            // 发送 POST 请求到端口 5002 的 /analyze 接口
            ResponseEntity<String> response = restTemplate.postForEntity(
                    "http://localhost:5002/analyze",
                    request,
                    String.class
            );

            if (response.getStatusCode().is2xxSuccessful()) {
                // 获取5002端口返回的响应
                String responseBody = response.getBody();
                if (responseBody != null) {
                    // 正确处理UTF-8编码（响应体已是字符串，需要正确解析）
                    JSONObject parsedResponse = JSONObject.parseObject(responseBody);
                    responseData = parsedResponse;
                }
                log.info("✓ 成功转发数据到端口 5002，已接收返回结果");
            } else {
                log.warn("✗ 端口 5002 返回非 2xx 状态码: {}", response.getStatusCode());
                responseData.put("error", "5002 返回非 2xx 状态码: " + response.getStatusCode());
            }
        } catch (Exception e) {
            log.warn("转发到端口 5002 失败: {}", e.getMessage());
            log.debug("转发错误详情", e);
            responseData.put("error", e.getMessage());
        }
        
        return responseData;
    }
}

