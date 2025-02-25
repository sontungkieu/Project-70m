// drivers/widgets/driver_card.dart
import 'package:flutter/material.dart';
import '../models/driver_model.dart';
import 'status_indicator.dart';

class DriverCard extends StatefulWidget {
  final Driver driver;
  final VoidCallback onTap;
  final VoidCallback onDelete; // Thêm dòng này

  const DriverCard({
    super.key,
    required this.driver,
    required this.onTap,
    required this.onDelete, // Thêm vào constructor
  });

  

  @override
  State<DriverCard> createState() => _DriverCardState();
}

class _DriverCardState extends State<DriverCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        transform: Matrix4.identity()..scale(_isHovered ? 1.02 : 1.0),
        child: Card(
          elevation: _isHovered ? 8 : 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          child: InkWell(
            onTap: widget.onTap,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    children: [
                      const CircleAvatar(
                        backgroundColor: Colors.black,
                        child: Icon(Icons.person, color: Colors.white),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.driver.name,
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            Text(
                              widget.driver.vehicleId,
                              style: TextStyle(
                                color: Colors.grey.shade600,
                                fontSize: 15,
                              ),
                            ),
                          ],
                        ),
                      ),
                      StatusIndicator(isActive: widget.driver.available),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("Phone: ${widget.driver.phoneNumber}"),
                      Text("Capacity: ${widget.driver.vehicleLoad} kg"),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}