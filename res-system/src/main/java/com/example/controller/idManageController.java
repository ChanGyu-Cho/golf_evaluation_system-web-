package com.example.controller;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.Query;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@Slf4j

public class idManageController {

    @PersistenceContext
    private EntityManager entityManager;    // entityManager를 선언하고 불러와야함

    @PostMapping("/api/login5")  // post 방식
    public ResponseEntity<?> login5(@RequestBody Map<String, String> requestBody, HttpServletResponse res) {
        String userid = requestBody.get("s_userid");
        String userpass = requestBody.get("s_userpass");

        log.info("userid: {}", userid);
        log.info("password: {}", userpass);

        String sql = "SELECT * FROM basemp WHERE userid = ? AND userpass = ?";
        try {
            // 네이티브 쿼리 생성
            Query query = entityManager.createNativeQuery(sql);
            query.setParameter(1, userid);  // 처음 ?에 userid를 넣고
            query.setParameter(2, userpass);    // 다음 ?에 userpass를 넣는다

            // 결과 조회
            List<Object[]> results = query.getResultList();
            log.info("results: {}", results);
            if (!results.isEmpty()) {
                Object[] row = results.get(0);  // select로 나오는 데이터는 유저정보 1줄 짜리
                Map <String, Object> resultMap = new HashMap<>();
                resultMap.put("userid", row[0]);
                resultMap.put("userpass", row[1]);
                resultMap.put("username", row[2]);
                resultMap.put("usermail", row[3]);

                log.info("조회 결과: " + resultMap);
                return ResponseEntity.ok(resultMap);
            } else {
                return ResponseEntity.ok("NOT");
            }
        } catch (Exception e) {
            log.error("Login error: ", e);
            return ResponseEntity.internalServerError().body("Expection Login failed");
        }
    }


    @PostMapping("/api/user_search")  // post 방식
    public ResponseEntity<?> user_search(@RequestBody Map<String, String> params, HttpServletResponse res) {
        String username = params.get("s_username");

        log.info("username: {}", username);

        // username이 null이거나 빈 문자열일 경우 전체 데이터를 반환
        String sql = "SELECT * FROM basemp WHERE username LIKE ?";

        try {
            // 네이티브 쿼리 생성
            Query query = entityManager.createNativeQuery(sql);

            // username이 비어 있으면 '%'로 설정하여 전체 데이터를 검색
            if (username == null || username.trim().isEmpty()) {
                query.setParameter(1, "%");
            } else {
                query.setParameter(1, '%'+username + '%');  // 부분 검색을 위한 LIKE 쿼리
            }

            // 결과 조회
            List<Object[]> results = query.getResultList();
            log.info("results: {}", results);

            if (!results.isEmpty()) {
                List<Map<String, Object>> userList = new ArrayList<>();

                for (Object[] row : results) {
                    Map<String, Object> userMap = new HashMap<>();
                    userMap.put("userid", row[0]);
                    userMap.put("userpass", row[1]);
                    userMap.put("username", row[2]);
                    userMap.put("usermail", row[3]);
                    userList.add(userMap);
                }

                log.info("조회 결과: " + userList);
                return ResponseEntity.ok(userList);
            } else {
                return ResponseEntity.ok(Map.of("status", "NOT"));
            }
        } catch (Exception e) {
            log.error("Login error: ", e);
            return ResponseEntity.internalServerError().body("Exception Login failed");
        }
    }

    @PostMapping("/api/user_insert")  // post 방식
    @Transactional  // 트랜잭션 관리
    public ResponseEntity<?> user_insert(@RequestBody Map<String, String> params, HttpServletResponse res) {
        String userid = params.get("s_userid");
        String userpass = params.get("s_userpass");
        String username = params.get("s_username");
        String usermail = params.get("s_usermail");

        log.info("userid: {}", userid);
        log.info("userpass: {}", userpass);
        log.info("username: {}", username);
        log.info("usermail: {}", usermail);

        // 먼저 userid가 이미 존재하는지 확인
        String sql = "SELECT * FROM basemp WHERE userid = ?";
        try {
            // 네이티브 쿼리 생성
            Query query = entityManager.createNativeQuery(sql);
            query.setParameter(1, userid);

            // 결과 조회
            List<Object[]> results = query.getResultList();

            if (!results.isEmpty()) {
                // 이미 존재하는 경우
                return  ResponseEntity.ok("사용자가 이미 존재합니다");
            }

            // userid가 존재하지 않으면 INSERT 쿼리 실행
            String insertSql = "INSERT INTO basemp (userid, userpass, username, usermail) VALUES (?, ?, ?, ?)";
            Query insertQuery = entityManager.createNativeQuery(insertSql);
            insertQuery.setParameter(1, userid);
            insertQuery.setParameter(2, userpass);
            insertQuery.setParameter(3, username);
            insertQuery.setParameter(4, usermail);

            insertQuery.executeUpdate();  // INSERT 실행

            return ResponseEntity.ok("사용자 추가 완료");

        } catch (Exception e) {
            log.error("Error occurred: ", e);
            return ResponseEntity.internalServerError().body("사용자 추가 실패");
        }
    }

    @PostMapping("/api/user_delete")
    @Transactional
    public ResponseEntity<?> userDelete(@RequestBody Map<String, Object> params) {
        List<String> userIds = (List<String>) params.get("s_userids");

        log.info("삭제 요청된 사용자 목록: {}", userIds);

        if (userIds.contains("admin")) {
            return ResponseEntity.ok("admin은 삭제할 수 없습니다");
        }

        String sql = "DELETE FROM basemp WHERE userid IN (:ids)";   // :로 바인드 파라미터 사용, ?는 순서기반, :는 이름 기반이다
        try {
            Query query = entityManager.createNativeQuery(sql);
            query.setParameter("ids", userIds); // :ids에 userIds 리스트를 넣음, IN 명령어를 통해 list에 해당하면 삭제
            int deletedCount = query.executeUpdate();

            return ResponseEntity.ok(deletedCount + "명의 사용자가 삭제되었습니다");
        } catch (Exception e) {
            log.error("삭제 오류: ", e);
            return ResponseEntity.internalServerError().body("사용자 삭제 실패");
        }
    }



    @PostMapping("/api/user_edit")  // post 방식
    @Transactional  // 트랜잭션 관리
    public ResponseEntity<?> user_edit(@RequestBody Map<String, String> params, HttpServletResponse res) {
        String userid = params.get("s_userid");
        String userpass = params.get("s_userpass");
        String username = params.get("s_username");
        String usermail = params.get("s_usermail");

        log.info("userid: {}", userid);
        log.info("userpass: {}", userpass);
        log.info("username: {}", username);
        log.info("usermail: {}", usermail);

        String sql = "SELECT * FROM basemp WHERE userid = ?";
        try {
            Query query = entityManager.createNativeQuery(sql);
            query.setParameter(1, userid);
            List<Object[]> results = query.getResultList();

            if (results.isEmpty()) {
                return ResponseEntity.ok("사용자가 존재하지 않습니다.");
            }

            String updateSql = "UPDATE basemp SET userpass = ?, username = ?, usermail = ? WHERE userid = ?";
            Query updateQuery = entityManager.createNativeQuery(updateSql);
            updateQuery.setParameter(1, userpass);
            updateQuery.setParameter(2, username);
            updateQuery.setParameter(3, usermail);
            updateQuery.setParameter(4, userid);

            updateQuery.executeUpdate();

            return ResponseEntity.ok("사용자 수정 완료");

        } catch (Exception e) {
            log.error("Error occurred: ", e);
            return ResponseEntity.internalServerError().body("사용자 수정 실패");
        }
    }
}