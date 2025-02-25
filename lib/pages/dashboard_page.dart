import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart'; // Để định dạng ngày giờ
import '../widgets/side_drawer.dart';

/// DashboardPage chuyển từ StatelessWidget sang StatefulWidget để cập nhật thời gian liên tục.
class DashboardPage extends StatefulWidget {
  const DashboardPage({Key? key}) : super(key: key);

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> with SingleTickerProviderStateMixin {
  // Biến lưu trữ thời gian hiện tại (theo GMT+7)
  late DateTime _currentTime;
  Timer? _timer;

  // Animation controller và các hiệu ứng
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;
  late Animation<Offset> _cardSlideAnimation;

  @override
  void initState() {
    super.initState();
    // Cập nhật thời gian hiện tại theo GMT+7
    _currentTime = DateTime.now().toUtc().add(const Duration(hours: 7));
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      setState(() {
        _currentTime = DateTime.now().toUtc().add(const Duration(hours: 7));
      });
    });

    // Khởi tạo AnimationController cho toàn bộ trang
    _controller = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );

    // Hiệu ứng fade cho toàn bộ nội dung
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );

    // Hiệu ứng slide nhẹ cho nội dung trang (từ dưới lên)
    _slideAnimation = Tween<Offset>(begin: const Offset(0, 0.1), end: Offset.zero).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );

    // Hiệu ứng slide riêng cho từng thẻ summary (để tạo cảm giác stagger)
    _cardSlideAnimation = Tween<Offset>(begin: const Offset(0, 0.2), end: Offset.zero).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.3, 0.7, curve: Curves.easeOut)),
    );

    _controller.forward();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Định dạng ngày và giờ sử dụng intl.
    final String formattedDate = DateFormat('MMMM dd, yyyy').format(_currentTime);
    final String formattedTime = DateFormat('HH:mm:ss').format(_currentTime);

    return Scaffold(
      backgroundColor: Colors.white,
      drawer: const SideDrawer(),
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        title: ScaleTransition(
          scale: Tween<double>(begin: 0.8, end: 1.0).animate(_controller),
          child: const Text(
            'Dashboard',
            style: TextStyle(fontWeight: FontWeight.w500),
          ),
        ),
      ),
      body: FadeTransition(
        opacity: _fadeAnimation,
        child: SlideTransition(
          position: _slideAnimation,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Row thống kê: Active Drivers, Pending Orders, Date và Time
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildAnimatedSummaryCard("Active Drivers", "24", "Currently on duty"),
                    _buildAnimatedSummaryCard("Pending Orders", "156", "Awaiting dispatch"),
                    _buildAnimatedSummaryCard("Date", formattedDate, ""),
                    _buildAnimatedSummaryCard("Time", formattedTime, ""),
                  ],
                ),
                const SizedBox(height: 32),
                // Tiêu đề phần Recent Orders
                Text(
                  "Recent Orders",
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 16),
                // Bảng dữ liệu đơn hàng với hiệu ứng fade và shadow nhẹ tạo cảm giác sang trọng
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: Container(
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
                      rows: [
                        _buildDataRow("#ORD-1001", "Mike Johnson", "Delivered", "10:30 AM", "..."),
                        _buildDataRow("#ORD-1002", "Sarah Smith", "In Transit", "11:15 AM", "..."),
                        _buildDataRow("#ORD-1003", "David Lee", "Delayed", "11:45 AM", "..."),
                      ],
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

  /// Hàm helper tạo thẻ thống kê với hiệu ứng hoạt ảnh tinh tế.
  Widget _buildAnimatedSummaryCard(String title, String value, String subtitle) {
    return SlideTransition(
      position: _cardSlideAnimation,
      child: Card(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        color: Colors.white,
        elevation: 3,
        shadowColor: Colors.black.withOpacity(0.1),
        child: SizedBox(
          width: 150,
          height: 100,
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(title, style: const TextStyle(fontSize: 16, color: Colors.black87)),
                if (subtitle.isNotEmpty)
                  Text(
                    subtitle,
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// Hàm helper tạo dòng của DataTable.
  DataRow _buildDataRow(String orderId, String driver, String status, String deliveryTime, String actions) {
    return DataRow(cells: [
      DataCell(Text(orderId)),
      DataCell(Text(driver)),
      DataCell(Text(status)),
      DataCell(Text(deliveryTime)),
      DataCell(Text(actions)),
    ]);
  }
}
