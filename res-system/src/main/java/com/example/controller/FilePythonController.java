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

@RestController
@CrossOrigin
@RequestMapping("/images")
public class FilePythonController {
    private static final Logger log = LoggerFactory.getLogger(FilePythonController.class);  // ✅ 여기가 핵심
    @Autowired
    private EntityManager entityManager;

    @Value("${video.upload-dir}")
    private String uploadDir;

    @PostMapping("/upload")
    @Transactional
    public ResponseEntity<?> handleVideoUpload(@RequestParam("file") MultipartFile file,
                                               @RequestParam("userid") int userId) {
        try {
            String originalFilename = file.getOriginalFilename();
            String prefixedFilename = userId + "_" + originalFilename;
            String uniqueFilename = getUniqueFilename(uploadDir, prefixedFilename);

            File savedFile = new File(uploadDir, uniqueFilename);
            file.transferTo(savedFile);

            String skeletonFilename = "skeleton_" + uniqueFilename;
            File skeletonOutput = new File(uploadDir, skeletonFilename);

            runSkeletonVideoProcessor(savedFile.getAbsolutePath(), skeletonOutput.getAbsolutePath());

            int rawResult = Integer.parseInt(runPythonModel(savedFile.getAbsolutePath()));

            String insertSql = "INSERT INTO basvid (user_id, vid_name, eval) VALUES (?, ?, ?)";
            Query insertQuery = entityManager.createNativeQuery(insertSql);
            insertQuery.setParameter(1, userId);
            insertQuery.setParameter(2, uniqueFilename);
            insertQuery.setParameter(3, rawResult);
            insertQuery.executeUpdate();

            String classifyResult;
            if (1 == rawResult) {
                classifyResult = "Good";
            } else if (0 == rawResult) {
                classifyResult = "Bad";
            } else {
                classifyResult = "unknown";
            }

            return ResponseEntity.ok().body(new VideoResponse(
                    classifyResult,
                    skeletonFilename
            ));
        } catch (Exception e) {
            log.info("파일 업로드 실패: ", e);
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


    // Python 분류 모델 실행 후 stdout에서 결과 읽기
    private String runPythonModel(String inputPath) throws IOException, InterruptedException {
        ProcessBuilder pb = new ProcessBuilder("python", "E:/resPy/classify_video.py", inputPath);
        pb.redirectErrorStream(true);
        Process process = pb.start();

        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
        String rawResult = reader.readLine();

        process.waitFor();
        reader.close();
        return rawResult;   // 숫자 라벨 0은 bad, 1은 good
    }

    // runSkeletonVideoProcessor 수정 (jsonPath 인자 추가 및 리턴)
    private String runSkeletonVideoProcessor(String inputPath, String outputPath) throws IOException, InterruptedException {
        // outputPath: "uploaded-videos/파일명.mp4" 라고 가정

        String baseName = new File(outputPath).getName();
        String baseNameNoExt = baseName.contains(".") ? baseName.substring(0, baseName.lastIndexOf('.')) : baseName;

        // relative path from uploaded-videos
        String csvRelPath = "landmarkFiles/" + baseNameNoExt + ".csv";
        String jsonRelPath = "landmarkFiles/" + baseNameNoExt + ".json";

        // landmarkFiles 폴더 존재 여부 확인 및 생성 (uploaded-videos/landmarkFiles)
        File landmarkDir = new File(uploadDir, "landmarkFiles");
        if (!landmarkDir.exists()) {
            landmarkDir.mkdirs();
        }

        // 실제 파일 경로 (절대 경로) 필요시, uploadDir 기준으로 합침
        String csvFullPath = new File(uploadDir, csvRelPath).getAbsolutePath();
        String jsonFullPath = new File(uploadDir, jsonRelPath).getAbsolutePath();

        ProcessBuilder pb = new ProcessBuilder(
                "python",
                "E:/resPy/skeleton_video.py",
                inputPath,
                outputPath,
                csvFullPath,
                jsonFullPath
        );
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

        return jsonRelPath;  // 프론트엔드로 넘겨줄 URL 경로는 상대경로로!
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
