package com.example.gujihuohua.mapper;

import com.example.gujihuohua.entity.ClusteringHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 聚类分析历史记录数据访问层
 */
@Repository
public interface ClusteringHistoryRepository extends JpaRepository<ClusteringHistory, Long> {

    /**
     * 根据分析ID查找
     */
    Optional<ClusteringHistory> findByAnalysisId(String analysisId);

    /**
     * 查找所有成功的分析记录
     */
    List<ClusteringHistory> findByAnalysisStatus(String analysisStatus);

    /**
     * 查找所有历史记录，按创建时间倒序
     */
    @Query("SELECT c FROM ClusteringHistory c ORDER BY c.createTime DESC")
    List<ClusteringHistory> findAllOrderByCreateTimeDesc();

    /**
     * 查找最近的N条记录
     */
    @Query(value = "SELECT * FROM clustering_history ORDER BY create_time DESC LIMIT :limit", nativeQuery = true)
    List<ClusteringHistory> findRecentRecords(@Param("limit") int limit);

    /**
     * 查找指定时间范围内的分析记录
     */
    @Query("SELECT c FROM ClusteringHistory c WHERE c.createTime BETWEEN :startTime AND :endTime ORDER BY c.createTime DESC")
    List<ClusteringHistory> findByTimeRange(@Param("startTime") LocalDateTime startTime, @Param("endTime") LocalDateTime endTime);

    /**
     * 统计成功的分析次数
     */
    @Query("SELECT COUNT(c) FROM ClusteringHistory c WHERE c.analysisStatus = 'success'")
    long countSuccessfulAnalysis();

    /**
     * 查找所有失败的分析记录
     */
    @Query("SELECT c FROM ClusteringHistory c WHERE c.analysisStatus = 'error' ORDER BY c.createTime DESC")
    List<ClusteringHistory> findFailedAnalysis();
}
