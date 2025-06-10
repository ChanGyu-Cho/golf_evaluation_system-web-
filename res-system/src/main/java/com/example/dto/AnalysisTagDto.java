package com.example.dto;

public class AnalysisTagDto {
    private Long userId;
    private String analysisId;
    private Integer frameIndex;
    private String tag;
    private String memo;

    // 기본 생성자
    public AnalysisTagDto() {}

    // getter, setter
    public Long getUserId() {
        return userId;
    }
    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getAnalysisId() {
        return analysisId;
    }
    public void setAnalysisId(String analysisId) {
        this.analysisId = analysisId;
    }

    public Integer getFrameIndex() {
        return frameIndex;
    }
    public void setFrameIndex(Integer frameIndex) {
        this.frameIndex = frameIndex;
    }

    public String getTag() {
        return tag;
    }
    public void setTag(String tag) {
        this.tag = tag;
    }

    public String getMemo() {
        return memo;
    }
    public void setMemo(String memo) {
        this.memo = memo;
    }
}
