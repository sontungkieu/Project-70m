import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:firebase_storage/firebase_storage.dart' as firebase_storage;
import 'package:http/http.dart' as http;
import '../widgets/side_drawer.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:convert';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:firebase_storage/firebase_storage.dart' as firebase_storage;
import 'package:http/http.dart' as http;
import 'package:flutter/material.dart';


class SchedulePage extends StatefulWidget {
  const SchedulePage({Key? key}) : super(key: key);

  @override
  State<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends State<SchedulePage> with SingleTickerProviderStateMixin {
  bool isProcessing = false;
  bool isGenerated = false;
  String? uploadedExcelUrl; // URL của file Excel đã upload
  String? generatedJsonUrl; // URL của file JSON kết quả

  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();

    // Khởi tạo AnimationController cho hiệu ứng mờ/slide
    _controller = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );
    _slideAnimation = Tween<Offset>(begin: const Offset(0, 0.1), end: Offset.zero).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

Future<void> _uploadExcelAndRun() async {
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
    final firebase_storage.Reference storageRef = firebase_storage.FirebaseStorage.instance
        .ref('gs://logistic-project-30dcd.firebasestorage.app/requests_xlsx/$fileName');
    await storageRef.putData(
      fileBytes,
      firebase_storage.SettableMetadata(
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      ),
    );
    // Lấy download URL của file Excel
    final String downloadUrl = await storageRef.getDownloadURL();
    
    // Tạo job_id ví dụ sử dụng timestamp
    final String jobId = DateTime.now().millisecondsSinceEpoch.toString();

    // Gửi HTTP request tới backend để chạy thuật toán OR-Tools
    final response = await http.post(
      Uri.parse('https://602f-202-191-58-161.ngrok-free.app/optimize'),   
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "job_id": jobId,
        "excel_url": downloadUrl,
      }),
    );

    if (response.statusCode == 200) {
    final responseData = jsonDecode(response.body);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("Algorithm triggered successfully. Job ID: ${responseData['job_id']}"),
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
  } on firebase_storage.FirebaseException catch (e) {
    // Debug chi tiết lỗi của Firebase Storage
    print("Firebase Storage Error: ${e.code} - ${e.message}");
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("Upload failed: ${e.code} - ${e.message}"),
        backgroundColor: Colors.red,
      ),
    );
  } catch (e) {
    print("General error: $e");
    ScaffoldMessenger.of(context).showSnackBar(

      SnackBar(
        content: Text("Upload failed: $e - $fileName"),
        backgroundColor: Colors.red,
      ),
    );
  }
}



  // ==================== Nút 2: Download JSON Result ====================
  Future<void> _downloadResultJson() async {
    try {
      // Giả sử file JSON được backend lưu tại: 'requests_xlsx/outputs/route_result.json'
      final firebase_storage.Reference jsonRef = firebase_storage.FirebaseStorage.instance
          .ref('requests_xlsx/outputs/route_result.json');
      final String url = await jsonRef.getDownloadURL();
      setState(() {
        generatedJsonUrl = url;
      });
      // Sử dụng url_launcher để mở URL (trình duyệt download file)
      if (await canLaunchUrl(Uri.parse(url))) {
        await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
      } else {
        throw "Could not launch URL";
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Error downloading JSON: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // ==================== Nút 3: Upload Edited JSON ====================
  Future<void> _uploadEditedJson() async {
    // Chọn file JSON đã chỉnh sửa
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['json'],
    );
    if (result == null || result.files.isEmpty) return;

    final Uint8List? fileBytes = result.files.single.bytes;
    final String fileName = result.files.single.name;
    if (fileBytes == null) return;

    try {
      // Upload file JSON lên Firebase Storage (ví dụ: 'requests_xlsx/outputs/edited_result.json')
      final firebase_storage.Reference storageRef = firebase_storage.FirebaseStorage.instance
          .ref('requests_xlsx/outputs/edited_result.json');
      await storageRef.putData(
        fileBytes,
        firebase_storage.SettableMetadata(
          contentType: 'application/json',
        ),
      );
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Edited JSON uploaded successfully"),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Failed to upload edited JSON: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // ==================== UI Build ====================
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
      body: SingleChildScrollView(
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
                          const Icon(Icons.file_upload, size: 40, color: Colors.black54),
                          const SizedBox(height: 8),
                          ElevatedButton(
                            onPressed: _uploadExcelAndRun,
                            child: const Text("Upload Excel File & Run Algorithm"),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.black,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // Khu vực Generate Schedule (hiển thị trạng thái processing)
                _buildCard(
                  title: "Generate Schedule",
                  child: SizedBox(
                    height: 100,
                    child: Center(
                      child: ElevatedButton.icon(
                        onPressed: isProcessing
                            ? null
                            : () {
                                setState(() {
                                  isProcessing = true;
                                });
                                // Giả lập gọi backend: ở đây bạn có thể gọi API nếu cần
                                Future.delayed(const Duration(seconds: 2), () {
                                  setState(() {
                                    isProcessing = false;
                                    isGenerated = true;
                                  });
                                });
                              },
                        icon: const Icon(Icons.schedule),
                        label: isProcessing
                            ? const Text("Processing...")
                            : const Text("Generate Schedule"),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.black,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // Khu vực Download Schedule
                _buildCard(
                  title: "Download Schedule",
                  child: SizedBox(
                    height: 100,
                    child: Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (isGenerated)
                            const Text(
                              "Schedule generated successfully!",
                              style: TextStyle(fontWeight: FontWeight.w500),
                            ),
                          const SizedBox(height: 8),
                          ElevatedButton(
                            onPressed: isGenerated ? _downloadResultJson : null,
                            child: const Text("Download JSON Schedule"),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.black,
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
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
                        child: const Text("Upload Edited JSON"),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.black,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
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
