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

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;

import java.time.LocalDateTime;
import java.sql.Timestamp;

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

            String skeletonFilename = "skeleton_" + uniqueFilename;
            File skeletonOutput = new File(uploadDir, skeletonFilename);

            // 스켈레톤 처리: 절대경로 전달 유지
            runSkeletonVideoProcessor(savedFile.getAbsolutePath(), skeletonOutput.getAbsolutePath());

            // 분류기는 파일 "이름"만 전달 (파이썬이 업로드 디렉토리 붙임)
            int rawResult = runPythonModel(uniqueFilename);

            Timestamp uploadTime = Timestamp.valueOf(LocalDateTime.now());

            String insertSql = "INSERT INTO video (userid, vid_name, eval, upload_date) VALUES (?, ?, ?, ?)";
            Query insertQuery = entityManager.createNativeQuery(insertSql);
            insertQuery.setParameter(1, userId);
            insertQuery.setParameter(2, uniqueFilename);
            insertQuery.setParameter(3, rawResult);
            insertQuery.setParameter(4, uploadTime);
            insertQuery.executeUpdate();

            String classifyResult = (rawResult == 1) ? "Good" : (rawResult == 0 ? "Bad" : "unknown");

            return ResponseEntity.ok().body(new VideoResponse(
                    classifyResult,
                    skeletonFilename
            ));
        } catch (Exception e) {
            log.error("파일 업로드 실패: ", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("업로드 실패");
        }
    }

    static class VideoResponse {
        public String result;
        public String skeletonVideo;

        public VideoResponse(String result, String skeletonVideo) {
            this.result = result;
            this.skeletonVideo = skeletonVideo;
        }
    }

    // Python 분류 모델 실행 (stderr 분리, exit code 체크, 안전 파싱)
    private int runPythonModel(String videoFilename) throws IOException, InterruptedException {
        ProcessBuilder pb = new ProcessBuilder(
                "python",
                "D:/golf_evaluation_system-web-/resPy/classify_video.py",
                videoFilename
        );
        // stderr를 stdout으로 합치지 않음
        Process process = pb.start();

        StringBuilder outBuf = new StringBuilder();
        StringBuilder errBuf = new StringBuilder();

        Thread outThread = new Thread(() -> {
            try (BufferedReader r = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = r.readLine()) != null) outBuf.append(line).append('\n');
            } catch (IOException ignored) {}
        });
        Thread errThread = new Thread(() -> {
            try (BufferedReader r = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
                String line;
                while ((line = r.readLine()) != null) errBuf.append(line).append('\n');
            } catch (IOException ignored) {}
        });

        outThread.start();
        errThread.start();

        int exit = process.waitFor();
        outThread.join();
        errThread.join();

        String stdout = outBuf.toString().trim();
        String stderr = errBuf.toString().trim();

        if (exit != 0) {
            throw new IOException("Python classify failed (exit=" + exit + "): " + stderr);
        }

        // stdout의 마지막 라인에서 0/1만 추출 ("RESULT: 1" 형태도 허용)
        String[] lines = stdout.split("\\R");
        for (int i = lines.length - 1; i >= 0; i--) {
            String s = lines[i].trim();
            if (s.matches("^[01]$")) return Integer.parseInt(s);
            if (s.matches(".*\\b[01]\\b.*")) {
                String digit = s.replaceAll(".*\\b([01])\\b.*", "$1");
                return Integer.parseInt(digit);
            }
        }
        throw new IOException("No numeric result in Python stdout. stdout=[" + stdout + "], stderr=[" + stderr + "]");
    }

    // 스켈레톤 처리 (stderr/stdout 로그 출력, 실패 시 예외)
    private String runSkeletonVideoProcessor(String inputPath, String outputPath) throws IOException, InterruptedException {
        String baseName = new File(outputPath).getName();
        String baseNameNoExt = baseName.contains(".") ? baseName.substring(0, baseName.lastIndexOf('.')) : baseName;

        String csvRelPath = "landmarkFiles/" + baseNameNoExt + ".csv";
        String jsonRelPath = "landmarkFiles/" + baseNameNoExt + ".json";

        File landmarkDir = new File(uploadDir, "landmarkFiles");
        if (!landmarkDir.exists()) {
            landmarkDir.mkdirs();
        }

        String csvFullPath = new File(uploadDir, csvRelPath).getAbsolutePath();
        String jsonFullPath = new File(uploadDir, jsonRelPath).getAbsolutePath();

        ProcessBuilder pb = new ProcessBuilder(
                "python",
                "D:/golf_evaluation_system-web-/resPy/skeleton_video.py",
                inputPath,
                outputPath,
                csvFullPath,
                jsonFullPath
        );
        // 스켈레톤 처리 로그는 합쳐서 한 스트림으로 출력
        pb.redirectErrorStream(true);
        Process process = pb.start();

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println("[SkeletonVideoProcessor] " + line);
            }
        }

        int exitCode = process.waitFor();
        if (exitCode != 0) {
            throw new IOException("Skeleton video processor exited with code " + exitCode);
        }

        return jsonRelPath;
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
