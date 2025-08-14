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

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
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

        String insertSql = "INSERT INTO comment (userid, analysis_id, frame_index, tag, memo, timestamp_sec) " +
                "VALUES (?, ?, ?, ?, ?, ?)";
        Query query = entityManager.createNativeQuery(insertSql);
        query.setParameter(1, dto.getUserId());
        query.setParameter(2, dto.getAnalysis_id());  // snake_case getter
        query.setParameter(3, dto.getFrame_index());
        query.setParameter(4, dto.getTag());
        query.setParameter(5, dto.getMemo());
        query.setParameter(6, now); // 현재시간

        query.executeUpdate();
        return ResponseEntity.ok("태그 저장 완료");
    }

    // ✅ 2. 특정 분석 ID의 태그/메모 조회
    @GetMapping("/{analysis_id}")
    public ResponseEntity<?> getTags(@PathVariable("analysis_id") String baseId) {

        String sql =
                "SELECT userid, analysis_id, frame_index, tag, memo, timestamp_sec " +
                        "FROM comment " +
                        "WHERE analysis_id REGEXP CONCAT('^', ?, '_[0-9]+$') " +
                        "ORDER BY frame_index ASC";

        Query query = entityManager.createNativeQuery(sql);
        query.setParameter(1, baseId);

        List<Object[]> results = query.getResultList();

        /* -------- 여기서 response 리스트를 먼저 선언 -------- */
        List<Map<String, Object>> response = new ArrayList<>();

        for (Object[] row : results) {
            Map<String, Object> map = new HashMap<>();
            map.put("userId",      row[0]);
            map.put("analysis_id", row[1]);
            map.put("frame_index", row[2]);
            map.put("tag",         row[3]);
            map.put("memo",        row[4]);
            map.put("timestamp",   row[5].toString());
            response.add(map);          // ← 이제 컴파일 오류 없음
        }

        return ResponseEntity.ok(response);
    }


    // ✅ 3. 특정 메모 삭제
    @Transactional
    @DeleteMapping("/delete/{analysis_id}")
    public ResponseEntity<?> deleteTag(@PathVariable String analysis_id) {
        String deleteSql = "DELETE FROM comment WHERE analysis_id = ?";
        Query query = entityManager.createNativeQuery(deleteSql);
        query.setParameter(1, analysis_id);
        int deletedCount = query.executeUpdate();

        if (deletedCount > 0) {
            return ResponseEntity.ok("삭제 성공");
        } else {
            return ResponseEntity.status(404).body("해당 메모가 존재하지 않습니다.");
        }
    }

    // ✅ 4. 유저 전체 메모 삭제
    @Transactional
    @DeleteMapping("/allDelete/{analysis_id}")
    public ResponseEntity<?> allDeleteTag(@PathVariable String analysis_id) {
        String deleteSql = "DELETE FROM comment " +
                "WHERE analysis_id REGEXP CONCAT('^', ?, '_[0-9]+$') ";
        Query query = entityManager.createNativeQuery(deleteSql);
        query.setParameter(1, analysis_id);
        int deletedCount = query.executeUpdate();

        if (deletedCount > 0) {
            return ResponseEntity.ok("삭제 성공");
        } else {
            return ResponseEntity.status(404).body("해당 메모가 존재하지 않습니다.");
        }
    }

}
