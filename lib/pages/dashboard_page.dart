import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:intl/intl.dart';
import '../widgets/side_drawer.dart';
import 'package:excel/excel.dart';
import 'package:firebase_storage/firebase_storage.dart' as firebase_storage;

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
  Timer? _timer; // Timer 1s để cập nhật thời gian
  Timer? _reloadTimer; // Timer 10 phút để reload future

  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  late Animation<Offset> _cardSlideAnimation;

  // Future chứa dữ liệu Dashboard
  Future<DashboardData>? _dashboardFuture;
  // Future chứa dữ liệu file Excel (chỉ khởi tạo 1 lần)
  late Future<Uint8List?> _excelFuture;

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
          curve: const Interval(0.3, 0.7, curve: Curves.easeOut)),
    );

    _controller.forward();

    // Lần đầu load dữ liệu Dashboard và file Excel (chỉ 1 lần)
    _dashboardFuture = fetchDashboardData();
    _excelFuture = _downloadExcelFile();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _reloadTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  /// Gọi các query Firestore để lấy dữ liệu Dashboard
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

  /// Hàm lấy download URL của file Excel từ Firebase Storage (dùng customStorage)
  Future<String?> _getDownloadLink() async {
    try {
      final firebase_storage.Reference storageRef =
          customStorage.ref('requests_xlsx/Lenh_Dieu_Xe.xlsx');
      final String url = await storageRef.getDownloadURL();
      print("Download URL: $url");
      return url;
    } catch (e) {
      print("Error getting download link: $e");
      return null;
    }
  }

  /// Hàm tải file Excel dưới dạng Uint8List từ Firebase Storage
  Future<Uint8List?> _downloadExcelFile() async {
  try {
    final firebase_storage.Reference storageRef =
        customStorage.ref('requests_xlsx/Lenh_Dieu_Xe.xlsx');

    // Kiểm tra metadata để xem file có quá lớn hay không (nếu cần)
    final metadata = await storageRef.getMetadata();
    final fileSize = metadata.size ?? 0;
    if (fileSize > 10 * 1024 * 1024) {
      throw Exception("File Excel quá lớn, không thể hiển thị trực tiếp.");
    }

    // Gọi getData() mà không dùng tham số maxSize
    final Uint8List? data = await storageRef.getData();
    if (data == null || data.isEmpty) {
      throw Exception("File rỗng hoặc không thể tải.");
    }
    return data;
  } catch (e) {
    print("Error downloading Excel file: $e");
    return null;
  }
}


  /// Hàm phân tích dữ liệu Excel và trả về Map với key là tên sheet, value là dữ liệu dạng List<List<String>>
  Map<String, List<List<String>>> parseExcelData(Uint8List excelData) {
    final excel = Excel.decodeBytes(excelData);
    final Map<String, List<List<String>>> allSheetData = {};

    for (var sheetName in excel.tables.keys) {
      final sheet = excel.tables[sheetName];
      if (sheet == null) continue;

      List<List<String>> sheetData = [];
      for (var row in sheet.rows) {
        List<String> rowData = [];
        for (var cell in row) {
          rowData.add(cell?.value?.toString() ?? "");
        }
        sheetData.add(rowData);
      }
      allSheetData[sheetName] = sheetData;
    }
    return allSheetData;
  }

  /// Widget hiển thị dữ liệu Excel với hỗ trợ nhiều sheet
  Widget _buildExcelViewer(BuildContext context) {
    return FutureBuilder<Uint8List?>(
      future: _excelFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(
            child: Text(
              "Không thể tải file Excel (lỗi bất ngờ): ${snapshot.error}\n"
              "Vui lòng kiểm tra lại hoặc sử dụng phương án khác.",
              textAlign: TextAlign.center,
            ),
          );
        }
        if (!snapshot.hasData || snapshot.data == null) {
          return const Center(
            child: Text(
              "Không thể tải file Excel. Có thể link bị sai hoặc bạn không đủ quyền truy cập.",
              textAlign: TextAlign.center,
            ),
          );
        }

        final excelData = snapshot.data!;
        try {
          final allSheetData = parseExcelData(excelData);
          if (allSheetData.isEmpty) {
            return const Center(child: Text("Không có sheet nào trong file Excel."));
          }
          return MultiSheetExcelViewer(excelData: allSheetData);
        } catch (e) {
          return Center(
            child: Text(
              "File Excel bị lỗi hoặc không đúng định dạng.\nChi tiết: $e",
              textAlign: TextAlign.center,
            ),
          );
        }
      },
    );
  }

  /// Widget hiển thị download URL (nếu muốn debug hoặc copy link)
  Widget _buildDownloadLink() {
    return FutureBuilder<String?>(
      future: _getDownloadLink(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        } else if (snapshot.hasError || !snapshot.hasData) {
          return Center(
            child: Text(
              "Không thể lấy link tải file: ${snapshot.error}\n"
              "Kiểm tra quyền truy cập hoặc đường dẫn.",
              textAlign: TextAlign.center,
            ),
          );
        } else {
          final url = snapshot.data!;
          return Padding(
            padding: const EdgeInsets.all(8.0),
            child: SelectableText(
              url,
              style: const TextStyle(color: Colors.blue),
            ),
          );
        }
      },
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
            return Center(child: Text("Error: ${snapshot.error}"));
          }
          final data = snapshot.data!;

          // Lên lịch reload dữ liệu sau 10 phút nếu chưa có timer
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
                        _buildSummaryCard("Active Drivers", data.activeDrivers.toString(), "Currently on duty"),
                        _buildSummaryCard("Pending Orders", data.pendingOrders.toString(), "Awaiting dispatch"),
                        _buildSummaryCard("Date", dateStr, ""),
                        _buildSummaryCard("Time", timeStr, ""),
                      ],
                    ),
                    const SizedBox(height: 16),
                    // Hiển thị link để kiểm tra (nếu cần)
                    _buildDownloadLink(),
                    const SizedBox(height: 32),
                    // Hiển thị dữ liệu Excel với hỗ trợ nhiều sheet
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

/// Widget hiển thị dữ liệu Excel với hỗ trợ nhiều sheet sử dụng TabBar
class MultiSheetExcelViewer extends StatelessWidget {
  final Map<String, List<List<String>>> excelData;

  const MultiSheetExcelViewer({Key? key, required this.excelData}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (excelData.isEmpty) {
      return const Center(child: Text("Không có dữ liệu Excel để hiển thị."));
    }
    return DefaultTabController(
      length: excelData.keys.length,
      child: Column(
        children: [
          TabBar(
            isScrollable: true,
            tabs: excelData.keys.map((sheetName) => Tab(text: sheetName)).toList(),
          ),
          Expanded(
            child: TabBarView(
              children: excelData.entries.map((entry) {
                final sheetData = entry.value;
                if (sheetData.isEmpty) {
                  return const Center(child: Text("Sheet này không có dữ liệu."));
                }
                return SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: DataTable(
                    columns: _buildHeaderRow(sheetData.first),
                    rows: _buildDataRows(sheetData.skip(1).toList()),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  List<DataColumn> _buildHeaderRow(List<String> header) {
    return header.map((column) => DataColumn(label: Text(column))).toList();
  }

  List<DataRow> _buildDataRows(List<List<String>> rows) {
    return rows.map((row) => DataRow(
      cells: row.map((cell) => DataCell(Text(cell))).toList(),
    )).toList();
  }
}
