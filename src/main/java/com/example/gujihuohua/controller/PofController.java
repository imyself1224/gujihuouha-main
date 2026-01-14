package com.example.gujihuohua.controller;

import com.alibaba.fastjson.JSONObject;
import com.example.gujihuohua.service.PofService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/analysis/pof")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
@Slf4j
public class PofController {

    private final PofService pofService;

    /**
     * 生成古籍人物画像
     * 接收前端输入的文本描述，生成人物画像
     *
     * @param request 包含 text 字段的请求体
     * @return 包含 imageUrl 和 caption 的响应
     */
    @PostMapping("/generate")
    public ResponseEntity<Map<String, Object>> generatePortrait(@RequestBody JSONObject request) {
        Map<String, Object> response = new HashMap<>();

        try {
            String text = request.getString("text");

            if (text == null || text.trim().isEmpty()) {
                response.put("error", "文本输入不能为空");
                return ResponseEntity.badRequest().body(response);
            }

            log.info("接收到人物描述文本: {}", text);

            // 调用服务层处理
            Map<String, Object> result = pofService.generatePortrait(text);

            response.putAll(result);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("生成人物画像失败", e);
            response.put("error", "生成失败: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }

    /**
     * 获取生成历史
     *
     * @return 人物画像生成历史列表
     */
    @GetMapping("/history")
    public ResponseEntity<Map<String, Object>> getHistory() {
        Map<String, Object> response = new HashMap<>();

        try {
            response.put("history", pofService.getHistory());
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("获取历史记录失败", e);
            response.put("error", "获取失败: " + e.getMessage());
            return ResponseEntity.internalServerError().body(response);
        }
    }
}
