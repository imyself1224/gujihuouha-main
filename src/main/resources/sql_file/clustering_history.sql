-- ----------------------------
-- 时空聚类分析历史记录表
-- ----------------------------
USE gujihuohua;

DROP TABLE IF EXISTS `clustering_history`;

CREATE TABLE `clustering_history`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `analysis_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '分析记录唯一标识',
  `location_file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '地点文件名',
  `location_file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '地点文件本地路径',
  `events_file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件文件名',
  `events_file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '事件文件本地路径',
  `num_events` int NULL DEFAULT 0 COMMENT '事件数量',
  `num_clusters` int NULL DEFAULT 0 COMMENT '聚类数量',
  `num_noise` int NULL DEFAULT 0 COMMENT '噪声点数量',
  `analysis_status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'success' COMMENT '分析状态 (success/error)',
  `result_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '聚类结果数据(JSON格式)',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '错误信息(如有)',
  `analysis_time_cost` bigint NULL DEFAULT 0 COMMENT '分析耗时(毫秒)',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_analysis_id`(`analysis_id`) USING BTREE,
  INDEX `idx_create_time`(`create_time`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '时空聚类分析历史记录表' ROW_FORMAT = Dynamic;
