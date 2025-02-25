import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';



/// SideDrawer: Thanh điều hướng của ứng dụng MyApp.
class SideDrawer extends StatelessWidget {
  const SideDrawer({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: Container(
        color: Colors.black87, // Màu nền của sidebar
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            // Header hiển thị tên ứng dụng.
            const DrawerHeader(
              child: Text(
                'MyApp',
                style: TextStyle(color: Colors.white, fontSize: 24),
              ),
            ),
            // Nút Logout (đặt đầu tiên) với hiệu ứng hover.
            ListTile(
              leading: const Icon(Icons.logout, color: Colors.white),
              title: const Text(
                "Logout",
                style: TextStyle(color: Colors.white),
              ),
              hoverColor: Colors.grey.shade700, // Hiệu ứng hover
              onTap: () async {
                // Đăng xuất khỏi Firebase.
                await FirebaseAuth.instance.signOut();
                // Điều hướng về trang login, loại bỏ các route cũ.
                Navigator.pushNamedAndRemoveUntil(
                    context, '/login', (route) => false);
              },
            ),
            const Divider(color: Colors.white54),
            // Các mục điều hướng khác với hiệu ứng hover.
            _buildDrawerItem(
              context: context,
              icon: Icons.dashboard,
              title: "Dashboard",
              route: '/dashboard',
            ),
            _buildDrawerItem(
              context: context,
              icon: Icons.calendar_today,
              title: "Schedule",
              route: '/schedule',
            ),
            _buildDrawerItem(
              context: context,
              icon: Icons.people,
              title: "Drivers",
              route: '/drivers',
            ),
            _buildDrawerItem(
              context: context,
              icon: Icons.attach_money,
              title: "Payroll",
              route: '/payroll',
            ),
          ],
        ),
      ),
    );
  }

  /// Hàm helper để xây dựng từng mục điều hướng với hiệu ứng hover.
  Widget _buildDrawerItem({
    required BuildContext context,
    required IconData icon,
    required String title,
    required String route,
  }) {
    return ListTile(
      leading: Icon(icon, color: Colors.white),
      title: Text(title, style: const TextStyle(color: Colors.white)),
      hoverColor: Colors.grey.shade700, // Hiệu ứng hover khi di chuột
      onTap: () {
        // Đóng sidebar trước khi chuyển trang.
        Navigator.pop(context);
        // Điều hướng tới route tương ứng.
        Navigator.pushNamed(context, route);
      },
    );
  }
}

