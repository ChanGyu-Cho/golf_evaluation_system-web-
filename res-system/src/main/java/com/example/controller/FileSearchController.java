package com.example.controller;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.Query;
import jakarta.servlet.http.HttpServletResponse;

import jakarta.transaction.Transactional;
import lombok.extern.slf4j.Slf4j;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.io.File;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@Slf4j
@RequestMapping("/images")
public class FileSearchController {

    @PersistenceContext
    private EntityManager entityManager;

    // 비디오 저장 경로 (application.properties에서 관리 권장)
    @Value("${video.upload-dir}")
    private String baseDir;

    @PostMapping("/file_search")
    public ResponseEntity<?> fileSearch(@RequestBody Map<String, String> params, HttpServletResponse res) {
        String userIdStr = params.get("userid");

        log.info("file_search userid: {}", userIdStr);

        String sql;
        Query query;

        try {
            if (userIdStr.equalsIgnoreCase("admin")) {
                // admin일 경우 전체 조회
                sql = "SELECT userid, vid_name, eval, upload_date FROM video";
                query = entityManager.createNativeQuery(sql);
            } else {
                // 특정 사용자만 조회
                sql = "SELECT userid, vid_name, eval, upload_date FROM video WHERE userid = ?";
                query = entityManager.createNativeQuery(sql);
                query.setParameter(1, Integer.parseInt(userIdStr));
            }

            List<Object[]> results = query.getResultList();
            log.info("file_search results: {}", results);

            if (!results.isEmpty()) {
                List<Map<String, Object>> fileList = new ArrayList<>();

                for (Object[] row : results) {
                    Map<String, Object> fileMap = new HashMap<>();
                    fileMap.put("userid", row[0]);
                    fileMap.put("vid_name", row[1]);
                    fileMap.put("eval", row[2]);
                    fileMap.put("upload_date", row[3] != null ? row[3].toString() : null);
                    fileList.add(fileMap);
                }

                log.info("조회 결과: {}", fileList);
                return ResponseEntity.ok(fileList);
            } else {
                return ResponseEntity.ok(Map.of("status", "NOT"));
            }
        } catch (Exception e) {
            log.error("file_search error: ", e);
            return ResponseEntity.internalServerError().body("File search failed");
        }
    }



    @Transactional
    @PostMapping("/file_delete")
    public ResponseEntity<?> fileDelete(@RequestBody Map<String, Object> params) {
        try {
            List<Map<String, Object>> deleteList = (List<Map<String, Object>>) params.get("list");
            if (deleteList == null || deleteList.isEmpty()) {
                return ResponseEntity.badRequest().body(Map.of("message", "삭제할 항목이 없습니다."));
            }

            Path basePath = Paths.get(baseDir);  // baseDir은 예: "D:\\golf_evaluation_system-web-\\resPy\\uploaded-videos"

            for (Map<String, Object> item : deleteList) {
                String userIdStr = String.valueOf(item.get("userid"));
                String vidName = String.valueOf(item.get("vid_name"));

                if ("admin".equals(userIdStr)) {
                    continue;
                }

                String sql = "DELETE FROM video WHERE userid = ? AND vid_name = ?";
                Query query = entityManager.createNativeQuery(sql);
                query.setParameter(1, Integer.parseInt(userIdStr));
                query.setParameter(2, vidName);
                query.executeUpdate();

                // 영상 파일 삭제
                Path videoFile = basePath.resolve(vidName);
                deleteFileIfExists(videoFile);

                Path skeletonVideoFile = basePath.resolve("skeleton_" + vidName);
                deleteFileIfExists(skeletonVideoFile);

                // landmarkFiles 폴더 경로
                Path landmarkDir = basePath.resolve("landmarkFiles");

                String baseNameNoExt = vidName.contains(".")
                        ? vidName.substring(0, vidName.lastIndexOf('.'))
                        : vidName;

                // landmarkFiles 내 csv, json 삭제
                Path csvFile = landmarkDir.resolve("skeleton_" + baseNameNoExt + ".csv");
                Path jsonFile = landmarkDir.resolve("skeleton_" + baseNameNoExt + ".json");

                deleteFileIfExists(csvFile);
                deleteFileIfExists(jsonFile);
            }

            return ResponseEntity.ok(Map.of("message", "삭제가 완료되었습니다."));
        } catch (Exception e) {
            log.error("file_delete error: ", e);
            return ResponseEntity.internalServerError().body(Map.of("message", "삭제 처리 중 오류가 발생했습니다."));
        }
    }


    private void deleteFileIfExists(Path path) {
        try {
            if (Files.exists(path)) {
                Files.delete(path);
                log.info("파일 삭제: " + path.toString());
            } else {
                log.warn("삭제할 파일이 존재하지 않음: " + path.toString());
            }
        } catch (IOException e) {
            log.error("파일 삭제 중 오류 발생: " + path.toString(), e);
        }
    }

    // 추가된 부분: 비디오 파일 스트리밍/다운로드 API
    @GetMapping("/search_video")
    public ResponseEntity<Resource> serveVideo(@RequestParam String filename) {
        try {
            log.info(filename);
            Path filePath = Paths.get(baseDir).resolve(filename).normalize();
            Resource resource = new UrlResource(filePath.toUri());


            if (!resource.exists() || !resource.isReadable()) {
                log.warn("비디오 파일이 존재하지 않거나 읽을 수 없습니다: {}", filename);
                return ResponseEntity.notFound().build();
            }

            // 파일 MIME 타입 확인 (필요시 확장자별 분기 가능)
            String contentType = Files.probeContentType(filePath);
            if (contentType == null) {
                contentType = "application/octet-stream";
            }

            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(contentType))
                    .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + resource.getFilename() + "\"")
                    .body(resource);

        } catch (MalformedURLException e) {
            log.error("잘못된 파일 경로: {}", filename, e);
            return ResponseEntity.badRequest().build();
        } catch (IOException e) {
            log.error("파일 MIME 타입 조회 중 오류: {}", filename, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @GetMapping("/search_json")
    public ResponseEntity<Resource> serveJson(@RequestParam String filename) {
        try {
            // 확장자 강제 추가 (사용자가 .json을 포함하지 않아도 되도록)
            if (!filename.endsWith(".json")) {
                filename = filename + ".json";
            }

            // landmarkFiles 하위 JSON 파일 경로 구성
            Path jsonPath = Paths.get(baseDir)
                    .resolve("landmarkFiles")
                    .resolve(filename)
                    .normalize();

            Resource resource = new UrlResource(jsonPath.toUri());

            if (!resource.exists() || !resource.isReadable()) {
                log.warn("JSON 파일을 찾을 수 없거나 읽을 수 없습니다: {}", jsonPath);
                return ResponseEntity.notFound().build();
            }

            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_JSON)
                    .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + resource.getFilename() + "\"")
                    .body(resource);

        } catch (MalformedURLException e) {
            log.error("잘못된 파일 경로(json): {}", filename, e);
            return ResponseEntity.badRequest().build();
        }
    }


}
