import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:intl/intl.dart';
import '../widgets/side_drawer.dart';
import 'package:firebase_storage/firebase_storage.dart' as firebase_storage;
import 'package:webview_flutter/webview_flutter.dart';
import 'package:path_provider/path_provider.dart';

/// Hàm ghi log vào file txt
Future<void> writeLog(String logMessage) async {
  try {
    final directory = await getApplicationDocumentsDirectory();
    final file = File('${directory.path}/app_log.txt');
    final sink = file.openWrite(mode: FileMode.append);
    sink.write('${DateTime.now()}: $logMessage\n');
    await sink.flush();
    await sink.close();
  } catch (e) {
    print("Error writing log: $e");
  }
}

/// Hàm lấy URL của file Excel từ Firebase Storage
Future<String?> _getExcelFileUrl() async {
  try {
    final firebase_storage.Reference storageRef = firebase_storage.FirebaseStorage.instance
        .ref('requests_xlsx/Lenh_Dieu_Xe.xlsx');
    final String fileUrl = await storageRef.getDownloadURL();
    await writeLog("Excel file URL: $fileUrl");
    return fileUrl;
  } catch (e) {
    await writeLog("Error getting Excel file URL: $e");
    return null;
  }
}

Widget _buildExcelViewer(BuildContext context) {
  return FutureBuilder<String?>(
    future: _getExcelFileUrl(),
    builder: (context, snapshot) {
      if (snapshot.connectionState == ConnectionState.waiting) {
        return const Center(child: CircularProgressIndicator());
      } else if (snapshot.hasError || !snapshot.hasData) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          showDialog(
            context: context,
            builder: (context) => AlertDialog(
              title: const Text("Lỗi"),
              content: Text("Không thể tải file Excel: ${snapshot.error}"),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text("Đóng"),
                ),
              ],
            ),
          );
        });
        return Container();
      } else {
        final fileUrl = snapshot.data!;
        final viewerUrl = "https://docs.google.com/gview?embedded=true&url=${Uri.encodeComponent(fileUrl)}";
        
        final controller = WebViewController()
          ..setJavaScriptMode(JavaScriptMode.unrestricted)
          ..loadRequest(Uri.parse(viewerUrl));

        return Container(
          height: MediaQuery.of(context).size.height * 0.6,
          decoration: BoxDecoration(
            border: Border.all(color: Colors.black12),
            borderRadius: BorderRadius.circular(12),
            color: Colors.grey.shade50,
          ),
          child: WebViewWidget(controller: controller),
        );
      }
    },
  );
}

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

class _DashboardPageState extends State<DashboardPage> with SingleTickerProviderStateMixin {
  late DateTime _currentTime;
  Timer? _timer;
  Timer? _reloadTimer;

  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  late Animation<Offset> _cardSlideAnimation;

  Future<DashboardData>? _dashboardFuture;

  @override
  void initState() {
    super.initState();
    _currentTime = DateTime.now().toUtc().add(const Duration(hours: 7));
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        _currentTime = DateTime.now().toUtc().add(const Duration(hours: 7));
      });
    });

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
      CurvedAnimation(parent: _controller, curve: const Interval(0.3, 0.7, curve: Curves.easeOut)),
    );

    _controller.forward();
    _dashboardFuture = fetchDashboardData();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _reloadTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  Future<DashboardData> fetchDashboardData() async {
    final activeSnap = await FirebaseFirestore.instance
        .collection('Drivers')
        .where('available', isEqualTo: true)
        .get();
    final activeCount = activeSnap.size;

    final pendingSnap = await FirebaseFirestore.instance
        .collection('Requests')
        .where('delivery_status', isEqualTo: false)
        .get();
    final pendingCount = pendingSnap.size;

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
            return Center(child: Text("Lỗi: ${snapshot.error}"));
          }
          final data = snapshot.data!;

          if (_reloadTimer == null) {
            _reloadTimer = Timer(const Duration(minutes: 10), () {
              setState(() {
                _dashboardFuture = fetchDashboardData();
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
                    Wrap(
                      spacing: 16,
                      runSpacing: 16,
                      children: [
                        _buildSummaryCard("Tài xế hoạt động", data.activeDrivers.toString(), "Đang làm việc"),
                        _buildSummaryCard("Đơn hàng đang chờ", data.pendingOrders.toString(), "Chờ điều phối"),
                        _buildSummaryCard("Ngày", dateStr, ""),
                        _buildSummaryCard("Giờ", timeStr, ""),
                      ],
                    ),
                    const SizedBox(height: 32),
                    const Text(
                      "Lệnh điều xe hôm nay",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    _buildExcelViewer(context),
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
              Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              Text(title, style: const TextStyle(fontSize: 16, color: Colors.black87)),
              if (subtitle.isNotEmpty)
                Text(subtitle, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
        ),
      ),
    );
  }
}