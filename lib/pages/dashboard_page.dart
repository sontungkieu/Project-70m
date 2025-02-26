import 'dart:async';
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:intl/intl.dart';
import '../widgets/side_drawer.dart';

// Lớp chứa dữ liệu cho Dashboard
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
  Timer? _timer;  // Timer 1s để cập nhật _currentTime
  Timer? _reloadTimer; // Timer 10 phút để reload future

  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  late Animation<Offset> _cardSlideAnimation;

  // Biến lưu future => khi setState thay đổi future => futurebuilder chạy lại
  Future<DashboardData>? _dashboardFuture;

  @override
  void initState() {
    super.initState();

    // Thời gian GMT+7, cập nhật mỗi giây (nếu muốn hiển thị giờ “live”)
    _currentTime = DateTime.now().toUtc().add(const Duration(hours: 7));
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() {
        _currentTime = DateTime.now().toUtc().add(const Duration(hours: 7));
      });
    });

    // Init animation
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

    // Lần đầu load => fetch
    _dashboardFuture = fetchDashboardData();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _reloadTimer?.cancel(); // Huỷ timer 10 phút
    _controller.dispose();
    super.dispose();
  }

  /// Gọi 3 query Firestore
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
            // Apple-style minimal loading
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text("Error: ${snapshot.error}"));
          }
          final data = snapshot.data!;
          
          // Khi data load xong => schedule 1 timer 10 phút (nếu chưa schedule)
          // Mỗi lần build, ta check reloadTimer == null
          if (_reloadTimer == null) {
            _reloadTimer = Timer(const Duration(minutes: 10), () {
              // 10 phút sau => setState => fetch lại
              setState(() {
                _dashboardFuture = fetchDashboardData();
              });
              // reset _reloadTimer = null => cho phép schedule lần nữa khi load xong
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
                    const SizedBox(height: 32),
                    Text(
                      "Today's Orders",
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w500),
                    ),
                    const SizedBox(height: 16),
                    _buildTodayOrdersTable(data.todaysOrders),
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

  Widget _buildTodayOrdersTable(List<Map<String, dynamic>> orders) {
    if (orders.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        alignment: Alignment.center,
        child: const Text("No orders for today"),
      );
    }

    final rows = orders.map((item) {
      final orderId = item['orderId'] ?? '-';
      final driver = item['driver'] ?? 'No Driver';
      final deliveryStatus = item['deliveryStatus'] ?? 'Pending';
      final deliveryTime = item['deliveryTime'] ?? '-';
      // Action
      const actionText = "...";
      return DataRow(cells: [
        DataCell(Text(orderId)),
        DataCell(Text(driver)),
        DataCell(Text(deliveryStatus)),
        DataCell(Text(deliveryTime)),
        DataCell(Text(actionText)),
      ]);
    }).toList();

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: Colors.grey.shade50,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: DataTable(
        columns: const [
          DataColumn(label: Text("Order ID")),
          DataColumn(label: Text("Driver")),
          DataColumn(label: Text("Status")),
          DataColumn(label: Text("Delivery Time")),
          DataColumn(label: Text("Actions")),
        ],
        rows: rows,
      ),
    );
  }
}
