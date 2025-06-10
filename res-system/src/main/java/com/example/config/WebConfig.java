package com.example.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // uploaded-videos 폴더에 대한 매핑 설정
        registry.addResourceHandler("/uploaded-videos/**")
                .addResourceLocations("file:///E:/resVue/resPy/uploaded-videos/");
    }
}
