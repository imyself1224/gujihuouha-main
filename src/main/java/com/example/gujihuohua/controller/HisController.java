package com.example.gujihuohua.controller;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * 综合分析控制器
 * 负责调度 Python AI 引擎进行高级分析 (因果画像、深度聚类等)
 */
@Slf4j
@RestController
@RequestMapping("/api/analysis")
@RequiredArgsConstructor
@CrossOrigin(origins = "*") // 允许跨域，方便本地开发调试
public class HisController {

    private final RestTemplate restTemplate;

    private static final String PYTHON_SERVICE_HOST = "http://localhost:5006";

    /**
     * 新增：代理下载接口，解决跨域及文件强制下载问题
     */
    @GetMapping("/proxy/download")
    @SuppressWarnings("null")
    public ResponseEntity<?> proxyDownload(@RequestParam String url) {
        try {
            log.info("[数据代理] 正在下载外部资源: {}", url);
            byte[] fileBytes = restTemplate.getForObject(url, byte[].class);
            if (fileBytes == null) return ResponseEntity.notFound().build();

            String fileName = url.substring(url.lastIndexOf("/") + 1);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(url.endsWith(".csv") ? MediaType.parseMediaType("text/csv") : MediaType.IMAGE_PNG);
            headers.setContentDispositionFormData("attachment", fileName);
            
            return ResponseEntity.ok()
                    .headers(headers)
                    .body(fileBytes);
        } catch (Exception e) {
            log.error("[数据代理] 下载失败: {}", e.getMessage());
            return ResponseEntity.internalServerError().body("下载失败: " + e.getMessage());
        }
    }

    /**
     * 新增：预览代理，用于在新窗口展示图片
     */
    @GetMapping("/proxy/view")
    @SuppressWarnings("null")
    public ResponseEntity<?> proxyView(@RequestParam String url) {
        try {
            log.info("[资源预览] 正在获取图片资源: {}", url);
            byte[] fileBytes = restTemplate.getForObject(url, byte[].class);
            if (fileBytes == null) return ResponseEntity.notFound().build();

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.IMAGE_PNG);
            // 不设置 attachment，让浏览器尝试渲染
            return ResponseEntity.ok()
                    .headers(headers)
                    .body(fileBytes);
        } catch (Exception e) {
            log.error("[资源预览] 获取失败: {}", e.getMessage());
            return ResponseEntity.internalServerError().body("预览失败");
        }
    }

    /**
     * 【核心功能】生成因果画像
     * <p>
     * 流程：前端调用 -> Java 转发 -> Python (读取本地 output/causal_relations.json) -> 返回分析结果
     */
    @PostMapping("/causal/portrait")
    public ResponseEntity<?> generateCausalPortrait() {
        // 1. 拼接 Python 接口地址 (对应 Python 代码中的 @app.route)
        String targetUrl = PYTHON_SERVICE_HOST + "/analysis/causal/portrait";

        log.info("正在调用因果分析引擎: {}", targetUrl);

        try {
            // 2. 设置请求头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            // 3. 构造请求体
            // 注意：因为 Python 端已经修改为直接读取服务器本地的 JSON 文件，
            // 所以这里不需要传任何实际数据，传一个空对象 "{}" 占位即可防止 400 错误。
            HttpEntity<String> requestEntity = new HttpEntity<>("{}", headers);

            // 4. 发起远程调用
            String responseBody = restTemplate.postForObject(targetUrl, requestEntity, String.class);

            // 5. 解析并返回结果
            if (responseBody == null) {
                return ResponseEntity.status(500).body(createErrorResponse(500, "AI 服务返回为空"));
            }

            JSONObject jsonResult = JSON.parseObject(responseBody);

            // 检查 Python 端返回的状态码
            if (jsonResult.containsKey("code") && jsonResult.getInteger("code") != 200) {
                return ResponseEntity.status(500).body(jsonResult);
            }

            return ResponseEntity.ok(jsonResult);

        } catch (ResourceAccessException e) {
            log.error("连接 Python 服务失败", e);
            return ResponseEntity.status(503).body(createErrorResponse(503, "连接分析引擎失败，请确认 Python 服务已启动 (端口 5006)"));
        } catch (Exception e) {
            log.error("调用因果分析接口异常", e);
            return ResponseEntity.status(500).body(createErrorResponse(500, "服务端处理异常: " + e.getMessage()));
        }
    }

    /**
     * 辅助方法：构建统一的错误返回格式
     */
    private Map<String, Object> createErrorResponse(int code, String msg) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", code);
        map.put("msg", msg);
        map.put("data", null);
        return map;
    }

    // 新增：事件类型画像接口
    @PostMapping("/event/type")
    public ResponseEntity<?> generateTypePortrait() {
        return forwardToPython("/analysis/event/type");
    }

    // 新增：地点空间画像接口
    @PostMapping("/event/location")
    public ResponseEntity<?> generateLocationPortrait() {
        return forwardToPython("/analysis/event/location");
    }

    // 新增：时间演化画像接口
    @PostMapping("/event/time")
    public ResponseEntity<?> generateTimePortrait() {
        return forwardToPython("/analysis/event/time");
    }

    // 通用转发辅助方法
    private ResponseEntity<?> forwardToPython(String path) {
        String pythonUrl = "http://localhost:5006" + path;
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<String> request = new HttpEntity<>("{}", headers);
            String response = restTemplate.postForObject(pythonUrl, request, String.class);
            return ResponseEntity.ok(JSON.parseObject(response));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("AI服务不可用: " + e.getMessage());
        }
    }
}