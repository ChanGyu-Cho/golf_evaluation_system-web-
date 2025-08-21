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
import java.util.List;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@Slf4j
@RequestMapping("/images")
public class FileSearchController {
    @GetMapping("/search_angle_json")
    public ResponseEntity<Resource> serveAngleJson(@RequestParam String filename) {
        try {
            String onlyName = new File(filename).getName();
            if (!onlyName.endsWith(".json")) {
                onlyName = onlyName + ".json";
            }
            log.info("search_angle_json 요청: {}", onlyName);
            File angleDir = new File("D:/golf_evaluation_system-web-/resPy/angle");
            if (!angleDir.exists() || !angleDir.isDirectory()) {
                log.warn("angle 폴더가 존재하지 않음");
                return ResponseEntity.notFound().build();
            }
            File[] files = angleDir.listFiles();
            if (files == null) {
                log.warn("angle 폴더 내 파일 없음");
                return ResponseEntity.notFound().build();
            }
            for (File f : files) {
                if (f.getName().equals(onlyName)) {
                    Resource resource = new UrlResource(f.toURI());
                    return ResponseEntity.ok()
                        .contentType(MediaType.APPLICATION_JSON)
                        .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + resource.getFilename() + "\"")
                        .body(resource);
                }
            }
            log.warn("angle 폴더에서 {} 파일을 찾을 수 없음", onlyName);
            return ResponseEntity.notFound().build();
        } catch (MalformedURLException e) {
            log.error("잘못된 파일 경로(angle json): {}", filename, e);
            return ResponseEntity.badRequest().build();
        }
    }

    @PersistenceContext
    private EntityManager entityManager;

    // 비디오 저장 경로 (application.properties에서 관리 권장)
    @Value("${video.upload-dir}")
    private String uploadDir;

    @PostMapping("/file_search")
    public ResponseEntity<?> fileSearch(@RequestBody Map<String, String> params, HttpServletResponse res) {
        String userIdStr = params.get("userid");
        log.info("file_search userid: {}", userIdStr);
        String sql;
        Query query;
        try {
            if (userIdStr.equalsIgnoreCase("admin")) {
                sql = "SELECT userid, vid_name, eval, upload_date FROM video";
                query = entityManager.createNativeQuery(sql);
            } else {
                sql = "SELECT userid, vid_name, eval, upload_date FROM video WHERE userid = ?";
                query = entityManager.createNativeQuery(sql);
                query.setParameter(1, userIdStr);
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
            return ResponseEntity.status(500).body("File search failed: " + e.getMessage());
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
            for (Map<String, Object> item : deleteList) {
                String userIdStr = String.valueOf(item.get("userid"));
                String vidName = String.valueOf(item.get("vid_name"));
                if ("admin".equals(userIdStr)) {
                    continue;
                }
                String sql = "DELETE FROM video WHERE userid = ? AND vid_name = ?";
                Query query = entityManager.createNativeQuery(sql);
                query.setParameter(1, userIdStr);
                query.setParameter(2, vidName);
                query.executeUpdate();

                // baseName: 확장자 없는 파일명
                String baseNameNoExt = vidName.contains(".")
                        ? vidName.substring(0, vidName.lastIndexOf('.'))
                        : vidName;

                // 1..n: 보다 관대하게 파일을 삭제하도록 변경
                // 각 폴더에서 baseNameNoExt를 포함하는 파일들을 찾아 삭제한다.
                String[] folders = new String[] {
                    "D:/golf_evaluation_system-web-/resPy/uploaded-videos",
                    "D:/golf_evaluation_system-web-/resPy/skeleton_video",
                    "D:/golf_evaluation_system-web-/resPy/angle",
                    "D:/golf_evaluation_system-web-/resPy/result/logs",
                    "D:/golf_evaluation_system-web-/resPy/crop_csv",
                    "D:/golf_evaluation_system-web-/resPy/crop_video",
                    "D:/golf_evaluation_system-web-/resPy/embedding",
                    "D:/golf_evaluation_system-web-/resPy/result",
                    "D:/golf_evaluation_system-web-/resPy/angle"
                };
                for (String folderPath : folders) {
                    File dir = new File(folderPath);
                    if (!dir.exists() || !dir.isDirectory()) continue;
                    File[] filesInDir = dir.listFiles();
                    if (filesInDir == null) continue;
                    for (File f : filesInDir) {
                        String fname = f.getName();
                        // 기본 매칭: 파일명에 baseNameNoExt가 포함되어 있으면 삭제 후보
                        if (fname.contains(baseNameNoExt)) {
                            deleteFileIfExists(f);
                        }
                    }
                }
            }
            return ResponseEntity.ok(Map.of("message", "삭제가 완료되었습니다."));
        } catch (Exception e) {
            log.error("file_delete error: ", e);
            return ResponseEntity.status(500).body(Map.of("message", "삭제 처리 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }


    private void deleteFileIfExists(File file) {
        try {
            if (file.exists()) {
                if (file.delete()) {
                    log.info("파일 삭제: " + file.getAbsolutePath());
                } else {
                    log.warn("파일 삭제 실패: " + file.getAbsolutePath());
                }
            } else {
                log.warn("삭제할 파일이 존재하지 않음: " + file.getAbsolutePath());
            }
        } catch (Exception e) {
            log.error("파일 삭제 중 오류 발생: " + file.getAbsolutePath(), e);
        }
    }

    // 비디오 파일 스트리밍/다운로드 API
    @GetMapping("/search_video")
    public ResponseEntity<Resource> serveVideo(@RequestParam String filename) {
        try {
            String onlyName = new File(filename).getName();
            log.info("search_video 요청: {}", onlyName);
            File skeletonVideoDir = new File("D:/golf_evaluation_system-web-/resPy/skeleton_video");
            if (!skeletonVideoDir.exists() || !skeletonVideoDir.isDirectory()) {
                log.warn("skeleton_video 폴더가 존재하지 않음");
                return ResponseEntity.notFound().build();
            }
            File[] files = skeletonVideoDir.listFiles();
            if (files == null) {
                log.warn("skeleton_video 폴더 내 파일 없음");
                return ResponseEntity.notFound().build();
            }
            // 1) Try exact match
            for (File f : files) {
                if (f.getName().equals(onlyName)) {
                    Resource resource = new UrlResource(f.toURI());
                    String contentType = Files.probeContentType(f.toPath());
                    if (contentType == null) contentType = "application/octet-stream";
                    return ResponseEntity.ok()
                        .contentType(MediaType.parseMediaType(contentType))
                        .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + resource.getFilename() + "\"")
                        .body(resource);
                }
            }

            // 2) Fallback: allow relaxed matching by base name (handle skeleton_ prefix and _openpose_skeleton_h264 suffix variations)
            String base = onlyName.replaceFirst("^skeleton_", "");
            base = base.replaceAll("_openpose_skeleton_h264\\.mp4$", "");
            base = base.replaceAll("\\.mp4$", "");
            for (File f : files) {
                String fname = f.getName();
                if (fname.contains(base) && fname.toLowerCase().endsWith(".mp4")) {
                    Resource resource = new UrlResource(f.toURI());
                    String contentType = Files.probeContentType(f.toPath());
                    if (contentType == null) contentType = "application/octet-stream";
                    log.info("skeleton_video relaxed match: requested='{}' -> serving='{}'", onlyName, fname);
                    return ResponseEntity.ok()
                        .contentType(MediaType.parseMediaType(contentType))
                        .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + resource.getFilename() + "\"")
                        .body(resource);
                }
            }

            log.warn("skeleton_video 폴더에서 {} 파일을 찾을 수 없음", onlyName);
            return ResponseEntity.notFound().build();
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
            String onlyName = new File(filename).getName();
            if (!onlyName.endsWith(".json")) {
                onlyName = onlyName + ".json";
            }
            log.info("search_json 요청: {}", onlyName);

            // Defensive: if client passed only an evaluation label (e.g. Bad.json or Good.json),
            // don't treat it as a real filename. Return 404 to avoid noisy proxy errors.
            String lower = onlyName.toLowerCase();
            if (lower.equals("bad.json") || lower.equals("good.json") || lower.equals("unknown.json")) {
                log.warn("search_json: received evaluation label instead of filename: {}", onlyName);
                return ResponseEntity.notFound().build();
            }

            // 우선 resPy/result 폴더에서 찾고, 없으면 angle 폴더로 fallback
            File resultDir = new File("D:/golf_evaluation_system-web-/resPy/result");
            if (resultDir.exists() && resultDir.isDirectory()) {
                File[] resultFiles = resultDir.listFiles();
                if (resultFiles != null) {
                    for (File f : resultFiles) {
                        if (f.getName().equals(onlyName)) {
                            Resource resource = new UrlResource(f.toURI());
                            return ResponseEntity.ok()
                                .contentType(MediaType.APPLICATION_JSON)
                                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + resource.getFilename() + "\"")
                                .body(resource);
                        }
                    }
                }
            }

            // fallback: angle 폴더 (legacy)
            File angleDir = new File("D:/golf_evaluation_system-web-/resPy/angle");
            if (!angleDir.exists() || !angleDir.isDirectory()) {
                log.warn("angle 폴더가 존재하지 않음");
                return ResponseEntity.notFound().build();
            }
            File[] files = angleDir.listFiles();
            if (files == null) {
                log.warn("angle 폴더 내 파일 없음");
                return ResponseEntity.notFound().build();
            }
            for (File f : files) {
                if (f.getName().equals(onlyName)) {
                    Resource resource = new UrlResource(f.toURI());
                    return ResponseEntity.ok()
                        .contentType(MediaType.APPLICATION_JSON)
                        .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + resource.getFilename() + "\"")
                        .body(resource);
                }
            }
            log.warn("result/angle 폴더에서 {} 파일을 찾을 수 없음", onlyName);
            return ResponseEntity.notFound().build();
        } catch (MalformedURLException e) {
            log.error("잘못된 파일 경로(json): {}", filename, e);
            return ResponseEntity.badRequest().build();
        }
    }


}
