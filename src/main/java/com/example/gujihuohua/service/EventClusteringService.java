package com.example.gujihuohua.service;

import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.example.gujihuohua.entity.ClusteringHistory;
import com.example.gujihuohua.mapper.ClusteringHistoryRepository;
import com.google.gson.Gson;
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

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

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
            log.info("开始执行事件聚类分析");

            // 生成唯一的分析ID
            String analysisId = generateAnalysisId();

            // 保存地点数据到本地文件系统
            String locationFilePath = saveLocationDataToFile(locationData, locationFileName);
            log.info("地点数据已保存到: {}", locationFilePath);

            // 保存事件数据到本地文件系统
            String eventsFilePath = saveEventDataToFile(eventsData, eventsFileName);
            log.info("事件数据已保存到: {}", eventsFilePath);

            // 调用 Flask 聚类服务
            Map<String, Object> clusteringResult = callFlaskClusteringService(locationData, eventsData);

            long endTime = System.currentTimeMillis();
            long timeCost = endTime - startTime;

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
                        
                        log.info("聚类分析完成: {} 个事件, {} 个聚类, {} 个噪声点", totalEvents, 
                                history.getNumClusters(), noiseCount);
                    }
                }
            } else {
                result.put("status", "error");
                result.put("message", clusteringResult.get("message"));
                result.put("error", clusteringResult.get("error"));
                result.put("analysisId", analysisId);

                history.setAnalysisStatus("error");
                history.setErrorMessage((String) clusteringResult.get("error"));
                log.error("聚类分析失败: {}", clusteringResult.get("error"));
            }

            // 保存历史记录到数据库
            try {
                clusteringHistoryRepository.save(history);
                log.info("聚类分析历史记录已保存到数据库: {}", analysisId);
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
     * @return 保存的文件路径
     * @throws IOException 如果文件操作失败
     */
    private String saveEventDataToFile(String eventsData, String fileName) throws IOException {
        // 检查是否存在重复数据
        String md5Hash = calculateMD5(eventsData);
        String existingPath = checkExistingFile(md5Hash, "events");
        if (existingPath != null) {
            log.info("检测到重复事件数据，使用已存在的文件: {}", existingPath);
            return existingPath;
        }

        // 创建日期目录
        LocalDate today = LocalDate.now();
        String dateStr = today.format(DATE_FORMATTER);
        Path dateDir = Paths.get(storageRootPath, CLUSTER_STORAGE_DIR, dateStr);
        Files.createDirectories(dateDir);

        // 生成唯一的文件名
        String uuid = UUID.randomUUID().toString().substring(0, 8);
        String extension = fileName.endsWith(".json") ? ".json" : ".json";
        String fileNameWithUUID = uuid + "_events" + extension;
        
        Path filePath = dateDir.resolve(fileNameWithUUID);

        // 保存文件
        Files.write(filePath, eventsData.getBytes(StandardCharsets.UTF_8));
        log.info("事件数据已保存: {} (MD5: {})", filePath, md5Hash);

        // 保存MD5映射
        saveMD5Mapping(md5Hash, "events", filePath.toString());

        return filePath.toString();
    }

    /**
     * 保存地点数据到本地文件系统
     *
     * @param locationData CSV格式的地点数据
     * @param fileName     原始文件名
     * @return 保存的文件路径
     * @throws IOException 如果文件操作失败
     */
    private String saveLocationDataToFile(String locationData, String fileName) throws IOException {
        // 检查是否存在重复数据
        String md5Hash = calculateMD5(locationData);
        String existingPath = checkExistingFile(md5Hash, "location");
        if (existingPath != null) {
            log.info("检测到重复地点数据，使用已存在的文件: {}", existingPath);
            return existingPath;
        }

        // 创建日期目录
        LocalDate today = LocalDate.now();
        String dateStr = today.format(DATE_FORMATTER);
        Path dateDir = Paths.get(storageRootPath, CLUSTER_STORAGE_DIR, dateStr);
        Files.createDirectories(dateDir);

        // 生成唯一的文件名
        String uuid = UUID.randomUUID().toString().substring(0, 8);
        String extension = fileName.endsWith(".csv") ? ".csv" : ".csv";
        String fileNameWithUUID = uuid + "_locations" + extension;
        
        Path filePath = dateDir.resolve(fileNameWithUUID);

        // 保存文件
        Files.write(filePath, locationData.getBytes(StandardCharsets.UTF_8));
        log.info("地点数据已保存: {} (MD5: {})", filePath, md5Hash);

        // 保存MD5映射
        saveMD5Mapping(md5Hash, "location", filePath.toString());

        return filePath.toString();
    }

    /**
     * 检查是否存在重复的文件
     *
     * @param md5Hash 文件内容的MD5哈希值
     * @param type    文件类型 (location 或 events)
     * @return 如果存在重复返回文件路径，否则返回null
     */
    private String checkExistingFile(String md5Hash, String type) {
        String mapFilePath = getHashMapFilePath();
        try {
            Path mapFile = Paths.get(mapFilePath);
            if (Files.exists(mapFile)) {
                String content = new String(Files.readAllBytes(mapFile), StandardCharsets.UTF_8);
                JSONObject hashMap = JSON.parseObject(content);
                
                String key = type + "_" + md5Hash;
                if (hashMap.containsKey(key)) {
                    String path = hashMap.getString(key);
                    // 验证文件是否仍然存在
                    if (Files.exists(Paths.get(path))) {
                        return path;
                    }
                }
            }
        } catch (Exception e) {
            log.debug("检查重复文件失败", e);
        }
        return null;
    }

    /**
     * 保存MD5映射信息
     *
     * @param md5Hash 文件内容的MD5哈希值
     * @param type    文件类型
     * @param path    文件路径
     */
    private void saveMD5Mapping(String md5Hash, String type, String path) {
        try {
            String mapFilePath = getHashMapFilePath();
            Path mapFile = Paths.get(mapFilePath);
            
            JSONObject hashMap = new JSONObject();
            if (Files.exists(mapFile)) {
                String content = new String(Files.readAllBytes(mapFile), StandardCharsets.UTF_8);
                hashMap = JSON.parseObject(content);
            }
            
            String key = type + "_" + md5Hash;
            hashMap.put(key, path);
            
            Files.write(mapFile, JSON.toJSONString(hashMap, true).getBytes(StandardCharsets.UTF_8));
        } catch (Exception e) {
            log.warn("保存MD5映射失败", e);
        }
    }

    /**
     * 获取MD5映射文件路径
     */
    private String getHashMapFilePath() {
        return Paths.get(storageRootPath, CLUSTER_STORAGE_DIR, "hash_mapping.json").toString();
    }

    /**
     * 计算文件内容的MD5值
     *
     * @param content 文件内容
     * @return MD5值
     */
    private String calculateMD5(String content) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] messageDigest = md.digest(content.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : messageDigest) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            log.error("计算MD5异常", e);
            return "";
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
            
            // 获取所有日期目录
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
     * 简化逻辑：直接读取日期文件夹下的CSV（地点数据）和JSON（事件数据）文件
     *
     * @param dateStr 日期字符串 (格式: yyyy-MM-dd)
     * @return 该日期下的记录列表
     */
    public List<Map<String, Object>> getRecordsByDate(String dateStr) {
        List<Map<String, Object>> recordsForDate = new ArrayList<>();
        
        try {
            Path dateDir = Paths.get(storageRootPath)
                    .resolve(CLUSTER_STORAGE_DIR)
                    .resolve(dateStr);
            
            if (!Files.exists(dateDir) || !Files.isDirectory(dateDir)) {
                log.warn("日期目录不存在: {}", dateDir);
                return recordsForDate;
            }
            
            // 获取该日期目录下所有的CSV文件（地点数据）和JSON文件（事件数据）
            List<Path> csvFiles = new ArrayList<>();
            List<Path> jsonFiles = new ArrayList<>();
            
            Files.list(dateDir)
                    .filter(Files::isRegularFile)
                    .forEach(file -> {
                        String fileName = file.getFileName().toString();
                        if (fileName.endsWith(".csv")) {
                            csvFiles.add(file);
                        } else if (fileName.endsWith(".json")) {
                            jsonFiles.add(file);
                        }
                    });
            
            log.debug("日期 {} 找到 {} 个CSV文件和 {} 个JSON文件", dateStr, csvFiles.size(), jsonFiles.size());
            
            // 构建该日期的历史记录
            // 每条记录对应一个聚类分析，包含一个CSV文件和一个JSON文件
            int recordCount = Math.min(csvFiles.size(), jsonFiles.size());
            for (int i = 0; i < recordCount; i++) {
                Map<String, Object> record = new HashMap<>();
                
                // 使用时间戳作为分析ID
                String analysisId = String.format("%s_%d", dateStr, i);
                
                Path csvFile = csvFiles.get(i);
                Path jsonFile = jsonFiles.get(i);
                
                record.put("analysisId", analysisId);
                record.put("date", dateStr);
                record.put("locationFileName", csvFile.getFileName().toString());
                record.put("locationFilePath", csvFile.toString());
                record.put("eventsFileName", jsonFile.getFileName().toString());
                record.put("eventsFilePath", jsonFile.toString());
                
                recordsForDate.add(record);
                log.debug("创建记录: {} -> {} 和 {}", analysisId, 
                        csvFile.getFileName(), jsonFile.getFileName());
            }
            
        } catch (Exception e) {
            log.error("获取日期记录失败: {}", dateStr, e);
        }
        
        return recordsForDate;
    }

    /**
     * 从文件系统读取所有聚类分析历史记录，按日期分组
     * 扫描 data-storage/cluster-storage 目录下的所有日期目录
     *
     * @return 按日期组织的历史记录Map (日期 -> 记录列表)
     */
    public Map<String, List<Map<String, Object>>> getClusteringHistoryByDate() {
        Map<String, List<Map<String, Object>>> historyByDate = new LinkedHashMap<>();
        
        try {
            List<String> dates = getAnalysisDates();
            for (String dateStr : dates) {
                List<Map<String, Object>> recordsForDate = getRecordsByDate(dateStr);
                if (!recordsForDate.isEmpty()) {
                    historyByDate.put(dateStr, recordsForDate);
                }
            }
                    
        } catch (Exception e) {
            log.error("读取聚类历史记录失败", e);
        }
        
        return historyByDate;
    }

    /**
     * 从文件系统读取所有聚类分析历史记录（平面列表，保留兼容性）
     *
     * @return 历史记录列表
     */
    public List<ClusteringHistory> getClusteringHistory() {
        List<ClusteringHistory> historyList = new ArrayList<>();
        Map<String, List<Map<String, Object>>> historyByDate = getClusteringHistoryByDate();
        
        // 将按日期分组的记录转换为平面列表
        historyByDate.forEach((date, records) -> {
            records.forEach(record -> {
                ClusteringHistory history = new ClusteringHistory();
                history.setAnalysisId((String) record.get("analysisId"));
                history.setLocationFileName((String) record.get("locationFileName"));
                history.setEventsFileName((String) record.get("eventsFileName"));
                history.setLocationFilePath((String) record.get("locationFilePath"));
                history.setEventsFilePath((String) record.get("eventsFilePath"));
                
                try {
                    LocalDate localDate = LocalDate.parse((String) record.get("date"), DATE_FORMATTER);
                    history.setCreateTime(localDate.atStartOfDay());
                } catch (Exception e) {
                    history.setCreateTime(LocalDateTime.now());
                }
                
                historyList.add(history);
            });
        });
        
        return historyList;
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

