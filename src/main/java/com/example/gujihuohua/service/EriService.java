package com.example.gujihuohua.service;

import java.util.List;
import java.util.Map;

/**
 * 古籍事件关系识别服务接口
 */
public interface EriService {

    /**
     * 单个事件关系预测
     *
     * @param text 原句文本
     * @param headTrigger 头部触发词
     * @param tailTrigger 尾部触发词
     * @return 预测结果（包含关系类型和置信度）
     */
    Map<String, Object> predictSingle(String text, String headTrigger, String tailTrigger);

    /**
     * 批量事件关系预测
     *
     * @param samples 样本列表，每个样本包含 text, head_trigger, tail_trigger
     * @return 批量预测结果
     */
    Map<String, Object> predictBatch(List<Map<String, String>> samples);

    /**
     * 启动异步批量分析任务
     *
     * @param corpusId 语料库ID
     */
    void runBatchAnalysisAsync(Long corpusId);

    /**
     * 查询分析进度
     *
     * @param corpusId 语料库ID
     * @return 进度百分比
     */
    Integer getProgress(Long corpusId);

    /**
     * 获取分析结果（从内存）
     *
     * @param corpusId 语料库ID
     * @return 事件关系列表
     */
    List<Map<String, Object>> getResults(Long corpusId);
}
