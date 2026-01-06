package com.example.gujihuohua.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.time.LocalDateTime;

/**
 * 用户上传的文件记录实体类
 * 用于存储用户上传的CSV、JSON等文件信息
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "upload_files")
public class UploadFile {

    /**
     * 主键ID
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * 原始文件名
     */
    @Column(nullable = false, length = 255)
    private String fileName;

    /**
     * 文件类型 (CSV/JSON)
     */
    @Column(nullable = false, length = 50)
    private String fileType;

    /**
     * 文件保存路径
     */
    @Column(nullable = false, length = 500)
    private String filePath;

    /**
     * 文件大小(字节)
     */
    @Column(nullable = false, columnDefinition = "bigint default 0")
    private Long fileSize;

    /**
     * 文件内容预览(前1000字符)
     */
    @Column(columnDefinition = "TEXT")
    private String contentPreview;

    /**
     * 文件MD5校验码
     */
    @Column(length = 32)
    private String fileMd5;

    /**
     * 上传时间
     */
    @Column(nullable = false, columnDefinition = "datetime default current_timestamp")
    private LocalDateTime uploadTime;

    /**
     * 创建时间
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
        if (uploadTime == null) {
            uploadTime = LocalDateTime.now();
        }
        if (createTime == null) {
            createTime = LocalDateTime.now();
        }
        if (updateTime == null) {
            updateTime = LocalDateTime.now();
        }
    }

    @PreUpdate
    protected void onUpdate() {
        updateTime = LocalDateTime.now();
    }
}
