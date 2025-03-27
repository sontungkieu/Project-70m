import 'dart:async';
import 'dart:typed_data';
// Thêm dòng này nếu đang chạy Flutter Web
import 'dart:html' as html;
import 'package:firebase_storage/firebase_storage.dart' as firebase_storage;
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:intl/intl.dart';
// Ẩn Border của package excel để tránh xung đột với Border của Flutter
import 'package:excel/excel.dart' hide Border;
import 'package:firebase_storage/firebase_storage.dart' as firebase_storage;

import '../widgets/side_drawer.dart';

/// Khởi tạo custom FirebaseStorage cho đúng bucket (nếu cần)
final firebase_storage.FirebaseStorage customStorage =
    firebase_storage.FirebaseStorage.instanceFor(
  bucket: 'gs://logistic-project-30dcd.firebasestorage.app',
);

/// Lớp chứa dữ liệu cho Dashboard
class DashboardData {
  final int activeDrivers;
  final int pendingOrders;
  final List<Map<String, dynamic>> todaysOrders;

  DashboardData({
    required this.activeDrivers,
    required this.pendingOrders,
    required this.todaysOrders,
  });
}

class DashboardPage extends StatefulWidget {
  const DashboardPage({Key? key}) : super(key: key);

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage>
    with SingleTickerProviderStateMixin {
  late DateTime _currentTime;
  Timer? _timer;       // Timer 1s để cập nhật thời gian
  Timer? _reloadTimer; // Timer 10 phút để reload future

  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  late Animation<Offset> _cardSlideAnimation;

  // Future chứa dữ liệu Dashboard (Firestore)
  Future<DashboardData>? _dashboardFuture;

  // Future chứa danh sách file Excel (Firebase Storage)
  Future<List<firebase_storage.Reference>>? _excelFilesFuture;

  @override
  void initState() {
    super.initState();

    // Thiết lập thời gian GMT+7 và cập nhật mỗi giây
    _currentTime = DateTime.now().toUtc().add(const Duration(hours: 7));
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        _currentTime = DateTime.now().toUtc().add(const Duration(hours: 7));
      });
    });

    // Khởi tạo animation controller
    _controller = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.1),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
    _cardSlideAnimation = Tween<Offset>(
      begin: const Offset(0, 0.2),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.3, 0.7, curve: Curves.easeOut),
      ),
    );

    _controller.forward();

    // Lần đầu load dữ liệu Dashboard (Firestore)
    _dashboardFuture = fetchDashboardData();

    // Lần đầu load danh sách file Excel (Firebase Storage)
    _excelFilesFuture = fetchLatestExcelFiles();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _reloadTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  /// Lấy dữ liệu Dashboard (Firestore)
  Future<DashboardData> fetchDashboardData() async {
    // 1) active drivers
    final activeSnap = await FirebaseFirestore.instance
        .collection('Drivers')
        .where('available', isEqualTo: true)
        .get();
    final activeCount = activeSnap.size;

    // 2) pending orders
    final pendingSnap = await FirebaseFirestore.instance
        .collection('Requests')
        .where('delivery_status', isEqualTo: false)
        .get();
    final pendingCount = pendingSnap.size;

    // 3) today’s orders
    final now = DateTime.now();
    final startOfToday = DateTime(now.year, now.month, now.day);
    final endOfToday = startOfToday.add(const Duration(days: 1));

    final todaySnap = await FirebaseFirestore.instance
        .collection('Requests')
        .where('date', isGreaterThanOrEqualTo: startOfToday)
        .where('date', isLessThan: endOfToday)
        .get();
    final todayOrders = todaySnap.docs.map((doc) {
      final data = doc.data();
      return {
        'orderId': data['request_id'] ?? '-',
        'driver': data['staff_id'] ?? 'No Driver',
        'deliveryStatus': data['delivery_status'] == true ? 'Delivered' : 'Pending',
        'deliveryTime': data['delivery_time'] ?? '-',
      };
    }).toList();

    return DashboardData(
      activeDrivers: activeCount,
      pendingOrders: pendingCount,
      todaysOrders: todayOrders,
    );
  }

  /// Lấy 5 file Excel mới nhất trong folder 'final_schedule' (Firebase Storage)
  Future<List<firebase_storage.Reference>> fetchLatestExcelFiles() async {
    final folderRef = customStorage.ref().child('final_schedule');

    // Lấy toàn bộ file trong folder
    final result = await folderRef.listAll();
    final allFiles = result.items;

    // Chỉ lấy các file có tên dạng 'output_...xlsx'
    final outputFiles = allFiles.where((fileRef) {
      return fileRef.name.startsWith('output_') &&
          fileRef.name.endsWith('.xlsx');
    }).toList();

    // Parse ngày tháng năm từ tên file, sau đó sắp xếp theo ngày giảm dần
    outputFiles.sort((a, b) {
      final dateA = _parseDateFromFileName(a.name);
      final dateB = _parseDateFromFileName(b.name);
      return dateB.compareTo(dateA);
    });

    // Lấy 5 file mới nhất
    return outputFiles.take(5).toList();
  }

DateTime _parseDateFromFileName(String fileName) {
  // Loại bỏ tiền tố "output_" và hậu tố ".xlsx"
  final nameWithoutPrefix = fileName.replaceAll('output_', '').replaceAll('.xlsx', '');
  
  // Xác định ký tự phân cách: nếu chứa "_" thì dùng "_" ngược lại nếu chứa "-" thì dùng "-"
  List<String> parts;
  if (nameWithoutPrefix.contains('_')) {
    parts = nameWithoutPrefix.split('_');
  } else if (nameWithoutPrefix.contains('-')) {
    parts = nameWithoutPrefix.split('-');
  } else {
    // Nếu không nhận dạng được, trả về ngày mặc định
    return DateTime(1970, 1, 1);
  }
  
  if (parts.length == 3) {
    final month = int.tryParse(parts[0]) ?? 1;
    final day = int.tryParse(parts[1]) ?? 1;
    final year = int.tryParse(parts[2]) ?? 1970;
    return DateTime(year, month, day);
  }
  
  // Nếu không đủ 3 phần, trả về ngày mặc định
  return DateTime(1970, 1, 1);
}

  /// Tải file Excel trên Flutter Web (mở tab mới với URL)
  Future<void> _downloadExcelFileWeb(firebase_storage.Reference ref) async {
    final downloadURL = await ref.getDownloadURL();
    html.window.open(downloadURL, "_blank");
  }

  @override
  Widget build(BuildContext context) {
    final dateStr = DateFormat('MMMM dd, yyyy').format(_currentTime);
    final timeStr = DateFormat('HH:mm:ss').format(_currentTime);

    return Scaffold(
      backgroundColor: Colors.white,
      drawer: const SideDrawer(),
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        title: ScaleTransition(
          scale: Tween<double>(begin: 0.8, end: 1).animate(_controller),
          child: const Text(
            'Dashboard',
            style: TextStyle(fontWeight: FontWeight.w500),
          ),
        ),
      ),
      body: FutureBuilder<DashboardData>(
        future: _dashboardFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text("Error: ${snapshot.error}"));
          }
          final data = snapshot.data!;

          // Lên lịch reload dữ liệu sau 10 phút (nếu chưa có timer)
          if (_reloadTimer == null) {
            _reloadTimer = Timer(const Duration(minutes: 10), () {
              setState(() {
                // Reload cả Firestore lẫn Storage
                _dashboardFuture = fetchDashboardData();
                _excelFilesFuture = fetchLatestExcelFiles();
              });
              _reloadTimer = null;
            });
          }

          return FadeTransition(
            opacity: _fadeAnimation,
            child: SlideTransition(
              position: _slideAnimation,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Các thẻ tóm tắt
                    Wrap(
                      spacing: 16,
                      runSpacing: 16,
                      children: [
                        _buildSummaryCard(
                          "Active Drivers",
                          data.activeDrivers.toString(),
                          "Currently on duty",
                        ),
                        _buildSummaryCard(
                          "Pending Orders",
                          data.pendingOrders.toString(),
                          "Awaiting dispatch",
                        ),
                        _buildSummaryCard("Date", dateStr, ""),
                        _buildSummaryCard("Time", timeStr, ""),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Hiển thị danh sách file Excel gần đây với UI đẹp và animation
                    FutureBuilder<List<firebase_storage.Reference>>(
                      future: _excelFilesFuture,
                      builder: (context, snap) {
                        if (snap.connectionState == ConnectionState.waiting) {
                          return const Center(child: CircularProgressIndicator());
                        }
                        if (snap.hasError) {
                          return Text('Error loading Excel files: ${snap.error}');
                        }
                        final files = snap.data ?? [];
                        if (files.isEmpty) {
                          return const Text('No recent Excel files found.');
                        }

                        return ExcelFileList(
                          files: files,
                          onFileTap: _downloadExcelFileWeb,
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSummaryCard(String title, String value, String subtitle) {
    return SlideTransition(
      position: _cardSlideAnimation,
      child: Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        color: Colors.white,
        elevation: 3,
        shadowColor: Colors.black.withOpacity(0.1),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(value,
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              Text(title,
                  style: const TextStyle(fontSize: 16, color: Colors.black87)),
              if (subtitle.isNotEmpty)
                Text(subtitle,
                    style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
        ),
      ),
    );
  }
}

/// Widget hiển thị danh sách file Excel gần đây với hiệu ứng animation và hover.
class ExcelFileList extends StatefulWidget {
  /// Danh sách file Excel (các Reference đã được sắp xếp theo thứ tự mới nhất)
  final List<firebase_storage.Reference> files;

  /// Callback khi người dùng bấm vào một file
  final Function(firebase_storage.Reference) onFileTap;

  const ExcelFileList({
    Key? key,
    required this.files,
    required this.onFileTap,
  }) : super(key: key);

  @override
  _ExcelFileListState createState() => _ExcelFileListState();
}

class _ExcelFileListState extends State<ExcelFileList>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    // Khởi tạo controller với thời gian 600ms cho hiệu ứng fade/slide
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _animationController.forward();
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'File Excel gần đây',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: widget.files.length,
          itemBuilder: (context, index) {
            final fileRef = widget.files[index];
            // Tạo hiệu ứng staggered cho từng mục trong danh sách
            final animation = Tween<Offset>(
              begin: const Offset(0, 0.2),
              end: Offset.zero,
            ).animate(
              CurvedAnimation(
                parent: _animationController,
                curve: Interval(
                  (index / widget.files.length),
                  1.0,
                  curve: Curves.easeOut,
                ),
              ),
            );
            return SlideTransition(
              position: animation,
              child: _ExcelFileListItem(
                fileName: fileRef.name,
                onTap: () => widget.onFileTap(fileRef),
              ),
            );
          },
        ),
      ],
    );
  }
}

/// Widget riêng cho từng mục file, tích hợp hiệu ứng hover và tap
class _ExcelFileListItem extends StatefulWidget {
  final String fileName;
  final VoidCallback onTap;

  const _ExcelFileListItem({
    Key? key,
    required this.fileName,
    required this.onTap,
  }) : super(key: key);

  @override
  State<_ExcelFileListItem> createState() => _ExcelFileListItemState();
}

class _ExcelFileListItemState extends State<_ExcelFileListItem> {
  bool _hovering = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return MouseRegion(
      onEnter: (_) => setState(() => _hovering = true),
      onExit: (_) => setState(() => _hovering = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: const EdgeInsets.symmetric(vertical: 6),
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
          decoration: BoxDecoration(
            color: _hovering ? Colors.blue.shade50 : Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 6,
                offset: const Offset(0, 3),
              ),
            ],
            border: Border.all(
              color: _hovering ? Colors.blue : Colors.grey.shade300,
              width: 1,
            ),
          ),
          child: Row(
            children: [
              const Icon(Icons.description, size: 28, color: Colors.green),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  widget.fileName,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              Icon(Icons.chevron_right, color: Colors.grey.shade600),
            ],
          ),
        ),
      ),
    );
  }
}
