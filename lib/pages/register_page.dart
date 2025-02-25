import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';

/// RegisterPage: Giao diện đăng ký sử dụng Firebase Authentication.
class RegisterPage extends StatefulWidget {
  const RegisterPage({Key? key}) : super(key: key);

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> with SingleTickerProviderStateMixin {
  // Animation controller cho trang và AppBar
  late AnimationController _controller;
  late Animation<Offset> _slideAnimation;

  // Controller để lấy giá trị nhập vào từ người dùng.
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  // Biến trạng thái để hiển thị loading và thông báo lỗi.
  bool _isLoading = false;
  String _errorMessage = '';

  /// Phương thức _register() dùng để đăng ký tài khoản với email và password thông qua Firebase.
  Future<void> _register() async {
    setState(() {
      _isLoading = true;    // Bật loading khi bắt đầu đăng ký.
      _errorMessage = '';   // Xóa thông báo lỗi cũ.
    });

    try {
      // Gọi Firebase Authentication để tạo tài khoản mới.
      await FirebaseAuth.instance.createUserWithEmailAndPassword(
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );

      // Nếu đăng ký thành công, điều hướng sang trang Dashboard.
      Navigator.pushReplacementNamed(context, '/dashboard');
    } on FirebaseAuthException catch (e) {
      // Nếu có lỗi từ Firebase, cập nhật thông báo lỗi.
      setState(() {
        _errorMessage = e.message ?? 'An error occurred during registration.';
      });
    } catch (e) {
      // Xử lý các lỗi không mong đợi.
      setState(() {
        _errorMessage = 'Unexpected error occurred.';
      });
    } finally {
      // Tắt loading khi quá trình đăng ký hoàn thành.
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  void initState() {
    super.initState();
    // Khởi tạo AnimationController cho hiệu ứng chuyển động của trang và AppBar.
    _controller = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0, 1), // Trượt từ dưới lên
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));
    _controller.forward();
  }

  @override
  void dispose() {
    // Giải phóng controller khi widget không còn sử dụng nữa để tránh rò rỉ bộ nhớ.
    _emailController.dispose();
    _passwordController.dispose();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _slideAnimation,
      child: Scaffold(
        appBar: AppBar(
          backgroundColor: Colors.black,
          title: ScaleTransition(
            scale: Tween<double>(begin: 0.8, end: 1.0).animate(_controller),
            child: const Text("Đăng ký"),
          ),
        ),
        body: Center(
          child: Container(
            constraints: const BoxConstraints(maxWidth: 400),
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Tiêu đề trang
                Text(
                  "Tạo tài khoản",
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                // Trường nhập liệu Email với hiệu ứng label nổi.
                TextFormField(
                  controller: _emailController,
                  decoration: InputDecoration(
                    labelText: "Email",
                    floatingLabelBehavior: FloatingLabelBehavior.auto,
                    prefixIcon: const Icon(Icons.email_outlined),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    filled: true,
                    fillColor: Colors.grey[100],
                  ),
                ),
                const SizedBox(height: 16),
                // Trường nhập liệu Password với hiệu ứng label nổi.
                TextFormField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: "Password",
                    floatingLabelBehavior: FloatingLabelBehavior.auto,
                    prefixIcon: const Icon(Icons.lock_outline),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    filled: true,
                    fillColor: Colors.grey[100],
                  ),
                ),
                const SizedBox(height: 24),
                // Animation cho nút đăng ký, chuyển đổi giữa nút và loading indicator.
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.black)
                      : ElevatedButton(
                          key: const ValueKey('register_button'),
                          onPressed: _register,
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            backgroundColor: Colors.black,
                            foregroundColor: Colors.white,
                          ),
                          child: const Text("Đăng ký"),
                        ),
                ),
                const SizedBox(height: 16),
                // Animation cho thông báo lỗi.
                AnimatedOpacity(
                  opacity: _errorMessage.isNotEmpty ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 500),
                  child: Text(
                    _errorMessage,
                    style: const TextStyle(color: Colors.red),
                    textAlign: TextAlign.center,
                  ),
                ),
                const SizedBox(height: 24),
                // Nút chuyển sang trang đăng nhập nếu người dùng đã có tài khoản.
                TextButton(
                  onPressed: () => Navigator.pushNamed(context, '/login'),
                  child: const Text("Already have an account? Sign in"),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
