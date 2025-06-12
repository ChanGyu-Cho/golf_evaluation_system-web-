package com.example.dto;

public class AnalysisTagDto {

    private Long userId;            // DB 컬럼은 userid
    private String analysis_id;     // ★ 그대로 사용
    private Integer frame_index;    // ★ 그대로 사용
    private String tag;
    private String memo;

    /* 기본 생성자 */
    public AnalysisTagDto() {}

    /* ------- getter / setter ------- */
    public Long getUserId()               { return userId; }
    public void setUserId(Long userId)    { this.userId = userId; }

    public String getAnalysis_id()                { return analysis_id; }
    public void setAnalysis_id(String analysis_id){ this.analysis_id = analysis_id; }

    public Integer getFrame_index()                 { return frame_index; }
    public void setFrame_index(Integer frame_index) { this.frame_index = frame_index; }

    public String getTag()            { return tag; }
    public void setTag(String tag)    { this.tag = tag; }

    public String getMemo()           { return memo; }
    public void setMemo(String memo)  { this.memo = memo; }
}
