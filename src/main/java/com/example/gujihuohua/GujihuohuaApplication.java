package com.example.gujihuohua;


import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@MapperScan(value = "com.example.gujihuohua.mapper", annotationClass = org.apache.ibatis.annotations.Mapper.class)
@EnableAsync
public class GujihuohuaApplication {
    public static void main(String[] args) {
        SpringApplication.run(GujihuohuaApplication.class, args);
    }

}
