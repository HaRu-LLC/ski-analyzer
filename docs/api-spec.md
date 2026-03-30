# API仕様書

## Base URL

```
http://localhost:8000/api
```

## エンドポイント一覧

### POST /upload

動画をアップロードして解析を開始する。

**Request**: `multipart/form-data`
| Field | Type | Description |
|-------|------|-------------|
| file | File | 動画ファイル (MP4/MOV/WebM, 最大500MB, 最大60秒) |

**Response**: `200 OK`
```json
{
  "analysis_id": "uuid",
  "status": "validating",
  "message": "動画を受け付けました。解析を開始します。"
}
```

**Errors**:
- `400`: ファイル形式/サイズ/解像度/fps/長さの不正

---

### GET /analysis/{id}/status

解析の進捗状況を返す。ポーリング用。

**Response**: `200 OK`
```json
{
  "analysis_id": "uuid",
  "status": "estimating_pose",
  "progress": 45.0,
  "estimated_remaining_seconds": 120,
  "error_message": null
}
```

**status値**: `uploading` → `validating` → `extracting_frames` → `estimating_pose` → `calculating_angles` → `comparing_ideal` → `generating_coaching` → `saving_results` → `rendering_overlay` → `generating_report` → `completed` / `failed`

---

### GET /analysis/{id}/result

解析結果全体を返す。`status: completed` 後に呼び出す。

**Response**: `200 OK`
```json
{
  "analysis_id": "uuid",
  "video_info": { "width": 1920, "height": 1080, "fps": 60, "duration": 30.0, "total_frames": 1800 },
  "total_frames": 1800,
  "frames": [
    {
      "frame_index": 0,
      "timestamp_ms": 0.0,
      "joint_positions_3d": { "l_knee": [0.1, -0.3, 0.5], ... },
      "joint_rotations": { "l_knee": [0.2, 0.1, -0.3], ... },
      "joint_angles": [
        { "joint_name": "l_knee", "joint_name_ja": "左膝", "flexion": -52.3, "rotation": 3.1, "abduction": -2.0, "confidence": "medium" }
      ]
    }
  ],
  "coaching": {
    "overall_score": 72,
    "summary": "全体的にバランスの良いフォームです。膝の曲げをもう少し深くすると安定感が増します。",
    "details": [...]
  },
  "ideal_comparison": [
    { "joint_name": "l_knee", "joint_name_ja": "左膝", "user_angle": -48.5, "ideal_angle": -55.0, "difference": 6.5, "rating": "good" }
  ]
}
```

`agent_trace.json` は内部保存用 artifact であり、このレスポンスには含めない。

---

### GET /analysis/{id}/frames/{frame_index}

特定フレームの解析データのみ返す。軽量取得用。

---

### GET /download/{id}/video

スケルトン重畳済みMP4動画をダウンロード。

**Response**: `application/octet-stream` (MP4)

---

### GET /download/{id}/report

PDFレポートをダウンロード。

**Response**: `application/pdf`

---

### GET /download/{id}/csv

全フレームの関節角度CSVをダウンロード。

**Response**: `text/csv`

**CSV列**: `frame_index, timestamp_ms, joint_name, flexion, rotation, abduction, confidence`
