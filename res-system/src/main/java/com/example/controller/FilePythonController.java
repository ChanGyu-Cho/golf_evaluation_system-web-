package com.example.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.beans.factory.annotation.Autowired;

import jakarta.persistence.EntityManager;
import jakarta.persistence.Query;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.time.LocalDateTime;
import java.sql.Timestamp;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@CrossOrigin
@RequestMapping("/images")
public class FilePythonController {
    private static final Logger log = LoggerFactory.getLogger(FilePythonController.class);

    @Autowired
    private EntityManager entityManager;

    @Value("${video.upload-dir}")
    private String uploadDir;

    @PostMapping("/upload")
    @Transactional
    public ResponseEntity<?> handleVideoUpload(@RequestParam("file") MultipartFile file,
                                               @RequestParam("userid") String userId) {
        try {
            String originalFilename = file.getOriginalFilename();
            String prefixedFilename = userId + "_" + originalFilename;
            String uniqueFilename = getUniqueFilename(uploadDir, prefixedFilename);

            File savedFile = new File(uploadDir, uniqueFilename);
            file.transferTo(savedFile);


            // 분석 결과 JSON 파일 경로 지정 (항상 resPy/result/에서 읽기)
            String resultJsonName = "result_" + uniqueFilename + ".json";
            File resultJsonFile = new File("D:/golf_evaluation_system-web-/resPy/result", resultJsonName);

            // Python 전체 분석 파이프라인 호출
            ProcessBuilder pb = new ProcessBuilder(
                "python",
                "D:/golf_evaluation_system-web-/resPy/analyze_golf_video.py",
                "--video", savedFile.getAbsolutePath(),
                "--out", resultJsonFile.getAbsolutePath(), // result 폴더로 넘김
                "--user", userId
            );
            // Prepare logs directory and per-run log file
            File logsDir = new File("D:/golf_evaluation_system-web-/resPy/result/logs");
            logsDir.mkdirs();
            File pyLogFile = new File(logsDir, "analyze_" + System.currentTimeMillis() + ".log");

            // Start process without redirecting output so we can capture both streams
            pb.redirectErrorStream(false);
            Process process = pb.start();

            // Capture stdout/stderr into the log file while keeping a short in-memory preview
            final StringBuilder pythonLogPreview = new StringBuilder();
            final int PREVIEW_LIMIT = 64 * 1024; // keep up to 64KB in memory for quick error messages

            Thread stdoutPump = new Thread(() -> {
                try (BufferedReader r = new BufferedReader(new InputStreamReader(process.getInputStream(), java.nio.charset.StandardCharsets.UTF_8));
                     BufferedWriter w = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(pyLogFile, true), java.nio.charset.StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = r.readLine()) != null) {
                        w.write(line);
                        w.newLine();
                        w.flush();
                        synchronized (pythonLogPreview) {
                            if (pythonLogPreview.length() < PREVIEW_LIMIT) {
                                pythonLogPreview.append(line).append('\n');
                            }
                        }
                        log.info("[PythonAnalyze-STDOUT] {}", line);
                    }
                } catch (Exception ex) {
                    log.warn("Error while reading python stdout", ex);
                }
            }, "py-stdout-pump");

            Thread stderrPump = new Thread(() -> {
                try (BufferedReader r = new BufferedReader(new InputStreamReader(process.getErrorStream(), java.nio.charset.StandardCharsets.UTF_8));
                     BufferedWriter w = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(pyLogFile, true), java.nio.charset.StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = r.readLine()) != null) {
                        w.write(line);
                        w.newLine();
                        w.flush();
                        synchronized (pythonLogPreview) {
                            if (pythonLogPreview.length() < PREVIEW_LIMIT) {
                                pythonLogPreview.append(line).append('\n');
                            }
                        }
                        log.info("[PythonAnalyze-STDERR] {}", line);
                    }
                } catch (Exception ex) {
                    log.warn("Error while reading python stderr", ex);
                }
            }, "py-stderr-pump");

            stdoutPump.setDaemon(true);
            stderrPump.setDaemon(true);
            stdoutPump.start();
            stderrPump.start();

            // wait with timeout (e.g., 10 minutes)
            boolean finished = process.waitFor(10, java.util.concurrent.TimeUnit.MINUTES);
            int exit = finished ? process.exitValue() : -1;
            if (!finished) {
                process.destroyForcibly();
            }

            // Give pumps a moment to flush
            try { stdoutPump.join(2000); } catch (InterruptedException ignored) {}
            try { stderrPump.join(2000); } catch (InterruptedException ignored) {}

            String pythonLog = null;
            synchronized (pythonLogPreview) { pythonLog = pythonLogPreview.toString(); }

            if (exit != 0) {
                String logMsg = "Python analyze_golf_video.py failed (exit=" + exit + ")\n" + pythonLog;
                log.error(logMsg);
                String userMsg = finished ? ("Python 분석 실패: " + pythonLog) : ("Python 분석 타임아웃. 로그: " + pyLogFile.getAbsolutePath());
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                        .body(userMsg);
            }

            // 결과 JSON 파싱 — 존재하지 않으면 result 폴더에서 유사 파일명으로 대체 검색
            ObjectMapper mapper = new ObjectMapper();
            File finalResultFile = resultJsonFile;
            if (!resultJsonFile.exists()) {
                // try fuzzy match: find any file in result dir that contains the base name
                File resultDir = new File("D:/golf_evaluation_system-web-/resPy/result");
                if (resultDir.exists() && resultDir.isDirectory()) {
                    File[] files = resultDir.listFiles();
                    if (files != null) {
                        String baseNoExt = uniqueFilename.contains(".") ? uniqueFilename.substring(0, uniqueFilename.lastIndexOf('.')) : uniqueFilename;
                        File best = null;
                        for (File f : files) {
                            if (f.getName().contains(baseNoExt)) {
                                if (best == null || f.lastModified() > best.lastModified()) best = f;
                            }
                        }
                        if (best != null) {
                            log.info("Fallback: using result file {} for expected {}", best.getName(), resultJsonFile.getName());
                            finalResultFile = best;
                        }
                    }
                }
            }
            if (!finalResultFile.exists()) {
                throw new FileNotFoundException("Result JSON not found: " + resultJsonFile.getAbsolutePath());
            }
            JsonNode result = mapper.readTree(finalResultFile);

            // 에러 발생 시: 기존 'error' 키와 새로 추가한 status=='error'를 모두 처리
            boolean pyError = result.has("error") || (result.has("status") && "error".equals(result.path("status").asText(null)));
            if (pyError) {
                String errMsg = null;
                if (result.has("error")) errMsg = result.get("error").asText();
                else if (result.has("traceback")) errMsg = result.get("traceback").asText();
                else errMsg = "Unknown Python error";
                log.error("Python error (from result JSON): " + errMsg);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Python 분석 실패: " + errMsg);
            }

            // 필요한 정보 추출
            // openpose_skeleton_video_h264 경로에서 파일명만 추출 (안전하게 접근)
            String openposeSkeletonVideoH264Full = result.path("openpose_skeleton_video_h264").asText(null);
            String openposeSkeletonVideoH264 = openposeSkeletonVideoH264Full == null ? null : new File(openposeSkeletonVideoH264Full).getName();
            // mlp_result 내부 값은 안전하게 읽기(mlp_result가 없을 경우 기본값)
            JsonNode mlpNode = result.path("mlp_result");
            int pred = mlpNode.has("pred") && !mlpNode.get("pred").isNull() ? mlpNode.get("pred").asInt() : -1;
            double probTrue = mlpNode.has("prob_true") && !mlpNode.get("prob_true").isNull() ? mlpNode.get("prob_true").asDouble() : Double.NaN;
            double probFalse = mlpNode.has("prob_false") && !mlpNode.get("prob_false").isNull() ? mlpNode.get("prob_false").asDouble() : Double.NaN;

            Timestamp uploadTime = Timestamp.valueOf(LocalDateTime.now());

            String insertSql = "INSERT INTO video (userid, vid_name, eval, upload_date) VALUES (?, ?, ?, ?)";
            Query insertQuery = entityManager.createNativeQuery(insertSql);
            insertQuery.setParameter(1, userId);
            insertQuery.setParameter(2, uniqueFilename);
            insertQuery.setParameter(3, pred);
            insertQuery.setParameter(4, uploadTime);
            insertQuery.executeUpdate();

            String classifyResult = (pred == 1) ? "Good" : (pred == 0 ? "Bad" : "unknown");

            // 응답: result에는 result JSON 파일명(result_...json)을 넣어 프론트가 곧바로 불러오게 함.
            String resultJsonBasename = resultJsonFile.getName(); // 이미 위에서 만든 이름

        return ResponseEntity.ok().body(new VideoResponse(
            resultJsonBasename,
            openposeSkeletonVideoH264,
            probTrue,
            probFalse,
            classifyResult
        ));
        } catch (Exception e) {
            log.error("파일 업로드 실패: ", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("업로드 실패: " + e.getMessage());
        }
    }

    static class VideoResponse {
        public String result;           // result json basename (result_...json)
        public String skeletonVideo;    // skeleton video filename (for frontend compatibility)
        public double probTrue;
        public double probFalse;
        public String classifyResult;

        public VideoResponse(String result, String skeletonVideo, double probTrue, double probFalse, String classifyResult) {
            this.result = result;
            this.skeletonVideo = skeletonVideo;
            this.probTrue = probTrue;
            this.probFalse = probFalse;
            this.classifyResult = classifyResult;
        }
    }

    private String getUniqueFilename(String directory, String filename) {
        File file = new File(directory, filename);
        String name = filename;
        String baseName = filename.contains(".") ? filename.substring(0, filename.lastIndexOf('.')) : filename;
        String extension = filename.contains(".") ? filename.substring(filename.lastIndexOf('.')) : "";
        int counter = 1;

        while (file.exists()) {
            name = baseName + "_" + counter + extension;
            file = new File(directory, name);
            counter++;
        }
        return name;
    }
}