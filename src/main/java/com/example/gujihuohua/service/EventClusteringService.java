package com.example.gujihuohua.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.example.gujihuohua.entity.ClusteringHistory;
import com.example.gujihuohua.repository.ClusteringHistoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.http.HttpEntity;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.mime.MultipartEntityBuilder;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * 事件时空聚类服务
 * 调用 Flask 端口 5005 的聚类分析服务
 * 支持数据保存到本地文件系统及分析历史记录存储到数据库
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class EventClusteringService {
    private static final String CLUSTERING_SERVICE_URL = "http://localhost:5005";
    private static final String CLUSTER_API_PATH = "/api/cluster/file";
    private static final String CLUSTER_STORAGE_DIR = "cluster-storage";
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    private final ClusteringHistoryRepository clusteringHistoryRepository;
    
    @Value("${app.storage.root-path:./data-storage}")
    private String storageRootPath;

    /**
     * 执行事件聚类分析并保存数据到本地文件系统
     *
     * @param locationData CSV格式的地名数据，字段: 古代地名,现代地名,纬度,经度
     * @param eventsData   JSON格式的事件数据（JSON数组），结构: [{"id": "1", "year": 220, "location": "长安", "description": "..."}]
     * @param locationFileName 地点文件名
     * @param eventsFileName   事件文件名
     * @return 聚类分析结果
     */
    public Map<String, Object> performClusteringWithHistory(String locationData, String eventsData, 
                                                             String locationFileName, String eventsFileName) {
        Map<String, Object> result = new HashMap<>();
        long startTime = System.currentTimeMillis();

        try {
            log.info("========== 开始执行事件聚类分析 ==========");
            log.info("存储根路径: {}", storageRootPath);
            log.info("分析ID: {}", "即将生成");

            // 生成唯一的分析ID
            String analysisId = generateAnalysisId();
            log.info("生成的分析ID: {}", analysisId);

            // 保存地点数据到本地文件系统
            String locationFilePath = saveLocationDataToFile(locationData, locationFileName, analysisId);
            log.info("✓ 地点数据已保存到: {}", locationFilePath);

            // 保存事件数据到本地文件系统
            String eventsFilePath = saveEventDataToFile(eventsData, eventsFileName, analysisId);
            log.info("✓ 事件数据已保存到: {}", eventsFilePath);

            // 调用 Flask 聚类服务
            log.info("开始调用Flask聚类服务...");
            Map<String, Object> clusteringResult = callFlaskClusteringService(locationData, eventsData);

            long endTime = System.currentTimeMillis();
            long timeCost = endTime - startTime;
            log.info("聚类分析耗时: {}ms", timeCost);

            // 创建历史记录
            ClusteringHistory history = new ClusteringHistory();
            history.setAnalysisId(analysisId);
            history.setLocationFileName(locationFileName);
            history.setLocationFilePath(locationFilePath);
            history.setEventsFileName(eventsFileName);
            history.setEventsFilePath(eventsFilePath);
            history.setAnalysisTimeCost(timeCost);

            if ("success".equals(clusteringResult.get("status"))) {
                result.put("status", "success");
                result.put("message", clusteringResult.get("message"));
                result.put("data", clusteringResult.get("data"));
                result.put("analysisId", analysisId);
                
                // 在返回结果中也包含文件路径，便于客户端调试
                result.put("locationFilePath", locationFilePath);
                result.put("eventsFilePath", eventsFilePath);

                // 提取聚类结果统计信息
                JSONObject data = (JSONObject) clusteringResult.get("data");
                if (data != null) {
                    JSONArray clusters = data.getJSONArray("clusters");
                    if (clusters != null) {
                        history.setNumClusters(clusters.size());
                        // 统计事件总数和噪声点数
                        int totalEvents = 0;
                        int noiseCount = 0;
                        for (int i = 0; i < clusters.size(); i++) {
                            JSONObject cluster = clusters.getJSONObject(i);
                            if (cluster.getInteger("cluster_id") == -1) {
                                // 噪声点簇
                                JSONArray events = cluster.getJSONArray("events");
                                if (events != null) {
                                    noiseCount = events.size();
                                }
                            } else {
                                JSONArray events = cluster.getJSONArray("events");
                                if (events != null) {
                                    totalEvents += events.size();
                                }
                            }
                        }
                        history.setNumEvents(totalEvents);
                        history.setNumNoise(noiseCount);
                        
                        log.info("========== 聚类分析完成 ==========");
                        log.info("分析结果: {} 个事件, {} 个聚类, {} 个噪声点", totalEvents, 
                                history.getNumClusters(), noiseCount);
                    }
                }
            } else {
                result.put("status", "error");
                result.put("message", clusteringResult.get("message"));
                result.put("error", clusteringResult.get("error"));
                result.put("analysisId", analysisId);
                
                // 在返回结果中也包含文件路径，便于调试错误
                result.put("locationFilePath", locationFilePath);
                result.put("eventsFilePath", eventsFilePath);

                history.setAnalysisStatus("error");
                history.setErrorMessage((String) clusteringResult.get("error"));
                log.error("聚类分析失败: {}", clusteringResult.get("error"));
            }

            // 保存历史记录到数据库
            try {
                clusteringHistoryRepository.save(history);
                log.info("✓ 聚类分析历史记录已保存到数据库: {}", analysisId);
            } catch (Exception e) {
                log.error("保存聚类分析历史记录失败", e);
            }

            return result;

        } catch (Exception e) {
            log.error("执行聚类分析异常", e);
            result.put("status", "error");
            result.put("message", "执行聚类分析异常");
            result.put("error", e.getMessage());
            return result;
        }
    }

    /**
     * 执行事件聚类分析（保持向后兼容）
     *
     * @param locationData CSV格式的地名数据，字段: 古代地名,现代地名,纬度,经度
     * @param eventsData   JSON格式的事件数据（JSON数组），结构: [{"id": "1", "year": 220, "location": "长安", "description": "..."}]
     * @return 聚类分析结果
     */
    public Map<String, Object> performClustering(String locationData, String eventsData) {
        return performClusteringWithHistory(locationData, eventsData, "locations.csv", "events.json");
    }

    /**
     * 根据历史文件重新运行聚类分析
     *
     * @param locationFilePath 地点数据文件路径
     * @param eventsFilePath   事件数据文件路径
     * @param locationFileName 地点文件原始名称
     * @param eventsFileName   事件文件原始名称
     * @return 聚类分析结果
     */
    public Map<String, Object> rerunClusteringAnalysis(String locationFilePath, String eventsFilePath,
                                                        String locationFileName, String eventsFileName) {
        Map<String, Object> result = new HashMap<>();

        try {
            log.info("重新运行聚类分析: locationFilePath={}, eventsFilePath={}", locationFilePath, eventsFilePath);

            // 读取地点数据文件
            String locationData = new String(Files.readAllBytes(Paths.get(locationFilePath)), StandardCharsets.UTF_8);
            
            // 读取事件数据文件
            String eventsData = new String(Files.readAllBytes(Paths.get(eventsFilePath)), StandardCharsets.UTF_8);

            // 验证数据格式
            if (!validateLocationData(locationData)) {
                result.put("status", "error");
                result.put("message", "地点数据格式无效");
                return result;
            }

            if (!validateEventsData(eventsData)) {
                result.put("status", "error");
                result.put("message", "事件数据格式无效");
                return result;
            }

            // 调用聚类分析，使用新的文件名以区分不同的运行
            return performClusteringWithHistory(locationData, eventsData, locationFileName, eventsFileName);

        } catch (Exception e) {
            log.error("重新运行聚类分析失败", e);
            result.put("status", "error");
            result.put("message", "重新运行聚类分析失败: " + e.getMessage());
            return result;
        }
    }

    /**
     * 删除聚类分析历史记录
     *
     * @param analysisId 分析ID
     * @return 删除是否成功
     */
    @SuppressWarnings("null")
    public boolean deleteAnalysisHistory(String analysisId) {
        try {
            // 1. 查找数据库记录
            Optional<ClusteringHistory> historyOpt = clusteringHistoryRepository.findByAnalysisId(analysisId);
            
            // 2. 删除关联文件 (基于 ID 扫描所有可能的日期文件夹)
            Path clusterStoragePath = Paths.get(storageRootPath).resolve(CLUSTER_STORAGE_DIR);
            
            // 记录受影响的日期目录路径，以便后续检查是否为空
            Set<Path> dateDirsToCheck = new HashSet<>();

            if (Files.exists(clusterStoragePath)) {
                // 遍历存储目录下的所有日期文件夹
                try (Stream<Path> pathStream = Files.walk(clusterStoragePath, 2)) {
                    pathStream.filter(Files::isRegularFile)
                        .forEach(path -> {
                            String fileName = path.getFileName().toString();
                            // 直接匹配 {analysisId}.json 或 {analysisId}.csv
                            if (fileName.equals(analysisId + ".json") || fileName.equals(analysisId + ".csv") || 
                                fileName.startsWith(analysisId + "_")) { // 兼容旧命名
                                try {
                                    Path parentDir = path.getParent();
                                    Files.delete(path);
                                    log.info("已删除文件: {}", path);
                                    if (parentDir != null) {
                                        dateDirsToCheck.add(parentDir);
                                    }
                                } catch (IOException e) {
                                    log.error("删除文件失败: {}", path, e);
                                }
                            }
                        });
                }
                
                // 检查并删除空的日期目录
                for (Path dateDir : dateDirsToCheck) {
                    try {
                        if (Files.exists(dateDir) && Files.isDirectory(dateDir)) {
                            // 检查目录是否为空
                            try (Stream<Path> entries = Files.list(dateDir)) {
                                if (!entries.findAny().isPresent()) {
                                    Files.delete(dateDir);
                                    log.info("已删除空日期文件夹: {}", dateDir);
                                }
                            }
                        }
                    } catch (IOException e) {
                        log.warn("检查或删除空日期目录失败: {}", dateDir, e);
                    }
                }
            }

            // 3. 删除数据库记录
            historyOpt.ifPresent(clusteringHistory -> {
                clusteringHistoryRepository.delete(clusteringHistory);
                log.info("成功删除聚类分析历史记录: {}", analysisId);
            });
            
            return true;

        } catch (Exception e) {
            log.error("删除聚类分析历史记录异常", e);
            return false;
        }
    }

    /**
     * 调用 Flask 聚类服务
     *
     * @param locationData CSV地名数据
     * @param eventsData   JSON事件数据
     * @return Flask服务的响应
     */
    private Map<String, Object> callFlaskClusteringService(String locationData, String eventsData) 
            throws Exception {
        
        Map<String, Object> response = new HashMap<>();
        CloseableHttpClient httpClient = HttpClients.createDefault();

        try {
            String url = CLUSTERING_SERVICE_URL + CLUSTER_API_PATH;
            log.info("调用 Flask 聚类服务: {}", url);
            log.debug("地名数据长度: {}, 事件数据长度: {}", locationData.length(), eventsData.length());

            HttpPost httpPost = new HttpPost(url);

            // 构建 multipart/form-data 请求
            MultipartEntityBuilder builder = MultipartEntityBuilder.create();
            builder.setCharset(StandardCharsets.UTF_8);
            
            // 添加 CSV 地名数据作为文件（使用UTF-8编码）
            builder.addBinaryBody("location_file", 
                    locationData.getBytes(StandardCharsets.UTF_8),
                    org.apache.http.entity.ContentType.create("text/plain", StandardCharsets.UTF_8),
                    "locations.csv");
            
            // 添加 JSON 事件数据作为文件（使用UTF-8编码）
            builder.addBinaryBody("events_file", 
                    eventsData.getBytes(StandardCharsets.UTF_8),
                    org.apache.http.entity.ContentType.create("application/json", StandardCharsets.UTF_8),
                    "events.json");

            httpPost.setEntity(builder.build());

            // 发送请求
            CloseableHttpResponse httpResponse = httpClient.execute(httpPost);
            HttpEntity entity = httpResponse.getEntity();

            if (entity != null) {
                String responseStr = EntityUtils.toString(entity, StandardCharsets.UTF_8);
                log.info("Flask 聚类服务响应: {}", responseStr);

                // 解析响应
                JSONObject responseJson = JSON.parseObject(responseStr);
                response.put("status", responseJson.getString("status"));
                response.put("message", responseJson.getString("message"));
                response.put("data", responseJson.getJSONObject("data"));
            }

            httpResponse.close();

        } catch (Exception e) {
            log.error("调用 Flask 聚类服务异常", e);
            response.put("status", "error");
            response.put("message", "调用 Flask 聚类服务异常");
            response.put("error", e.getMessage());

        } finally {
            try {
                httpClient.close();
            } catch (Exception e) {
                log.error("关闭 HttpClient 异常", e);
            }
        }

        return response;
    }

    /**
     * 验证地名数据格式
     *
     * @param locationData CSV格式的地名数据
     * @return 是否有效
     */
    public boolean validateLocationData(String locationData) {
        try {
            if (locationData == null || locationData.trim().isEmpty()) {
                return false;
            }

            String[] lines = locationData.split("\n");
            if (lines.length < 2) {
                return false;
            }

            // 检查表头
            String header = lines[0].trim();
            if (!header.contains("古代地名") && !header.contains("纬度") && !header.contains("经度")) {
                // 如果没有中文标题，至少需要有数据行
                return lines.length > 1;
            }

            // 至少有一条数据
            return lines.length > 1;

        } catch (Exception e) {
            log.error("验证地名数据异常", e);
            return false;
        }
    }

    /**
     * 验证事件数据格式
     * JSON数组格式: [{"id": "HGZ-256", "description": "...", "year": -256, "location": "沛丰邑"}]
     *
     * @param eventsData JSON格式的事件数据
     * @return 是否有效
     */
    public boolean validateEventsData(String eventsData) {
        try {
            if (eventsData == null || eventsData.trim().isEmpty()) {
                return false;
            }

            JSONArray events = null;
            
            // 解析为JSON数组
            if (eventsData.trim().startsWith("[")) {
                events = JSON.parseArray(eventsData);
            } else {
                log.warn("事件数据应为JSON数组格式");
                return false;
            }

            if (events == null || events.size() == 0) {
                return false;
            }

            // 验证每个事件的必要字段: id, year, location, description
            for (int i = 0; i < events.size(); i++) {
                JSONObject event = events.getJSONObject(i);
                if (event.getString("id") == null || 
                    event.getInteger("year") == null || 
                    event.getString("location") == null ||
                    event.getString("description") == null) {
                    return false;
                }
            }

            return true;

        } catch (Exception e) {
            log.error("验证事件数据异常", e);
            return false;
        }
    }

    /**
     * 保存事件数据到本地文件系统
     *
     * @param eventsData JSON格式的事件数据
     * @param fileName   原始文件名
     * @param analysisId 分析ID
     * @return 保存的文件路径
     * @throws IOException 如果文件操作失败
     */
    private String saveEventDataToFile(String eventsData, String fileName, String analysisId) throws IOException {
        try {
            LocalDate today = LocalDate.now();
            String dateStr = today.format(DATE_FORMATTER);
            
            // 确保根路径存在
            Path clusterStoragePath = Paths.get(storageRootPath).resolve(CLUSTER_STORAGE_DIR);
            
            Path dateDir = clusterStoragePath.resolve(dateStr);
            if (!Files.exists(dateDir)) {
                Files.createDirectories(dateDir);
            }

            // 文件名就是生成的唯一id (analysisId).json
            // 通过后缀 .json 区分这是事件数据
            String fileNameWithId = analysisId + ".json";
            
            Path filePath = dateDir.resolve(fileNameWithId);

            // 保存文件
            Files.write(filePath, eventsData.getBytes(StandardCharsets.UTF_8));
            log.info("事件数据已保存: {}", filePath);

            return filePath.toString();
        } catch (IOException e) {
            log.error("保存事件数据文件异常", e);
            throw e;
        }
    }

    /**
     * 保存地点数据到本地文件系统
     *
     * @param locationData CSV格式的地点数据
     * @param fileName     原始文件名
     * @param analysisId   分析ID
     * @return 保存的文件路径
     * @throws IOException 如果文件操作失败
     */
    private String saveLocationDataToFile(String locationData, String fileName, String analysisId) throws IOException {
        try {
            LocalDate today = LocalDate.now();
            String dateStr = today.format(DATE_FORMATTER);
            
            // 确保根路径存在
            Path clusterStoragePath = Paths.get(storageRootPath).resolve(CLUSTER_STORAGE_DIR);
            
            Path dateDir = clusterStoragePath.resolve(dateStr);
            if (!Files.exists(dateDir)) {
                Files.createDirectories(dateDir);
            }

            // 文件名就是生成的唯一id (analysisId).csv
            // 通过后缀 .csv 区分这是地点数据
            String fileNameWithId = analysisId + ".csv";
            
            Path filePath = dateDir.resolve(fileNameWithId);

            // 保存文件
            Files.write(filePath, locationData.getBytes(StandardCharsets.UTF_8));
            log.info("地点数据已保存: {}", filePath);

            return filePath.toString();
        } catch (IOException e) {
            log.error("保存地点数据文件异常", e);
            throw e;
        }
    }

    /**
     * 生成唯一的分析ID
     *
     * @return 分析ID
     */
    private String generateAnalysisId() {
        return "CLUSTER_" + System.currentTimeMillis() + "_" + UUID.randomUUID().toString().substring(0, 8);
    }

    /**
     * 获取所有存在的分析日期列表
     * 
     * @return 日期列表，按倒序排列（最新优先）
     */
    public List<String> getAnalysisDates() {
        List<String> dates = new ArrayList<>();
        
        try {
            Path clusterStoragePath = Paths.get(storageRootPath).resolve(CLUSTER_STORAGE_DIR);
            
            if (!Files.exists(clusterStoragePath)) {
                log.warn("聚类存储目录不存在: {}", clusterStoragePath);
                return dates;
            }

            Files.list(clusterStoragePath)
                    .filter(Files::isDirectory)
                    .map(path -> path.getFileName().toString())
                    .sorted((a, b) -> b.compareTo(a)) // 倒序排列
                    .forEach(dates::add);
                    
        } catch (Exception e) {
            log.error("获取分析日期列表失败", e);
        }
        
        return dates;
    }

    /**
     * 获取指定日期的所有聚类分析记录
     * 直接扫描文件夹下的文件，查找匹配的 JSON 和 CSV
     *
     * @param dateStr 日期字符串 (格式: yyyy-MM-dd)
     * @return 该日期下的记录列表
     */
    public List<Map<String, Object>> getRecordsByDate(String dateStr) {
        List<Map<String, Object>> records = new ArrayList<>();
        try {
            Path dateDir = Paths.get(storageRootPath, CLUSTER_STORAGE_DIR, dateStr);
            if (!Files.exists(dateDir) || !Files.isDirectory(dateDir)) {
                return records;
            }

            // 获取所有文件
            List<Path> files = Files.list(dateDir).collect(Collectors.toList());
            
            // 提取唯一ID
            Set<String> analysisIds = new HashSet<>();
            for (Path file : files) {
                String fileName = file.getFileName().toString();
                String analysisId = null;
                
                if (fileName.endsWith(".json")) {
                    if (fileName.endsWith("_events.json")) {
                        analysisId = fileName.substring(0, fileName.lastIndexOf("_events.json"));
                    } else {
                        analysisId = fileName.substring(0, fileName.lastIndexOf(".json"));
                    }
                } else if (fileName.endsWith(".csv")) {
                    if (fileName.endsWith("_locations.csv")) {
                        analysisId = fileName.substring(0, fileName.lastIndexOf("_locations.csv"));
                    } else {
                        analysisId = fileName.substring(0, fileName.lastIndexOf(".csv"));
                    }
                }
                
                if (analysisId != null && !analysisId.equals("hash_mapping")) {
                    analysisIds.add(analysisId);
                }
            }

            // 构建记录
            for (String id : analysisIds) {
                Map<String, Object> record = new HashMap<>();
                record.put("analysisId", id);
                record.put("createTime", dateStr); // 粗略时间
                
                // 查找文件路径 (优先匹配新格式，兼容旧格式)
                String eventsFile = id + ".json";
                String oldEventsFile = id + "_events.json";
                
                String locationsFile = id + ".csv";
                String oldLocationsFile = id + "_locations.csv";
                
                // Check Events File
                if (Files.exists(dateDir.resolve(eventsFile))) {
                    record.put("eventsFileName", eventsFile);
                    record.put("eventsFilePath", dateDir.resolve(eventsFile).toString());
                } else if (Files.exists(dateDir.resolve(oldEventsFile))) {
                    record.put("eventsFileName", oldEventsFile);
                    record.put("eventsFilePath", dateDir.resolve(oldEventsFile).toString());
                }
                
                // Check Locations File
                if (Files.exists(dateDir.resolve(locationsFile))) {
                    record.put("locationFileName", locationsFile);
                    record.put("locationFilePath", dateDir.resolve(locationsFile).toString());
                } else if (Files.exists(dateDir.resolve(oldLocationsFile))) {
                    record.put("locationFileName", oldLocationsFile);
                    record.put("locationFilePath", dateDir.resolve(oldLocationsFile).toString());
                }

                // 尝试从数据库补充详细信息
                Optional<ClusteringHistory> dbInfo = clusteringHistoryRepository.findByAnalysisId(id);
                if (dbInfo.isPresent()) {
                    record.put("numEvents", dbInfo.get().getNumEvents());
                    record.put("numClusters", dbInfo.get().getNumClusters());
                    record.put("status", dbInfo.get().getAnalysisStatus());
                }

                records.add(record);
            }
            
            // 按ID倒序
            records.sort((a, b) -> ((String)b.get("analysisId")).compareTo((String)a.get("analysisId")));

        } catch (Exception e) {
            log.error("扫描日期目录异常", e);
        }
        return records;
    }

    /**
     * 获取按日期分组的聚类分析历史记录
     * 直接扫描文件系统，不依赖数据库，实现"历史记录直接看对应文件夹下有哪些文件"
     *
     * @return 按日期组织的历史记录Map (日期 -> 记录列表)
     */
    public Map<String, List<ClusteringHistory>> getClusteringHistoryGroupedByDate() {
        Map<String, List<ClusteringHistory>> historyByDate = new LinkedHashMap<>();
        
        try {
            Path clusterStoragePath = Paths.get(storageRootPath).resolve(CLUSTER_STORAGE_DIR);
            
            if (!Files.exists(clusterStoragePath)) {
                return historyByDate;
            }

            // 获取所有日期文件夹
            List<Path> dateDirs = Files.list(clusterStoragePath)
                .filter(Files::isDirectory)
                .sorted((a, b) -> b.getFileName().compareTo(a.getFileName())) // 倒序
                .collect(Collectors.toList());

            for (Path dateDir : dateDirs) {
                String dateStr = dateDir.getFileName().toString();
                Map<String, ClusteringHistory> historiesInDate = new HashMap<>();

                // 遍历文件
                List<Path> files = Files.list(dateDir).collect(Collectors.toList());
                for (Path file : files) {
                    String fileName = file.getFileName().toString();
                    
                    // 匹配 {analysisId}.json 或 {analysisId}.csv
                    // 同时也兼容旧的 {analysisId}_events.json 格式（虽然新上传不再使用）
                    String analysisId = null;
                    if (fileName.endsWith(".json")) {
                        if (fileName.endsWith("_events.json")) {
                            analysisId = fileName.substring(0, fileName.lastIndexOf("_events.json"));
                        } else {
                            analysisId = fileName.substring(0, fileName.lastIndexOf(".json"));
                        }
                    } else if (fileName.endsWith(".csv")) {
                        if (fileName.endsWith("_locations.csv")) {
                            analysisId = fileName.substring(0, fileName.lastIndexOf("_locations.csv"));
                        } else {
                            analysisId = fileName.substring(0, fileName.lastIndexOf(".csv"));
                        }
                    }

                    if (analysisId != null && !analysisId.equals("hash_mapping")) { // 排除hash_mapping.json
                        ClusteringHistory history = historiesInDate.computeIfAbsent(analysisId, k -> {
                            ClusteringHistory h = new ClusteringHistory();
                            h.setAnalysisId(k);
                            h.setCreateTime(LocalDateTime.now()); // 占位
                            h.setAnalysisStatus("success");
                            return h;
                        });

                        if (fileName.endsWith(".json")) {
                            history.setEventsFileName(fileName);
                            history.setEventsFilePath(file.toString());
                        } else if (fileName.endsWith(".csv")) {
                            history.setLocationFileName(fileName);
                            history.setLocationFilePath(file.toString());
                        }
                    }
                }
                
                // 将配对好的记录加入列表
                if (!historiesInDate.isEmpty()) {
                    List<ClusteringHistory> list = historiesInDate.values().stream()
                        // 简单过滤：至少要有一个文件，并且排除非分析的杂文件
                        .filter(h -> h.getLocationFilePath() != null || h.getEventsFilePath() != null)
                        .collect(Collectors.toList());
                    
                    // 尝试从数据库补充元数据
                    for (ClusteringHistory h : list) {
                        try {
                            Optional<ClusteringHistory> dbRecord = clusteringHistoryRepository.findByAnalysisId(h.getAnalysisId());
                            if (dbRecord.isPresent()) {
                                ClusteringHistory db = dbRecord.get();
                                h.setNumEvents(db.getNumEvents());
                                h.setNumClusters(db.getNumClusters());
                                h.setNumNoise(db.getNumNoise());
                                h.setCreateTime(db.getCreateTime());
                                h.setErrorMessage(db.getErrorMessage());
                                if (db.getAnalysisStatus() != null) {
                                    h.setAnalysisStatus(db.getAnalysisStatus());
                                }
                            }
                        } catch (Exception e) {
                            // ignore
                        }
                    }

                    // 排序
                    list.sort((a, b) -> {
                        LocalDateTime t1 = a.getCreateTime() != null ? a.getCreateTime() : LocalDateTime.MIN;
                        LocalDateTime t2 = b.getCreateTime() != null ? b.getCreateTime() : LocalDateTime.MIN;
                        return t2.compareTo(t1);
                    });
                    
                    historyByDate.put(dateStr, list);
                }
            }
                    
        } catch (Exception e) {
            log.error("扫描聚类历史记录文件失败", e);
        }
        
        return historyByDate;
    }

    /**
     * 从数据库读取所有聚类分析历史记录
     * 这里也改为基于文件系统，为了保持 getRecentClusteringHistory 的一致性
     *
     * @return 历史记录列表
     */
    public List<ClusteringHistory> getClusteringHistory() {
        // 复用文件扫描逻辑
        Map<String, List<ClusteringHistory>> grouped = getClusteringHistoryGroupedByDate();
        List<ClusteringHistory> all = new ArrayList<>();
        grouped.values().forEach(all::addAll);
        return all;
    }

    /**
     * 获取最近的N条聚类分析记录
     *
     * @param limit 限制数量
     * @return 历史记录列表
     */
    public List<ClusteringHistory> getRecentClusteringHistory(int limit) {
        List<ClusteringHistory> allHistory = getClusteringHistory();
        return allHistory.stream()
                .limit(limit)
                .sorted((a, b) -> {
                    LocalDateTime timeA = a.getCreateTime() != null ? a.getCreateTime() : LocalDateTime.MIN;
                    LocalDateTime timeB = b.getCreateTime() != null ? b.getCreateTime() : LocalDateTime.MIN;
                    return timeB.compareTo(timeA);
                })
                .collect(Collectors.toList());
    }

    /**
     * 根据分析ID获取聚类分析记录
     *
     * @param analysisId 分析ID
     * @return 聚类分析记录
     */
    public Optional<ClusteringHistory> getClusteringHistoryById(String analysisId) {
        List<ClusteringHistory> allHistory = getClusteringHistory();
        return allHistory.stream()
                .filter(h -> analysisId.equals(h.getAnalysisId()))
                .findFirst();
    }

    /**
     * 获取成功的分析次数统计
     *
     * @return 统计数据
     */
    public Map<String, Object> getClusteringStatistics() {
        Map<String, Object> statistics = new HashMap<>();
        try {
            long successCount = clusteringHistoryRepository.countSuccessfulAnalysis();
            List<ClusteringHistory> failedList = clusteringHistoryRepository.findFailedAnalysis();
            
            statistics.put("successCount", successCount);
            statistics.put("errorCount", failedList.size());
            statistics.put("totalCount", successCount + failedList.size());
            
            return statistics;
        } catch (Exception e) {
            log.error("获取统计数据异常", e);
            return statistics;
        }
    }
}

