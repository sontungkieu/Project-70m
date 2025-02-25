import 'dart:async';
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';

/// LoginPage: Giao diện đăng nhập sử dụng Firebase Authentication với theme trắng–đen tinh tế,
/// hiệu ứng animation chuyên nghiệp và background gradient thay đổi liên tục.
class LoginPage extends StatefulWidget {
  const LoginPage({Key? key}) : super(key: key);

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  // Controllers cho input email và password.
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  // Biến trạng thái cho loading và thông báo lỗi.
  bool _isLoading = false;
  String _errorMessage = '';

  // Biến và Timer điều khiển gradient nền.
  bool _toggleGradient = false;
  late Timer _gradientTimer;

  @override
  void initState() {
    super.initState();
    // Thay đổi gradient nền mỗi 4 giây.
    _gradientTimer = Timer.periodic(const Duration(seconds: 4), (timer) {
      setState(() {
        _toggleGradient = !_toggleGradient;
      });
    });
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _gradientTimer.cancel();
    super.dispose();
  }

  /// Phương thức đăng nhập sử dụng FirebaseAuth.
  Future<void> _login() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      await FirebaseAuth.instance.signInWithEmailAndPassword(
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );
      Navigator.pushReplacementNamed(context, '/dashboard');
    } on FirebaseAuthException catch (e) {
      setState(() {
        _errorMessage = e.message ?? 'Đã có lỗi xảy ra trong quá trình đăng nhập.';
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Đã có lỗi không mong muốn xảy ra.';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  /// Xây dựng widget form đăng nhập với các hiệu ứng staggered animations.
  Widget _buildLoginForm() {
    return Container(
      constraints: const BoxConstraints(maxWidth: 400),
      padding: const EdgeInsets.all(24.0),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.9),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Tiêu đề "Login" với phông chữ chuyên nghiệp.
          Text(
            "Login",
            style: GoogleFonts.lato(
              textStyle: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: Colors.black87,
                    fontWeight: FontWeight.bold,
                  ),
            ),
          ).animate().fadeIn(delay: 400.ms, duration: 600.ms),
          const SizedBox(height: 24),
          // TextField nhập email với hiệu ứng fadeIn và slideY.
          TextField(
            controller: _emailController,
            style: const TextStyle(color: Colors.black87),
            decoration: InputDecoration(
              labelText: "Email or Username",
              labelStyle: const TextStyle(color: Colors.black54),
              prefixIcon: const Icon(Icons.email, color: Colors.black54),
              enabledBorder: OutlineInputBorder(
                borderSide: const BorderSide(color: Colors.black26),
                borderRadius: BorderRadius.circular(8),
              ),
              focusedBorder: OutlineInputBorder(
                borderSide: const BorderSide(color: Colors.black87),
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ).animate()
              .fadeIn(delay: 600.ms, duration: 600.ms)
              .slideY(begin: 0.3, duration: 600.ms),
          const SizedBox(height: 16),
          // TextField nhập password với hiệu ứng fadeIn và slideY.
          TextField(
            controller: _passwordController,
            obscureText: true,
            style: const TextStyle(color: Colors.black87),
            decoration: InputDecoration(
              labelText: "Password",
              labelStyle: const TextStyle(color: Colors.black54),
              prefixIcon: const Icon(Icons.lock, color: Colors.black54),
              enabledBorder: OutlineInputBorder(
                borderSide: const BorderSide(color: Colors.black26),
                borderRadius: BorderRadius.circular(8),
              ),
              focusedBorder: OutlineInputBorder(
                borderSide: const BorderSide(color: Colors.black87),
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ).animate()
              .fadeIn(delay: 800.ms, duration: 600.ms)
              .slideY(begin: 0.3, duration: 600.ms),
          const SizedBox(height: 24),
          // Nút Login với hiệu ứng scale và fadeIn.
          _isLoading
              ? const CircularProgressIndicator()
                  .animate().fadeIn(delay: 1000.ms, duration: 600.ms)
              : ElevatedButton(
                  onPressed: _login,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text(
                    "Login",
                    style: GoogleFonts.lato(
                      textStyle: const TextStyle(color: Colors.white, fontSize: 16),
                    ),
                  ),
                ).animate()
                .fadeIn(delay: 1000.ms, duration: 600.ms)
                .scale(begin: Offset(0.8, 0.8), duration: 600.ms),
          const SizedBox(height: 16),
          // Thông báo lỗi với hiệu ứng fadeIn (nếu có).
          if (_errorMessage.isNotEmpty)
            Text(
              _errorMessage,
              style: const TextStyle(color: Colors.red),
            ).animate().fadeIn(delay: 1200.ms, duration: 600.ms),
          const SizedBox(height: 16),
          // Nút chuyển sang trang đăng ký.
          TextButton(
            onPressed: () => Navigator.pushNamed(context, '/register'),
            child: Text(
              "Don’t have an account? Register",
              style: GoogleFonts.lato(
                color: Colors.black87,
                fontWeight: FontWeight.w600,
              ),
            ),
          ).animate().fadeIn(delay: 1400.ms, duration: 600.ms),
          const SizedBox(height: 24),
          // Câu quote truyền cảm hứng về giao thông.
          Text(
            "“Giao thông là huyết mạch của đất nước – nơi mỗi hành trình là một khởi đầu mới.”",
            textAlign: TextAlign.center,
            style: GoogleFonts.lato(
              textStyle: const TextStyle(
                color: Colors.black54,
                fontStyle: FontStyle.italic,
                fontSize: 14,
              ),
            ),
          ).animate().fadeIn(delay: 1600.ms, duration: 600.ms),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Định nghĩa 2 gradient đối lập theo phong cách trắng–đen
    final Gradient gradient1 = const LinearGradient(
      colors: [Colors.white, Colors.black],
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
    );
    final Gradient gradient2 = const LinearGradient(
      colors: [Colors.black, Colors.white],
      begin: Alignment.topRight,
      end: Alignment.bottomLeft,
    );

    return Scaffold(
      body: AnimatedContainer(
        duration: const Duration(seconds: 4),
        curve: Curves.easeInOut,
        decoration: BoxDecoration(
          gradient: _toggleGradient ? gradient1 : gradient2,
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: _buildLoginForm(),
          ),
        ),
      ),
    );
  }
}
