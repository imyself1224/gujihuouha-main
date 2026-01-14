package com.example.gujihuohua.mapper;

import com.example.gujihuohua.entity.UploadFile;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 上传文件数据访问层
 */
@Repository
public interface UploadFileRepository extends JpaRepository<UploadFile, Long> {

    /**
     * 根据文件MD5查找
     */
    Optional<UploadFile> findByFileMd5(String fileMd5);

    /**
     * 查找所有CSV文件
     */
    List<UploadFile> findByFileType(String fileType);

    /**
     * 查找指定时间范围内上传的文件
     */
    @Query("SELECT u FROM UploadFile u WHERE u.uploadTime BETWEEN :startTime AND :endTime ORDER BY u.uploadTime DESC")
    List<UploadFile> findByUploadTimeRange(@Param("startTime") LocalDateTime startTime, @Param("endTime") LocalDateTime endTime);

    /**
     * 查找最近上传的N个文件
     */
    @Query(value = "SELECT * FROM upload_files ORDER BY upload_time DESC LIMIT :limit", nativeQuery = true)
    List<UploadFile> findRecentFiles(@Param("limit") int limit);

    /**
     * 查找特定类型的最近文件
     */
    @Query("SELECT u FROM UploadFile u WHERE u.fileType = :fileType ORDER BY u.uploadTime DESC")
    List<UploadFile> findRecentFilesByType(@Param("fileType") String fileType);
}
