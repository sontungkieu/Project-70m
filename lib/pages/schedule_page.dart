import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'dart:html' as html; // Để mở tab mới tải file
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:firebase_storage/firebase_storage.dart' as firebase_storage;
import 'package:http/http.dart' as http;
import '../widgets/side_drawer.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:firebase_storage/firebase_storage.dart' as firebase_storage;
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import 'dart:convert';
import 'dart:html' as html; // Dành cho web
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_storage/firebase_storage.dart' as firebase_storage;

/// Khởi tạo custom FirebaseStorage cho đúng bucket (nếu cần)
final firebase_storage.FirebaseStorage customStorage = firebase_storage
    .FirebaseStorage.instanceFor(
  bucket: 'gs://logistic-project-30dcd.firebasestorage.app',
);

final String ngrok =
    'https://b32a-123-18-225-103.ngrok-free.app/'; // Địa chỉ API của bạn

class ExcelFileList extends StatefulWidget {
  const ExcelFileList({Key? key}) : super(key: key);

  @override
  State<ExcelFileList> createState() => _ExcelFileListState();
}

/// Lớp phụ để lưu cặp (fileRef, creationTime) phục vụ sort
class _FileData {
  final firebase_storage.Reference ref;
  final DateTime lastModified;

  _FileData(this.ref, this.lastModified);
}

class _ExcelFileListState extends State<ExcelFileList>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  /// Danh sách các file tham chiếu sau khi đã lọc
  List<firebase_storage.Reference> _filteredFiles = [];

  /// Biến để theo dõi hover
  int _hoverIndex = -1;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(
      begin: 0,
      end: 1,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeIn));
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    // Lấy danh sách file ngay khi initState
    _fetchExcelFiles();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  /// Hàm lấy danh sách file trong thư mục "expect_schedule"
  /// - Chỉ lấy các file có tên bắt đầu "output_" và kết thúc ".xlsx"
  /// - Lấy những file có lastModified trong 2 ngày gần nhất (48 giờ)
  /// - Sắp xếp theo lastModified giảm dần (file mới nhất lên trước)
  Future<void> _fetchExcelFiles() async {
    try {
      // Trỏ tới thư mục expect_schedule
      final storageRef = customStorage.ref().child('expect_schedule');
      // Lấy danh sách file (không đệ quy)
      final listResult = await storageRef.listAll();

      final List<_FileData> fileDataList = [];

      for (var item in listResult.items) {
        final name = item.name.toLowerCase();

        // Chỉ xét file "output_... .xlsx"
        if (name.startsWith('output_') && name.endsWith('.xlsx')) {
          // Lấy metadata để check lastModified
          final metadata = await item.getMetadata();
          final lastModified = metadata.updated;
          if (lastModified != null) {
            // Kiểm tra nếu trong vòng 48 giờ
            final diffInHours = DateTime.now().difference(lastModified).inHours;
            if (diffInHours <= 48) {
              fileDataList.add(_FileData(item, lastModified));
            }
          }
        }
      }

      // Sắp xếp giảm dần theo lastModified
      fileDataList.sort((a, b) => b.lastModified.compareTo(a.lastModified));

      setState(() {
        _filteredFiles = fileDataList.map((f) => f.ref).toList();
      });

      // Reset & chạy animation sau khi dữ liệu đã sẵn sàng
      _controller.reset();
      _controller.forward();

      debugPrint('Fetched total: ${_filteredFiles.length} files.');
    } catch (e) {
      debugPrint('Error fetching excel files: $e');
    }
  }

  /// Tạo widget cho từng file
  Widget _buildFileItem(int index, firebase_storage.Reference fileRef) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: SlideTransition(
        position: _slideAnimation,
        child: MouseRegion(
          onEnter: (_) => setState(() => _hoverIndex = index),
          onExit: (_) => setState(() => _hoverIndex = -1),
          child: InkWell(
            onTap: () async {
              // Lấy URL download
              final url = await fileRef.getDownloadURL();
              // Mở tab mới (dùng dart:html)
              html.window.open(url, "_blank");
            },
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 6),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _hoverIndex == index ? Colors.grey[200] : Colors.white,
                borderRadius: BorderRadius.circular(8),
                boxShadow:
                    _hoverIndex == index
                        ? [
                          BoxShadow(
                            color: Colors.black26,
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ]
                        : [],
              ),
              child: Row(
                children: [
                  const Icon(Icons.insert_drive_file, color: Colors.green),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      fileRef.name,
                      style: const TextStyle(fontSize: 14),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_filteredFiles.isEmpty) {
      return const Center(
        child: Text(
          "No recent Excel files found.",
          style: TextStyle(color: Colors.grey),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      itemCount: _filteredFiles.length,
      itemBuilder: (context, index) {
        return _buildFileItem(index, _filteredFiles[index]);
      },
    );
  }
}

// ------------------ Trang SchedulePage gốc, đã chỉnh để chia đôi màn hình ------------------
class SchedulePage extends StatefulWidget {
  const SchedulePage({Key? key}) : super(key: key);

  @override
  State<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends State<SchedulePage>
    with SingleTickerProviderStateMixin {
  bool isProcessing = false;
  bool isGenerated = false;
  bool isAlgorithmSuccess = false; // Thêm biến này
  String? uploadedExcelUrl; // URL của file Excel đã upload

  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();

    // Khởi tạo AnimationController cho hiệu ứng mờ/slide (phần logic cũ)
    _controller = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(
      begin: 0,
      end: 1,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeIn));
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.1),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  // ==================== Nút 1: Upload Excel ====================
  Future<void> _uploadExcelFile() async {
    // Mở file picker để chọn file Excel
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['xlsx', 'xls'],
    );
    if (result == null || result.files.isEmpty) return;

    // Lấy dữ liệu file dưới dạng bytes
    final Uint8List? fileBytes = result.files.single.bytes;
    final String fileName = result.files.single.name;
    if (fileBytes == null) return;

    try {
      // Upload file lên Firebase Storage (thư mục "requests_xlsx")
      final firebase_storage.Reference
      storageRef = firebase_storage.FirebaseStorage.instance.ref(
        'gs://logistic-project-30dcd.firebasestorage.app/requests_xlsx/$fileName',
      );
      await storageRef.putData(
        fileBytes,
        firebase_storage.SettableMetadata(
          contentType:
              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ),
      );
      // Lấy download URL của file Excel
      final String downloadUrl = await storageRef.getDownloadURL();

      setState(() {
        uploadedExcelUrl = downloadUrl;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("File uploaded successfully!"),
          backgroundColor: Colors.green,
        ),
      );
    } on firebase_storage.FirebaseException catch (e) {
      debugPrint("Firebase Storage Error: ${e.code} - ${e.message}");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Upload failed: ${e.code} - ${e.message}"),
          backgroundColor: Colors.red,
        ),
      );
    } catch (e) {
      debugPrint("General error: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Upload failed: $e - $fileName"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // ==================== Nút 2: Trigger Algorithm ====================
  Future<void> _triggerAlgorithm() async {
    if (uploadedExcelUrl == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Please upload the Excel file first."),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // Tạo job_id ví dụ sử dụng timestamp
    final String jobId = DateTime.now().millisecondsSinceEpoch.toString();
    try {
      final response = await http.post(
        Uri.parse(ngrok + '/optimize'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"job_id": jobId, "excel_url": uploadedExcelUrl}),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        setState(() {
          isAlgorithmSuccess = true; // Cập nhật trạng thái thành công
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              "Algorithm triggered successfully. Job ID: ${responseData['job_id']}",
            ),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Error triggering algorithm: ${response.body}"),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      debugPrint("Error triggering algorithm: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Error triggering algorithm: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // ==================== Nút 3: Dowload schedule ====================

  Future<void> _downloadTodaySchedule() async {
    try {
      // Tham chiếu đến file trong bucket tùy chỉnh
      final fileRef = customStorage.ref().child(
        'requests_xlsx/Lenh_Dieu_Xe.xlsx',
      );

      // Lấy URL tải file
      final downloadUrl = await fileRef.getDownloadURL();

      // Tạo đối tượng AnchorElement để tải file
      final anchor =
          html.AnchorElement(href: downloadUrl)
            ..target = 'blank'
            ..download = 'Lenh_Dieu_Xe.xlsx';
      html.document.body!.append(anchor);
      anchor.click();
      anchor.remove();

      print('File download initiated.');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đã tải file Lenh_Dieu_Xe.xlsx về thành công!'),
        ),
      );
    } catch (e) {
      print('❌ Lỗi khi tải file: $e');
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Lỗi khi tải file: $e')));
    }
  }

  Future<void> _downloadTomorrowRequests(BuildContext context) async {
    try {
      // Gọi endpoint của backend để tạo file Excel và đẩy lên Firebase Storage
      final response = await http.post(
        Uri.parse(ngrok + '/create_excel'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "day": "tomorrow", // hoặc định dạng ngày bạn muốn
          "is_recreate": true,
        }),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        final downloadUrl = responseData['download_url'];
        // Tạo AnchorElement để tải file trên trình duyệt web
        final anchor =
            html.AnchorElement(href: downloadUrl)
              ..target = 'blank'
              ..download = 'Lenh_Dieu_xe.xlsx';
        html.document.body!.append(anchor);
        anchor.click();
        anchor.remove();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã tải file thành công!')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error creating excel: ${response.body}")),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e"), backgroundColor: Colors.red),
      );
      print('Error: $e');
    }
  }

  // ==================== Nút 4: Upload Excel ====================
  Future<void> _uploadEditedJson() async {
    // Chọn tệp Excel (chỉ cho phép .xlsx và .xls)
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['xlsx', 'xls'],
    );
    if (result == null || result.files.isEmpty) return;

    final Uint8List? fileBytes = result.files.single.bytes;
    String fileName = result.files.single.name;
    if (fileBytes == null) return;

    // Đổi tên tệp nếu cần thiết
    if (fileName.startsWith('output_')) {
      fileName = 'final_output_${fileName.substring(7)}';
    }

    try {
      // Tải tệp Excel lên Firebase Storage trong thư mục "final_schedule"
      final firebase_storage.Reference storageRef = customStorage.ref(
        'final_schedule/$fileName',
      );

      await storageRef.putData(
        fileBytes,
        firebase_storage.SettableMetadata(
          contentType:
              'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ),
      );

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Tệp Excel đã được tải lên thành công"),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Tải lên tệp Excel thất bại: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // ------------------ UI Build ------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const SideDrawer(),
      appBar: AppBar(
        title: const Text('Schedule'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      // Thay vì SingleChildScrollView, ta chia thành 2 cột: trái (logic cũ), phải (danh sách file)
      body: Row(
        children: [
          // Nửa màn hình trái: giữ nguyên logic cũ
          Expanded(
            flex: 1,
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: FadeTransition(
                opacity: _fadeAnimation,
                child: SlideTransition(
                  position: _slideAnimation,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Khu vực Upload Excel & Run Algorithm
                      _buildCard(
                        title: "Upload Transport Requests",
                        child: SizedBox(
                          height: 150,
                          child: Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                // Nút upload Excel
                                ElevatedButton(
                                  onPressed: _uploadExcelFile,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.black,
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 24,
                                      vertical: 16,
                                    ),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                  ),
                                  child: const Text("Upload Excel File"),
                                ),
                                const SizedBox(height: 16),
                                // Nút trigger thuật toán
                                ElevatedButton(
                                  onPressed:
                                      (uploadedExcelUrl != null)
                                          ? _triggerAlgorithm
                                          : null,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.black,
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 24,
                                      vertical: 16,
                                    ),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                  ),
                                  child: const Text("Run Algorithm"),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Card mới thay thế Generate Schedule
                      _buildCard(
                        title: "Download Schedules",
                        child: SizedBox(
                          height: 150,
                          child: Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                // Nút tải về file Excel đơn giao hàng hiện tại
                                ElevatedButton(
                                  onPressed:
                                      _downloadTodaySchedule, // TODO: define function
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.black,
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 24,
                                      vertical: 16,
                                    ),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                  ),
                                  child: const Text(
                                    "Tải về file Excel đơn giao hàng hiện tại",
                                  ),
                                ),
                                const SizedBox(height: 16),
                                // Nút tải file request đơn giao hàng ngày mai
                                ElevatedButton(
                                  onPressed:
                                      () => _downloadTomorrowRequests(
                                        context,
                                      ), // TODO: define function
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.black,
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 24,
                                      vertical: 16,
                                    ),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                  ),
                                  child: const Text(
                                    "Tải file request đơn giao hàng mới ngày mai",
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 16),

                      // Khu vực Upload Edited JSON
                      _buildCard(
                        title: "Upload Edited Schedule",
                        child: SizedBox(
                          height: 100,
                          child: Center(
                            child: ElevatedButton(
                              onPressed: _uploadEditedJson,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.black,
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 24,
                                  vertical: 16,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                              child: const Text("Upload Edited Schedule"),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // Nửa màn hình phải: Danh sách file Excel với tiêu đề
          Expanded(
            flex: 1,
            child: Container(
              color: Colors.grey.shade50,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      "Các lịch chạy xe dự kiến do thuật toán đưa ra gần đây:",
                      style: TextStyle(
                        // Bạn có thể thay đổi thành Theme.of(context).textTheme.headline6 nếu trong build context
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),

                  const Expanded(child: ExcelFileList()),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // Widget helper tạo card
  Widget _buildCard({required String title, required Widget child}) {
    return Card(
      elevation: 0,
      color: Colors.grey.shade50,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            const SizedBox(height: 8),
            child,
          ],
        ),
      ),
    );
  }
}
