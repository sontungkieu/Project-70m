import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';

// HoverableTile widget inserted inline
class HoverableTile extends StatefulWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;

  const HoverableTile({
    Key? key,
    required this.icon,
    required this.title,
    required this.onTap,
  }) : super(key: key);

  @override
  State<HoverableTile> createState() => _HoverableTileState();
}

class _HoverableTileState extends State<HoverableTile> {
  bool _isHover = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHover = true),
      onExit: (_) => setState(() => _isHover = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeInOut,
        color: _isHover ? Colors.white.withOpacity(0.1) : Colors.transparent,
        child: InkWell(
          onTap: widget.onTap,
          splashColor: Colors.transparent,
          highlightColor: Colors.transparent,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
            child: Row(
              children: [
                TweenAnimationBuilder<double>(
                  duration: const Duration(milliseconds: 200),
                  tween: Tween<double>(
                    begin: 1.0,
                    end: _isHover ? 1.1 : 1.0,
                  ),
                  builder: (context, scale, child) {
                    return Transform.scale(
                      scale: scale,
                      child: Icon(
                        widget.icon,
                        color: Colors.white,
                      ),
                    );
                  },
                ),
                const SizedBox(width: 16),
                Text(
                  widget.title,
                  style: const TextStyle(color: Colors.white, fontSize: 16),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class SideDrawer extends StatefulWidget {
  const SideDrawer({Key? key}) : super(key: key);

  @override
  State<SideDrawer> createState() => _SideDrawerState();
}

class _SideDrawerState extends State<SideDrawer>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnim;
  late Animation<Offset> _slideAnim;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _fadeAnim = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );
    _slideAnim = Tween<Offset>(
      begin: const Offset(-0.05, 0),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _controller.forward(from: 0);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF2C2C2E), Color(0xFF1C1C1E)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: FadeTransition(
          opacity: _fadeAnim,
          child: SlideTransition(
            position: _slideAnim,
            child: ListView(
              padding: EdgeInsets.zero,
              children: [
                const DrawerHeader(
                  margin: EdgeInsets.zero,
                  decoration: BoxDecoration(
                    color: Colors.transparent,
                  ),
                  child: Text(
                    'MyApp',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                HoverableTile(
                  icon: Icons.logout,
                  title: "Logout",
                  onTap: () async {
                    await FirebaseAuth.instance.signOut();
                    Navigator.pushNamedAndRemoveUntil(
                      context,
                      '/login',
                      (route) => false,
                    );
                  },
                ),
                const Divider(color: Colors.white54),
                HoverableTile(
                  icon: Icons.dashboard,
                  title: "Dashboard",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.pushNamed(context, '/dashboard');
                  },
                ),
                HoverableTile(
                  icon: Icons.calendar_today,
                  title: "Schedule",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.pushNamed(context, '/schedule');
                  },
                ),
                HoverableTile(
                  icon: Icons.people,
                  title: "Drivers",
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.pushNamed(context, '/drivers');
                  },
                ),
               
              ],
            ),
          ),
        ),
      ),
    );
  }
}
