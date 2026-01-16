package com.example.gujihuohua.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/**
 * 时空聚类分析历史记录实体类
 * 用于存储聚类分析的历史记录和结果
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "clustering_history")
public class ClusteringHistory {

    /**
     * 主键ID
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * 分析记录唯一标识
     */
    @Column(nullable = false, unique = true, length = 64)
    private String analysisId;

    /**
     * 地点文件名
     */
    @Column(length = 255)
    private String locationFileName;

    /**
     * 地点文件本地路径
     */
    @Column(length = 500)
    private String locationFilePath;

    /**
     * 事件文件名
     */
    @Column(length = 255)
    private String eventsFileName;

    /**
     * 事件文件本地路径
     */
    @Column(length = 500)
    private String eventsFilePath;

    /**
     * 事件数量
     */
    @Column(columnDefinition = "int default 0")
    private Integer numEvents;

    /**
     * 聚类数量
     */
    @Column(columnDefinition = "int default 0")
    private Integer numClusters;

    /**
     * 噪声点数量
     */
    @Column(columnDefinition = "int default 0")
    private Integer numNoise;

    /**
     * 分析状态 (success/error)
     */
    @Column(nullable = false, length = 50, columnDefinition = "varchar(50) default 'success'")
    private String analysisStatus;

    /**
     * 聚类结果数据(JSON格式)
     */
    @Column(columnDefinition = "LONGTEXT")
    private String resultData;

    /**
     * 错误信息(如有)
     */
    @Column(columnDefinition = "TEXT")
    private String errorMessage;

    /**
     * 分析耗时(毫秒)
     */
    @Column(columnDefinition = "bigint default 0")
    private Long analysisTimeCost;

    /**
     * 分析时间
     */
    @Column(nullable = false, columnDefinition = "datetime default current_timestamp")
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    @Column(nullable = false, columnDefinition = "datetime default current_timestamp on update current_timestamp")
    private LocalDateTime updateTime;

    @PrePersist
    protected void onCreate() {
        if (createTime == null) {
            createTime = LocalDateTime.now();
        }
        if (updateTime == null) {
            updateTime = LocalDateTime.now();
        }
        if (analysisStatus == null) {
            analysisStatus = "success";
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updateTime = LocalDateTime.now();
    }
}
