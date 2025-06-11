package com.example.controller;

import com.example.dto.AnalysisTagDto;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.Query;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/comments")
public class CommentsController {

    @PersistenceContext
    private EntityManager entityManager;

    // ✅ 1. 태그/메모 추가
    @Transactional
    @PostMapping("/add")
    public ResponseEntity<?> addTag(@RequestBody AnalysisTagDto dto) {
        Timestamp now = Timestamp.valueOf(LocalDateTime.now());

        String insertSql = "INSERT INTO analysis_tag (userid, analysis_id, frame_index, tag, memo, timestamp_sec) " +
                "VALUES (?, ?, ?, ?, ?, ?)";
        Query query = entityManager.createNativeQuery(insertSql);
        query.setParameter(1, dto.getUserId());
        query.setParameter(2, dto.getAnalysisId());
        query.setParameter(3, dto.getFrameIndex());
        query.setParameter(4, dto.getTag());
        query.setParameter(5, dto.getMemo());
        query.setParameter(6, now); // 현재시간

        query.executeUpdate();
        return ResponseEntity.ok("태그 저장 완료");
    }

    // ✅ 2. 특정 분석 ID에 대한 전체 태그/메모 조회
    @GetMapping("/{analysisId}")
    public ResponseEntity<?> getTags(@PathVariable String analysisId) {
        String sql = "SELECT id, userid, analysis_id, frame_index, tag, memo, timestamp_sec " +
                "FROM analysis_tag WHERE analysis_id = ? ORDER BY frame_index ASC";

        Query query = entityManager.createNativeQuery(sql);
        query.setParameter(1, analysisId);

        List<Object[]> results = query.getResultList();
        List<Map<String, Object>> response = new ArrayList<>();

        for (Object[] row : results) {
            Map<String, Object> map = new HashMap<>();
            map.put("id", row[0]);
            map.put("userId", row[1]);
            map.put("analysisId", row[2]);
            map.put("frameIndex", row[3]);
            map.put("tag", row[4]);
            map.put("memo", row[5]);
            map.put("timestamp", row[6].toString());  // Timestamp → String
            response.add(map);
        }

        return ResponseEntity.ok(response);
    }

    // ✅ 3. 특정 메모 삭제
    @Transactional
    @DeleteMapping("/delete/{analysisId}")
    public ResponseEntity<?> deleteTag(@PathVariable Long analysisId) {
        String deleteSql = "DELETE FROM analysis_tag WHERE id = ?";
        Query query = entityManager.createNativeQuery(deleteSql);
        query.setParameter(1, analysisId);
        int deletedCount = query.executeUpdate();

        if (deletedCount > 0) {
            return ResponseEntity.ok("삭제 성공");
        } else {
            return ResponseEntity.status(404).body("해당 메모가 존재하지 않습니다.");
        }
    }

}
