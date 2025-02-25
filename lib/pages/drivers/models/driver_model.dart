// drivers/models/driver_model.dart
import 'package:cloud_firestore/cloud_firestore.dart';

class Driver {
  final String id;
  final String name;
  final String vehicleId;
  final String phoneNumber;
  final int vehicleLoad;
  final bool available;

  Driver({
    required this.id,
    required this.name,
    required this.vehicleId,
    required this.phoneNumber,
    required this.vehicleLoad,
    required this.available,
  });

  factory Driver.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return Driver(
      id: doc.id,
      name: data['name'] ?? '',
      vehicleId: data['vehical_id'] ?? '',
      phoneNumber: data['phone_number'] ?? '',
      vehicleLoad: data['vehical_load']?.toInt() ?? 0,
      available: data['available'] ?? false,
    );
  }
}