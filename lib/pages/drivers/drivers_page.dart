import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:pull_to_refresh/pull_to_refresh.dart';
import '../../widgets/side_drawer.dart';
import 'models/driver_model.dart';
import 'widgets/driver_card.dart';
import 'widgets/dialogs/add_driver_dialog.dart';
import 'widgets/dialogs/edit_driver_dialog.dart';
import 'widgets/dialogs/delete_dialog.dart';
import 'widgets/status_indicator.dart';

class DriversPage extends StatefulWidget {
  const DriversPage({super.key});

  @override
  State<DriversPage> createState() => _DriversPageState();
}

class _DriversPageState extends State<DriversPage> {
  final RefreshController _refreshController = RefreshController();
  final TextEditingController _searchController = TextEditingController();
  final CollectionReference _driversCollection =
      FirebaseFirestore.instance.collection('Drivers');

  List<Driver> _filterDrivers(List<Driver> drivers, String query) {
  final searchQuery = query.toLowerCase().trim();
  
  return drivers.where((driver) {
    final nameMatch = driver.name.toLowerCase().contains(searchQuery);
    final licenseMatch = driver.vehicleId.toLowerCase().contains(searchQuery);
    return nameMatch || licenseMatch;
  }).toList();
}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const SideDrawer(),
      appBar: AppBar(
        title: const Text('Drivers Management'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildHeader(),
            const SizedBox(height: 24),
            Expanded(child: _buildDriverList()),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      children: [
        _buildAddButton(),
        const Spacer(),
        _buildSearchField(),
      ],
    );
  }

  Widget _buildAddButton() {
    return ElevatedButton.icon(
      icon: const Icon(Icons.add, size: 20),
      label: const Text("Add Driver"),
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      onPressed: () => AddDriverDialog.show(context, _driversCollection),
    );
  }

  Widget _buildSearchField() {
    return SizedBox(
      width: 280,
      child: TextField(
        controller: _searchController,
        decoration: InputDecoration(
          filled: true,
          fillColor: Colors.grey[100],
          hintText: "Search drivers...",
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
          prefixIcon: const Icon(Icons.search, color: Colors.grey),
          contentPadding: const EdgeInsets.symmetric(vertical: 14),
        ),
         onChanged: (value) => setState(() {}), 
      ),
    );
  }

  Widget _buildDriverList() {
  return StreamBuilder<QuerySnapshot>(
    stream: _driversCollection.snapshots(),
    builder: (context, snapshot) {
      if (snapshot.hasError) return _buildErrorWidget();
      if (snapshot.connectionState == ConnectionState.waiting) {
        return _buildLoading();
      }

      final allDrivers = _parseDrivers(snapshot.data!.docs);
      final filteredDrivers = _filterDrivers(allDrivers, _searchController.text);

      if (filteredDrivers.isEmpty) return _buildEmptySearch();
      
      return _buildRefreshableList(filteredDrivers);
    },
  );
}

  List<Driver> _parseDrivers(List<QueryDocumentSnapshot> docs) {
    return docs.map((doc) => Driver.fromFirestore(doc)).toList();
  }

  /// Đã thay thế AnimatedList bằng ListView.builder
 Widget _buildRefreshableList(List<Driver> drivers) {
  return SmartRefresher(
    controller: _refreshController,
    onRefresh: _refreshData,
    header: CustomHeader(
      builder: (context, status) => _buildRefreshIndicator(status ?? RefreshStatus.idle),
    ),
    child: ListView.builder(
      itemCount: drivers.length,
      itemBuilder: (context, index) {
        return DriverCard(
          driver: drivers[index],
          onTap: () => _showDriverDetails(context, drivers[index]),
          onDelete: () => _handleDelete(drivers[index]),
        );
      },
    ),
  );
}

  Widget _buildEmptySearch() {
  return Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.search_off, size: 50, color: Colors.grey.shade400),
        const SizedBox(height: 16),
        Text(
          "Không tìm thấy tài xế phù hợp",
          style: TextStyle(
            color: Colors.grey.shade600,
            fontSize: 16,
          ),
        ),
      ],
    ),
  );
}

  /// Chỉ xóa trên Firestore, không còn removeItem như AnimatedList
  void _handleDelete(Driver driver) async {
    try {
      await _driversCollection.doc(driver.id).delete();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Driver deleted successfully"),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Delete failed: ${e.toString()}"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Widget _buildRefreshIndicator(RefreshStatus status) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      child: Icon(
        Icons.autorenew,
        key: ValueKey(status),
        color: status == RefreshStatus.refreshing ? Colors.blue : Colors.grey,
        size: status == RefreshStatus.refreshing ? 28 : 24,
      ),
    );
  }

  /// Thêm textAlign và crossAxisAlignment để chắc chắn căn lề trái
  void _showDriverDetails(BuildContext context, Driver driver) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(
          driver.name,
          textAlign: TextAlign.left,
        ),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text("License Plate: ${driver.vehicleId}",
                  textAlign: TextAlign.left),
              Text("Phone: ${driver.phoneNumber}", textAlign: TextAlign.left),
              Text("Capacity: ${driver.vehicleLoad} kg",
                  textAlign: TextAlign.left),
              const SizedBox(height: 16),
              StatusIndicator(isActive: driver.available),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () =>
                EditDriverDialog.show(context, driver, _driversCollection),
            child: const Text('Edit'),
          ),
          TextButton(
            onPressed: () =>
                DeleteDialog.show(context, driver.id, _driversCollection),
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.black),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, color: Colors.red, size: 50),
          const SizedBox(height: 16),
          const Text(
            "Error loading data",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            icon: const Icon(Icons.refresh),
            label: const Text("Retry"),
            onPressed: _refreshData,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.black,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoading() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(Colors.black),
          ),
          SizedBox(height: 16),
          Text('Loading...'),
        ],
      ),
    );
  }

  Widget _buildEmptyState() => const Center(child: Text("No drivers available"));

  Future<void> _refreshData() async => _refreshController.refreshCompleted();
}
