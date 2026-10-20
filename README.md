# AwakeGuard – Nhận diện dấu hiệu buồn ngủ và cảnh báo qua webcam

**Mã nguồn:** [github.com/dtc245180018-gif/AwakeGuard](https://github.com/dtc245180018-gif/AwakeGuard)

Đồ án trí tuệ nhân tạo ở mức **sinh viên đại học** (Python, thị giác máy tính và học máy). Dự án bao gồm **mô hình nhận diện mắt đã huấn luyện sẵn**, bộ phát hiện tư thế đầu, cảnh báo âm thanh, giao diện **tiếng Việt có dấu**, công cụ huấn luyện lại và các bài kiểm thử. Chạy trên **Windows 10/11 64-bit** với webcam và Python 3.12; không yêu cầu GPU.

> **Chỉ phục vụ học tập, KHÔNG sử dụng làm thiết bị an toàn khi lái xe.** Phần mềm theo dõi *mắt nhắm kéo dài, gật/cúi đầu, đầu hạ xuống và khuôn mặt biến mất khỏi camera*; không xác định chắc chắn người lái đang buồn ngủ. Có thể cảnh báo sai hoặc bỏ sót, nhất là trong ánh sáng yếu, đeo kính, nhìn xuống/bên cạnh, camera rung hoặc góc quay không phù hợp. **Chỉ thử nghiệm khi xe đang đỗ; không cố nhắm mắt/gục đầu lúc lái xe.**

## 1. Cài đặt và chạy trên Windows 10/11

### Bước 1: Tải dự án

**Cách A – dùng Git (khuyên dùng):** Mở PowerShell trong thư mục muốn lưu dự án và nhập:

```powershell
git clone https://github.com/dtc245180018-gif/AwakeGuard.git
cd AwakeGuard
```

**Cách B – không cần Git:** Mở trang GitHub ở trên, chọn **Code → Download ZIP**, giải nén **toàn bộ** thư mục, mở PowerShell tại thư mục có file `app.py` và `cai_dat_windows.bat`.

### Bước 2: Cài Python và thư viện

1. Cài **Python 3.12 64-bit** từ [python.org](https://www.python.org/downloads/); bật `pip`, `py launcher` và tùy chọn `Add python.exe to PATH` nếu có.
2. Kiểm tra trong PowerShell:

   ```powershell
   py -3.12 --version
   ```

3. Tại **thư mục dự án chứa `app.py`**, chạy:

   ```powershell
   .\cai_dat_windows.bat
   ```

   File sẽ tạo `.venv` và cài các gói từ `requirements.txt`. Lần đầu cần Internet và có thể mất vài phút.

   **Chú ý:** Trong PowerShell, phải có `.\` trước tên file `.bat` nằm tại thư mục hiện tại. Nếu vẫn báo *not recognized*, hãy chạy `dir` để kiểm tra bạn đang ở đúng thư mục chưa.

### Bước 3: Mở camera

1. Vào **Windows Settings → Privacy (hoặc Privacy & security) → Camera**, bật quyền dùng camera và cho phép **desktop apps** truy cập.
2. Tại thư mục chứa `app.py`, chạy:

   ```powershell
   .\chay_camera_windows.bat
   ```

3. **Ngồi thẳng, nhìn về phía trước và giữ yên 1,5–2 giây**. Đợi bảng thông tin hiện **`Tư thế: ĐÃ HIỆU CHỈNH`**. Nếu cử động, bộ hiệu chỉnh sẽ thu mẫu lại.
4. Nếu **đổi vị trí camera, chỉnh ghế hoặc đổi người thử**, hãy ngồi thẳng rồi nhấn **`C`** để lấy tư thế chuẩn mới.

**Mở thủ công nếu file `.bat` lỗi:**

```powershell
.\.venv\Scripts\python.exe app.py
```

Các mô hình cần thiết đều đi kèm trong `models/`, nên **không phải tải dữ liệu hoặc huấn luyện lại** để chạy thử.

**Để thử gục đầu**: hãy ngồi ở bàn/ghế khi không điều khiển phương tiện. Sau khi thấy **`Tư thế: ĐÃ HIỆU CHỈNH`**, thử cúi đầu rõ rệt và giữ vài giây. Nếu chỉ nhìn xuống mà đầu không thực sự hạ xuống, hệ thống có thể chưa cảnh báo. Khi mặt ra khỏi khung hình quá lâu, phần mềm sẽ báo **Mất dấu khuôn mặt** (không đồng nghĩa chắc chắn với ngủ gật).

### Phím điều khiển

| Phím | Chức năng |
|---|---|
| `Q` hoặc `Esc` | Thoát |
| `M` | Bật/tắt tiếng cảnh báo |
| `C` | Hiệu chỉnh lại tư thế đầu khi đang ngồi thẳng |
| `V` | Chuyển quy tắc báo đầu cúi: **Cân bằng / Theo mắt** |
| `[` | Hạ ngưỡng, cảnh báo nhạy hơn |
| `]` | Tăng ngưỡng, cảnh báo ít nhạy hơn |
| `Space` | Lưu mẫu mắt (chỉ trong chế độ thu dữ liệu) |

### Các trạng thái bằng tiếng Việt

| Trên giao diện | Giải thích |
|---|---|
| **ĐANG HIỆU CHỈNH** | Đang lấy tư thế ngồi thẳng để làm mốc |
| **BÌNH THƯỜNG** | Chưa nhận thấy dấu hiệu vượt ngưỡng; **không đảm bảo người dùng đang tỉnh táo** |
| **ĐANG NHÌN XUỐNG** | Đầu cúi vừa, mắt vẫn được nhận diện là mở; chưa bật còi chỉ vì cúi đầu |
| **ĐỔI TƯ THẾ** | Vị trí đầu thay đổi nhưng chưa đủ dấu hiệu để báo động; nhấn `C` khi đã đổi ghế/camera |
| **ĐẦU CÚI SÂU** | Đang theo dõi tư thế đầu cúi/hạ, chờ đủ thời gian để quyết định |
| **MẮT ĐANG NHẮM** | Phát hiện mắt nhắm, chưa chắc đã đủ 1,5 giây để cảnh báo |
| **CHƯA RÕ TRẠNG THÁI MẮT** | Chưa suy luận được trạng thái mắt |
| **KHÔNG THẤY MẶT** | Không phát hiện khuôn mặt trong khung hình |
| **CẢNH BÁO!** | Một hoặc nhiều ngưỡng đã bị vượt; nguyên nhân sẽ hiển thị tiếng Việt bên dưới |

Các nguyên nhân cảnh báo hiển thị: **Nhắm mắt quá lâu**, **Gật/cúi đầu bất thường**, **Đầu gục xuống sâu** hoặc **Mất dấu khuôn mặt**.

**Ngưỡng mặc định:**

- **Mắt nhắm liên tục 1,5 giây**: cảnh báo **Nhắm mắt quá lâu**.
- **Mắt nhắm và cúi đầu vừa**: góc cúi thêm từ 17°, hoặc đầu hạ từ 0,33 chiều cao khuôn mặt kèm góc cúi từ 8°, giữ 1 giây: cảnh báo **Gật/cúi đầu bất thường** hoặc **Đầu gục xuống sâu**.
- **Mắt vẫn mở nhưng đầu gục rất sâu/kéo dài**: góc cúi thêm từ 35° **hoặc** đầu hạ từ 0,95 chiều cao khuôn mặt, giữ liên tục 2,5 giây: cảnh báo tư thế đầu (vẫn có thể báo nhầm khi cố ý cúi sâu).
- **Khuôn mặt mất khỏi camera 1,6 giây** sau khi đã được nhận diện ổn định: **Mất dấu khuôn mặt** (không có nghĩa chắc chắn đang ngủ).
- **Mắt mở và cúi mức vừa**: hiển thị **ĐANG NHÌN XUỐNG**, **không phát còi** chỉ vì cúi đầu.

Các ngưỡng chỉ là giá trị thử nghiệm, không phải độ nhạy được kiểm định trên người lái. Phần mềm không thể chắc chắn phân biệt gục ngủ với cố ý nhìn xuống chỉ bằng ảnh khuôn mặt.

**Hai quy tắc phát hiện đầu cúi (nhấn `V` để chuyển ngay khi chạy):**

- **Cân bằng** (`balanced`, mặc định): vẫn báo động nếu đầu gục **rất sâu và kéo dài**, ngay cả khi mắt đang được nhận diện là mở. Có thể báo nhầm khi chủ động cúi xuống quá lâu.
- **Theo mắt** (`eyes_confirmed`): **không phát cảnh báo vì đầu cúi nếu mô hình vẫn nhận diện mắt mở**; chỉ dùng góc/độ hạ đầu để bổ sung cho trạng thái mắt nhắm. Cảnh báo mất khuôn mặt vẫn độc lập. Chế độ này có thể **bỏ sót** người thật sự gục nhưng mắt vẫn được mô hình dự đoán là mở.

## 2. Cách hoạt động

1. **MediaPipe Face Landmarker**: xác định khuôn mặt, các điểm mốc ở mắt và ma trận tư thế đầu từ webcam.
2. **Trích xuất ảnh mắt**: căn chỉnh, cắt riêng hai mắt rồi chuyển thành ảnh xám.
3. **Mô hình HOG + SVM**: dự đoán xác suất mắt nhắm / mở; đây là phần **đã được huấn luyện từ dữ liệu thật**.
4. **Kết hợp thông tin hình học mắt (EAR)**: hạn chế phụ thuộc hoàn toàn vào ảnh hồng ngoại dùng khi huấn luyện.
5. **Hiệu chỉnh tư thế đầu riêng cho người/camera**: lấy góc cúi và độ cao vị trí mũi khi ngồi thẳng, kiểm tra các mẫu có ổn định trước khi lưu tư thế chuẩn. Sau đó theo dõi:
   - Góc đầu cúi thêm so với tư thế chuẩn (`Nod`, đơn vị độ).
   - Đầu hạ thấp trong khung hình (`Drop`, đơn vị chiều cao mặt ban đầu), nhưng chỉ báo động với mức hạ vừa khi có thêm dấu hiệu cúi đầu **và mắt nhắm**, hoặc mức hạ rất sâu liên tục.
   - `POSTURE SHIFT` khi người dùng chỉ đổi vị trí ngồi mà không có góc cúi đáng kể; gợi ý hiệu chỉnh bằng `C` thay vì bật còi liên tục.
   - `LOOKING DOWN` khi người dùng cúi nhìn nhưng mắt vẫn mở, tránh nhầm với dấu hiệu ngủ gật ở mức cúi vừa.
6. **Phát hiện khuôn mặt biến mất** sau khi đã nhận diện được người ngồi trước camera; đây là dấu hiệu *cần kiểm tra camera/người lái*, không tự chứng minh người đó ngủ.
7. **Tích hợp thời gian và cảnh báo**: chỉ một trong các nhóm dấu hiệu vượt ngưỡng đã nêu trong thời gian yêu cầu là đủ để hiện viền đỏ và phát âm thanh. Các ngưỡng có thể chỉnh trong dòng lệnh; âm thanh được giới hạn tần suất để tránh dồn cảnh báo.

**Phần huấn luyện AI:** HOG+SVM là mô hình nhận diện **mắt**, không phải mô hình học trực tiếp trạng thái ngủ gật. Đầu cúi/gật dùng mô hình Face Landmarker đã huấn luyện sẵn cộng với đo góc và quy tắc thời gian; độ chính xác 91,08% ở mục 3 **không áp dụng** cho phát hiện đầu gục. Chưa có đo lường recall/false-alarm rate trên bộ dữ liệu người lái thực tế.

Camera xử lý **cục bộ trên máy**, không gửi video lên server và không lưu hình ảnh nếu bạn không bật chế độ thu mẫu.

## 3. Dữ liệu và kết quả huấn luyện

- Dữ liệu: **MRL Eye Dataset 2018**, tác giả Media Research Lab, VSB–Technical University of Ostrava, [nguồn gốc](https://mrl.cs.vsb.cz/eyedataset.html).
- Dữ liệu nguồn gồm 84.898 ảnh mắt của 37 người, phân loại mắt mở/nhắm và các điều kiện khác.
- Trong bản huấn luyện giao kèm, lấy **8.323 ảnh** (giới hạn tối đa 130 ảnh cho mỗi trạng thái của từng người để giảm chênh lệch số lượng mẫu).
- **6.575 ảnh** được dùng cho huấn luyện/chọn siêu tham số; **1.748 ảnh** từ các **người tách biệt** dùng làm tập kiểm thử cuối.
- Dùng HOG (540 đặc trưng) + StandardScaler + RBF SVM; thử hai giá trị tham số `C` trên tập validation, rồi huấn luyện lại với tham số tốt nhất.
- **Độ chính xác kiểm thử: 91,08%**; **F1 mắt nhắm: 0,906**.
- Confusion matrix và toàn bộ số liệu: `models/evaluation.json`.

**Lưu ý học thuật**: MRL là ảnh **hồng ngoại**, còn webcam laptop thường là ảnh RGB. Kết quả trên tập MRL **không phải** độ chính xác trên webcam hay độ chính xác phát hiện người buồn ngủ thực sự. Muốn báo cáo chất lượng sử dụng thực tế, cần tự kiểm thử bằng video của nhiều người, ánh sáng, kính, góc mặt và báo cáo riêng.

## 4. Thu thêm dữ liệu trên chính webcam của bạn

Để tăng mức phù hợp với webcam thực tế, bạn có thể thu thêm ảnh từ camera bằng Command Prompt tại thư mục đã giải nén:

```bat
.venv\Scripts\python.exe app.py --collect open
```

Mở mắt tự nhiên, nhấn `Space` nhiều lần (mỗi lần lưu 2 ảnh). Thay đổi góc nhìn và ánh sáng; sau đó nhấn `Q`.

```bat
.venv\Scripts\python.exe app.py --collect closed
```

Nhắm mắt **khi đang ngồi an toàn**, nhấn `Space` nhiều lần; tuyệt đối không làm việc này khi đang lái xe. Nên thu tối thiểu 30–50 ảnh cho mỗi lớp, rồi chạy `train_lai_windows.bat` để huấn luyện lại. File này tự tải dữ liệu MRL gốc (~326 MB) nếu máy chưa có. Kết quả train mới sẽ **ghi đè mô hình mắt mặc định**, vì vậy hãy sao lưu `models/eye_state_svm.joblib` và `models/evaluation.json` trước khi train. Có thể khôi phục bản gốc từ GitHub hoặc ZIP tải ban đầu.

**Quyền riêng tư**: ảnh bạn tự thu nằm tại `data/custom/open/` và `data/custom/closed/` trên máy bạn. Hãy xóa bằng File Explorer nếu không muốn giữ ảnh; không chia sẻ các thư mục này khi chưa được người trong ảnh đồng ý.

## 5. Chạy bằng lệnh / kiểm thử video

```bat
.venv\Scripts\python.exe app.py --camera 0
.venv\Scripts\python.exe app.py --seconds 2.0 --mode hybrid
.venv\Scripts\python.exe app.py --mode model
.venv\Scripts\python.exe app.py --mode geometry
.venv\Scripts\python.exe app.py --head-policy eyes_confirmed
.venv\Scripts\python.exe app.py --head-degrees 13 --head-seconds 0.8
.venv\Scripts\python.exe app.py --severe-head-degrees 42 --severe-head-seconds 3.0
.venv\Scripts\python.exe app.py --drop-ratio 0.40 --drop-pitch-degrees 10 --deep-drop-ratio 1.10
.venv\Scripts\python.exe app.py --missing-seconds 2.0
.venv\Scripts\python.exe app.py --video "duong_dan_video.mp4"
.venv\Scripts\python.exe app.py --video "duong_dan_video.mp4" --no-window --max-frames 100 --mute
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Nếu không mở được camera: đóng Zoom/Teams, xem quyền Camera của Windows, hoặc thử `--camera 1`.

Nếu **mắt đang mở nhưng phần mềm vẫn báo**:

1. Xem dòng *nguyên nhân* dưới **CẢNH BÁO!**. **Đầu gục xuống sâu** là cảnh báo về tư thế đầu, **không phải** phân loại mắt nhắm.
2. Ở một ảnh lỗi từng phản ánh: `AI dự đoán nhắm 25,8%`, `EAR 0,358`, `Góc cúi +2,7°`, `Đầu hạ +0,51`. Đây là dịch chuyển vị trí mặt nhẹ đến vừa nhưng chưa có bằng chứng gật đầu; hệ thống hiện tại xử lý thành **ĐỔI TƯ THẾ**, không báo động.
3. Với trường hợp **cúi đầu nhưng vẫn mở to mắt**: giao diện hiện **ĐANG NHÌN XUỐNG** và không tự phát còi với mức cúi vừa. Nếu cúi sâu (từ 35° hoặc hạ 0,95 chiều cao mặt) kéo dài hơn 2,5 giây, vẫn có thể bị cảnh báo ở chế độ **Cân bằng**.
4. Nếu mục tiêu thử nghiệm là **"mắt mở thì tuyệt đối không được báo động do cúi đầu"**, nhấn `V` chuyển sang **Theo mắt** (`eyes_confirmed`). Quy tắc này vẫn báo nhắm mắt kéo dài và mất khuôn mặt, nhưng có thể bỏ sót người gục có mắt mở.
5. Khi chỉnh ghế/camera, hãy ngồi thẳng và nhấn `C`. Nếu vẫn bị nhầm khi cố ý nhìn xuống rất sâu, thử `--severe-head-degrees 42 --severe-head-seconds 3.0` hoặc tăng `--deep-drop-ratio`. Tăng ngưỡng có thể làm **bỏ sót** các tình huống gục đầu thật.

Nếu **cúi/gục nhưng chưa cảnh báo**:

1. Xem màn hình có **Tư thế: ĐÃ HIỆU CHỈNH** chưa; nếu chưa hãy ngồi thẳng, nhìn thẳng và đợi. Nếu đang cúi lúc mở ứng dụng, hãy ngồi thẳng rồi bấm `C`.
2. Đặt camera hơi cao và chếch về mặt người ngồi, thấy rõ đầu/mặt trong tư thế ngồi thẳng và cúi xuống. Đừng đặt quá thấp hoặc quay lệch ngang.
3. Quan sát **Góc cúi** và **Đầu hạ** thay đổi khi cúi. Với mắt mở, hệ thống chỉ báo động đầu gục rất sâu kéo dài; nếu vẫn muốn thử nhận diện nhạy hơn, giảm `--severe-head-degrees` hoặc `--severe-head-seconds` **khi đã hiểu rõ nguy cơ cảnh báo nhầm**. `--head-degrees` điều khiển ngưỡng cúi mức vừa **có kết hợp mắt nhắm**. Nếu đầu hạ mức vừa mà ít cúi, **ĐỔI TƯ THẾ** là dự kiến.
4. Nếu camera không nhìn thấy mặt, cảnh báo **Mất dấu khuôn mặt** chỉ hiện sau khoảng 1,6 giây và chỉ sau khi đã nhận diện mặt ổn định. Nếu đang ở ngoài khung ngay từ lúc khởi động, hệ thống không thể xác định đó là người lái bị gục.
5. Nếu mặt, mắt vẫn hiện nhưng các chỉ số **Góc cúi/Đầu hạ** không thay đổi đúng theo chuyển động thật, hãy quay đoạn video **khi xe đỗ và người thử đồng ý** để kiểm tra góc quay, ánh sáng và tinh chỉnh cho camera đó.

Nếu bị lỗi cài gói trên Windows: kiểm tra đúng Python 3.12 **64-bit**, phiên bản hệ điều hành, kết nối Internet; chạy lại `cai_dat_windows.bat` và gửi lại toàn bộ dòng lỗi.

## 6. Cấu trúc dự án

| File | Mục đích |
|---|---|
| `app.py` | Chạy webcam, phân loại, cảnh báo, giao diện, thu ảnh tùy chọn |
| `vi_text.py` | Vẽ tiếng Việt có dấu bằng font Unicode trên OpenCV |
| `eye_features.py` | Đặc trưng HOG, tính EAR và cắt ảnh mắt |
| `alerting.py` | Bộ đếm thời gian và thời gian chờ giữa các cảnh báo |
| `head_monitor.py` | Đo góc gật từ ma trận đầu, tự hiệu chỉnh, phát hiện đầu hạ/mất mặt, kết hợp các cảnh báo |
| `train.py` | Chia dữ liệu theo người, chọn SVM, đánh giá và lưu mô hình |
| `download_data.py` | Tải bộ dữ liệu nguồn MRL (chỉ khi cần train lại) |
| `models/eye_state_svm.joblib` | **Mô hình phân loại mắt đã huấn luyện**, khoảng 5,4 MB |
| `models/face_landmarker.task` | Mô hình tìm điểm mốc khuôn mặt từ Google MediaPipe |
| `models/evaluation.json` | Kết quả kiểm thử mô hình |
| `tests/` | 20 bài kiểm thử cho dữ liệu mắt, tư thế đầu, cảnh báo và hiển thị tiếng Việt |
| `cai_dat_windows.bat` | Tạo môi trường và cài thư viện |
| `chay_camera_windows.bat` | Mở chương trình |
| `train_lai_windows.bat` | Tải dữ liệu nếu cần, huấn luyện lại |

## 7. Lỗi thường gặp và cách khắc phục

| Biểu hiện/lỗi | Nguyên nhân và hướng xử lý |
|---|---|
| **`cai_dat_windows.bat : The term ... is not recognized`** | Trong PowerShell, chạy **`.\cai_dat_windows.bat`** (không bỏ `.\`). Dùng `pwd`, `dir` để chắc chắn bạn ở thư mục chứa file. Sau khi clone phải `cd AwakeGuard`; nếu giải nén ZIP cần mở đúng thư mục con chứa `app.py`. |
| **`\.\cai_dat_windows.bat` vẫn không tìm thấy** | File không ở vị trí hiện tại hoặc chỉ tải riêng lẻ vài file. Dùng `dir *.bat`; chuyển đến thư mục chứa file bằng `cd "C:\duong-dan\AwakeGuard"`. Nếu GitHub ZIP giải nén thành `AwakeGuard-main`, phải vào thư mục này. |
| **`py is not recognized` / `No suitable Python runtime found`** | Cài Python **3.12 64-bit** từ python.org, chọn Python Launcher, mở cửa sổ PowerShell mới, thử `py -0p` và `py -3.12 --version`. Nếu `py` không có nhưng `python --version` là 3.12, tạo venv thủ công bằng `python -m venv .venv`, rồi tiếp tục các lệnh cài dưới đây. |
| **`python` mở Microsoft Store** | Tắt alias `python.exe`/`python3.exe` trong **Settings → Apps → Advanced app settings → App execution aliases**, hoặc chạy qua `py -3.12`. |
| **`No module named 'mediapipe'`, `cv2`, `PIL`, `sklearn` hoặc `joblib`** | Thư viện được cài vào **`.venv`**, không nhất thiết vào Python hệ thống. Chạy lại `.\cai_dat_windows.bat`; luôn khởi động bằng `.\.venv\Scripts\python.exe app.py`. Nếu dùng VS Code, chọn đúng trình thông dịch `.venv\Scripts\python.exe`. |
| **`ERROR: Could not find a version that satisfies the requirement`** | Kiểm tra Windows **64-bit**, Python **3.12**, Internet, proxy và phiên bản `pip`. Chạy `.\.venv\Scripts\python.exe -m pip install --upgrade pip` và `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. Nếu mạng trường học chặn PyPI, thử mạng hợp lệ khác. |
| **`Access is denied` / lỗi tạo `.venv`** | Đóng ứng dụng/VS Code đang giữ môi trường; chuyển dự án đến thư mục cá nhân có quyền ghi (ví dụ `Documents\AwakeGuard`); không cần chạy PowerShell với quyền Admin. Kiểm tra dung lượng ổ cứng và antivirus. |
| **`Không mở được camera/video` hoặc khung hình đen** | Bật quyền Camera của Windows và desktop apps; đóng Zoom/Teams/ứng dụng camera; thử `--camera 1` hoặc `--camera 2`; kiểm tra webcam có hoạt động trong ứng dụng Camera của Windows không. |
| **`Thiếu mô hình: ...eye_state_svm.joblib` hoặc `face_landmarker.task`** | Tải/clone đầy đủ dự án; không chỉ tải `app.py`. Trong `models/` phải có **cả 2 file mô hình**. Nếu file bị phần mềm bảo mật cách ly, kiểm tra nguồn tải và khôi phục file hợp lệ từ repo. |
| **Hiển thị ký tự `?`, ô vuông hoặc lỗi font** | Đảm bảo có font **Segoe UI** hoặc **Arial** trong `C:\Windows\Fonts`, không bỏ `vi_text.py`. Giao diện vẽ bằng Unicode qua Pillow; terminal cũ cần `chcp 65001` (các file `.bat` đã thiết lập sẵn). |
| **Mắt mở nhưng báo buồn ngủ** | Xem nguyên nhân: có thể do **Đầu gục xuống sâu**, **Mất dấu khuôn mặt**, hay mắt bị đo sai. Hiệu chỉnh lại bằng `C`, điều chỉnh ánh sáng, thử `V` chuyển **Theo mắt**; tăng ngưỡng mắt bằng `]` nếu dự đoán mắt nhắm quá cao. Xem phân tích cụ thể ở mục 5. |
| **Gục đầu nhưng không cảnh báo** | Đợi hiệu chỉnh xong trong tư thế ngồi thẳng. Đảm bảo webcam nhìn thấy toàn bộ đầu/mặt và theo dõi chỉ số góc cúi/đầu hạ. Chế độ **Theo mắt** cố ý bỏ qua cúi đầu khi mắt vẫn mở. Để kiểm thử đầu gục sâu, chuyển **Cân bằng**; ngưỡng/giới hạn thời gian có thể chỉnh trong mục 5. |
| **Luôn hiển thị KHÔNG THẤY MẶT** | Cải thiện ánh sáng chiếu phía trước, chỉnh camera ngang/gần tầm mắt, bỏ vật che mặt, đảm bảo chỉ một khuôn mặt rõ; kiểm tra quyền camera. |
| **Không nghe chuông** | Nhấn `M` để bật lại âm thanh; tăng âm lượng Windows, kiểm tra thiết bị xuất âm. Khi chạy với `--mute`, chuông luôn tắt. |
| **Camera giật, máy quá nóng, FPS thấp** | Đóng ứng dụng ngốn CPU, dùng webcam 720p hoặc thấp hơn, cắm sạc và đặt hiệu năng Windows phù hợp. Hệ thống chạy bằng CPU; máy yếu có thể xử lý chậm, khiến thời điểm cảnh báo không ổn định. |
| **`FileNotFoundError` khi mở video** | Dùng đường dẫn đầy đủ và dấu ngoặc kép: `.\.venv\Scripts\python.exe app.py --video "C:\Videos\demo.mp4"`. Video phải tồn tại, codec được OpenCV hỗ trợ. |
| **Tải dữ liệu hoặc huấn luyện lại thất bại** | Dữ liệu MRL gốc ~326 MB, cần đủ dung lượng và Internet. Kiểm tra URL nguồn còn truy cập được. Không cần tải hoặc train lại nếu chỉ chạy bản đã huấn luyện. **Sao lưu mô hình trước khi train**. |
| **Lỗi Linux `libGLESv2.so.2`** | Bản mặc định dành cho Windows; Linux có thể cần thư viện đồ họa hệ thống `libgles2` tương ứng bản phân phối. Lỗi này thuộc môi trường Linux, không phải thiếu mô hình SVM. |

### Cài thủ công khi script bị lỗi

Mở PowerShell tại thư mục dự án:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py --camera 0
```

Không cần dùng `Activate.ps1`, vì vậy tránh được lỗi **PowerShell ExecutionPolicy** chặn kích hoạt môi trường ảo. Nếu đã lỡ chạy `Activate.ps1` và gặp lỗi *running scripts is disabled*, hãy dùng trực tiếp `.\.venv\Scripts\python.exe` như trên.

### Kiểm tra dự án trước khi báo lỗi

```powershell
py -3.12 --version
.\.venv\Scripts\python.exe -m pip --version
.\.venv\Scripts\python.exe app.py --help
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Nếu cần hỗ trợ, hãy cung cấp **thông báo lỗi đầy đủ dạng chữ**, phiên bản Windows, phiên bản Python, cách mở dự án và tình trạng camera. Không đăng dữ liệu cá nhân, video khuôn mặt hoặc mã truy cập riêng tư lên trang báo lỗi công khai.

## 8. Kiểm thử dự án

Để kiểm thử các module mà không cần mở camera:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Bộ kiểm thử hiện có **20 bài**, bao gồm các tình huống từng gây báo nhầm: mắt vẫn mở khi cúi vừa, đầu hạ do đổi tư thế, cảnh báo khi gục sâu, chế độ ưu tiên mắt và hiển thị tiếng Việt có dấu. **Unit test thành công không thay thế được kiểm thử thực tế với nhiều người và điều kiện ánh sáng khác nhau.**

## 9. Đưa dự án lên GitHub từ bản tải về (dành cho chủ kho)

Nếu nhận được **gói dự án kèm thư mục `.git`**, sau khi giải nén hãy mở PowerShell tại thư mục chứa `README.md`, rồi chạy:

```powershell
git remote -v
git status
git push -u origin main
```

`origin` đã được cấu hình trỏ tới `https://github.com/dtc245180018-gif/AwakeGuard.git`. Bạn cần đăng nhập GitHub bằng tài khoản **có quyền ghi** lên kho. Git for Windows thường sử dụng cửa sổ đăng nhập của **Git Credential Manager**; nếu được yêu cầu mật khẩu qua HTTPS, dùng cơ chế token/xác thực hợp lệ theo hướng dẫn của GitHub, không chia sẻ token công khai.

Nếu bạn tải mã nguồn dưới dạng ZIP từ **Code → Download ZIP** của GitHub thì **không có `.git`**, nên cần `git init`, tạo commit và thêm remote trước khi push. Trong trường hợp repo trên GitHub đã có commit khác, hãy đồng bộ và giải quyết xung đột bình thường; **không dùng `git push --force`** để tránh ghi đè dữ liệu.

## 10. Nguồn tham khảo và trách nhiệm sử dụng

- [MRL Eye Dataset (gốc)](https://mrl.cs.vsb.cz/eyedataset.html), tham khảo phương pháp thu và nhãn dữ liệu. **Ảnh gốc không được đưa vào kho GitHub**; trang nguồn chưa nêu rõ giấy phép thương mại, nên cần xin phép nếu sử dụng ngoài phạm vi học tập/nghiên cứu.
- [MediaPipe Face Landmarker (Google)](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/python): nhận diện điểm khuôn mặt và `facial_transformation_matrixes` để ước lượng tư thế đầu. Mô hình `.task` tải từ [địa chỉ của Google](https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task).
- [Dự án Man2Dev](https://github.com/Man2Dev/Drowsiness-Detection) và [dự án Fieldmarshall23](https://github.com/Fieldmarshall23/driver-drowsiness-detection): mã tham khảo công khai, **không sao chép nguyên mẫu** vào ứng dụng này.
- [scikit-learn SVM](https://scikit-learn.org/stable/modules/svm.html): phương pháp huấn luyện bộ phân loại.

Hệ thống **không phù hợp làm thiết bị duy nhất để đảm bảo an toàn giao thông hoặc đánh giá y tế**. Người dùng cần nghỉ ngơi thực sự khi có dấu hiệu mệt mỏi và không dựa vào việc phần mềm có phát cảnh báo hay không.
