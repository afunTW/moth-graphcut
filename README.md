# moth-graphcut

協助使用 ThermalCAM 軟體取得生物溫度之後, 想要取得各部位溫度的需求

**原圖**

<img src="https://user-images.githubusercontent.com/4820492/32762156-a3b0a968-c932-11e7-8d89-91c2c10594d0.jpg" alt="0" width="300">

**灰階溫度圖**

<img src="https://user-images.githubusercontent.com/4820492/32762178-ca574496-c932-11e7-84e0-eb37a3fbbcfb.png" alt="0" width="300">

**最終結果**

<img src="https://user-images.githubusercontent.com/4820492/32762244-3fae10d0-c933-11e7-9a0a-5f7de58f5b0d.png" alt="0" width="300"><img src="https://user-images.githubusercontent.com/4820492/32762247-431041c6-c933-11e7-9c89-c20a285ca7fb.png" alt="0" width="300"><img src="https://user-images.githubusercontent.com/4820492/32762207-00c55aea-c933-11e7-9b23-1fc3d397be5b.png" alt="0" width="300"><img src="https://user-images.githubusercontent.com/4820492/32762230-28d0ffee-c933-11e7-91ec-412092bd9203.png" alt="0" width="300"><img src="https://user-images.githubusercontent.com/4820492/32762219-14b91ef6-c933-11e7-98c3-e8fee919d9b3.png" alt="0" width="300">

## Requirement

### .SEQ to .txt

透過 ThermalCAM API 可以將他們自己的 .SEQ 檔案轉檔變成 .txt
格式會是一個透過逗號分隔的溫度矩陣, 每個 cell 都是一個攝氏溫度值

### .txt to image

為了後面要透過 OpenCV 演算法將兩種圖片做 alignment, 必須要再將文字檔轉成圖片
這邊可以參考 [ThermalCAM-converter](https://github.com/afunTW/ThermalCAM-converter)

## Workflow

<img src="https://user-images.githubusercontent.com/4820492/32761759-1b846aea-c930-11e7-9021-3de7c65c6c2d.png" alt="0" width="600">

### Step 1: Graphcut

- 可批次處理
- 分為瀏覽模式與編輯模式
- 可選擇是否透過 Floodfill 演算法去背
- 可選擇是否透過調整 gamma 調整對比
- 可選擇 threshold 來調整 output
- 可透過 'h' 來檢視詳細命令
- 存檔會以原始檔名新增資料夾, 儲存各部位切割檔與 metadata
- 相容於 [dearlep](http://dearlep.tw/) 資料

<img src="https://user-images.githubusercontent.com/4820492/32762031-ec1bcf80-c931-11e7-9f88-5e58b8f261a7.png" alt="0" width="600">

<img src="https://user-images.githubusercontent.com/4820492/32762130-819cd7f2-c932-11e7-89e8-5b0621564944.png" alt="0" width="600">

### Step 2: alignment and mapping

- 載入原始圖片與灰階溫度圖
- 預載自動修正的結果
- 可選擇手動標記

<img src="https://user-images.githubusercontent.com/4820492/32762753-3cc84b9e-c936-11e7-9c7d-52e3109a506a.png" alt="0" width="600">

### Step 3: component mapping

- 給予溫度檔資料夾
- 給予部位原圖資料夾
- 給予轉換矩陣
- 給予輪廓資訊
- 可選擇是否要輸出圖片當作檢查
- 可選擇每個部位的輸出檔案類型為 `.npy` `.dat` `.txt`

## Metadata format

```
{
  "image": {
    "symmetry": [],
    "timestamp": "",
    "l_track": [],
    "r_track": [],
    "size": [],
    "path": "",
    "body_width": int
  },
  "fl": {
    "rect": [],
    "threshold_option": "",
    "threshold": int,
    "cnts": []
  },
  "fr": {
    "rect": [],
    "threshold_option": "",
    "threshold": int,
    "cnts": []
  },
  "bl": {
    "rect": [],
    "threshold_option": "",
    "threshold": int,
    "cnts": []
  },
  "br": {
    "rect": [],
    "threshold_option": "",
    "threshold": int,
    "cnts": []
  },
  "body": {
    "rect": [],
    "threshold_option": "",
    "threshold": int,
    "cnts": []
  }
}
```

## Cited By
* demo images from [dearlep](http://dearlep.tw/)
* interactivate grabcut from [opencv](https://github.com/opencv/opencv/blob/master/samples/python/grabcut.py)
