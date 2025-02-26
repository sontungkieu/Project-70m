// drivers/models/driver_model.dart
import 'package:cloud_firestore/cloud_firestore.dart';

class Driver {
  final String id;
  final String name;
  final String cccd; // Thêm trường CCCD
  final String phoneNumber;
  final String vehicleId;
  final int vehicleLoad;
  final int salary; // Thêm trường salary
  final bool available;
  final dynamic routeByDay;
  final dynamic routeByMonth;
  final dynamic allRouteHistory;

  Driver({
    required this.id,
    required this.name,
    required this.cccd,
    required this.phoneNumber,
    required this.vehicleId,
    required this.vehicleLoad,
    required this.salary,
    required this.available,
    this.routeByDay,
    this.routeByMonth,
    this.allRouteHistory,
  });

  factory Driver.fromFirestore(DocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return Driver(
      id: doc.id,
      name: data['name'] ?? '',
      cccd: data['cccd'] ?? '', // Giá trị mặc định nếu không có
      phoneNumber: data['phone_number'] ?? '',
      vehicleId: data['vehical_id'] ?? '',
      vehicleLoad: data['vehical_load']?.toInt() ?? 0,
      salary: data['salary']?.toInt() ?? 0, // Mặc định 0 nếu không có
      available: data['available'] ?? false,
      routeByDay: data['route_by_day'],
      routeByMonth: data['route_by_month'],
      allRouteHistory: data['all_route_history'],
    );
  }
}