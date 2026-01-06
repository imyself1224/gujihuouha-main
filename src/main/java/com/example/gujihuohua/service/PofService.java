package com.example.gujihuohua.service;

import java.util.List;
import java.util.Map;

/**
 * 古籍人物画像服务接口
 */
public interface PofService {

    /**
     * 生成人物画像及分析结果
     *
     * @param text 古籍人物描述文本
     * @return 包含分析结果的 Map
     */
    Map<String, Object> generatePortrait(String text);

    /**
     * 获取生成历史
     *
     * @return 历史记录列表
     */
    List<Map<String, Object>> getHistory();
}
