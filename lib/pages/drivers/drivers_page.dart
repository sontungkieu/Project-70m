import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:pull_to_refresh/pull_to_refresh.dart';
import '../widgets/side_drawer.dart';

class DriversPage extends StatefulWidget {
  const DriversPage({Key? key}) : super(key: key);

  @override
  State<DriversPage> createState() => _DriversPageState();
}

class _DriversPageState extends State<DriversPage> {
  final CollectionReference driversCollection =
      FirebaseFirestore.instance.collection('Drivers');

  final TextEditingController _searchController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  // GlobalKey cho AnimatedList
  final GlobalKey<AnimatedListState> _listKey = GlobalKey<AnimatedListState>();

  // Refresh Controller từ pull_to_refresh
  final RefreshController _refreshController =
      RefreshController(initialRefresh: false);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const SideDrawer(),
      appBar: AppBar(
        title: const Text('Drivers Management'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            _buildHeaderSection(context),
            const SizedBox(height: 24),
            // Bọc AnimatedList trong pull-to-refresh
            Expanded(child: _buildDriverList()),
          ],
        ),
      ),
    );
  }

  Widget _buildHeaderSection(BuildContext context) {
    return Row(
      children: [
        _buildAddButton(context),
        const Spacer(),
        _buildSearchField(),
      ],
    );
  }

  Widget _buildAddButton(BuildContext context) {
    return ElevatedButton(
      onPressed: () => _showAddDriverDialog(context),
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.add, size: 20),
          SizedBox(width: 8),
          Text("Add Driver", style: TextStyle(fontSize: 16)),
        ],
      ),
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
      ),
    );
  }

  /// Build danh sách tài xế sử dụng AnimatedList và SmartRefresher
  Widget _buildDriverList() {
    return StreamBuilder<QuerySnapshot>(
      stream: driversCollection.snapshots(),
      builder: (context, snapshot) {
        if (snapshot.hasError) return _buildErrorWidget();
        if (snapshot.connectionState == ConnectionState.waiting)
          return _buildLoading();

        final data = snapshot.data;
        if (data == null || data.docs.isEmpty) return _buildEmptyState();

        // Chuyển về List để sử dụng AnimatedList
        final items = data.docs;

        return RefreshConfiguration(
          child: SmartRefresher(
            controller: _refreshController,
            onRefresh: _refreshData,
            header: CustomHeader(
              builder: (_, status) {
                return AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  child: Icon(
                    Icons.autorenew,
                    key: ValueKey(status),
                    color: status == RefreshStatus.refreshing
                        ? Colors.blue
                        : Colors.grey,
                    size: status == RefreshStatus.refreshing ? 28 : 24,
                  ),
                );
              },
            ),
            child: AnimatedList(
              key: _listKey,
              initialItemCount: items.length,
              itemBuilder: (context, index, animation) {
                final doc = items[index];
                final driver = doc.data() as Map<String, dynamic>;
                return SizeTransition(
                  sizeFactor: animation,
                  child: FadeTransition(
                    opacity: animation,
                    child: DriverCard(
                      doc: doc,
                      driver: driver,
                      onTap: () => _showDriverDetailModal(context, doc.id, driver),
                    ),
                  ),
                );
              },
            ),
          ),
        );
      },
    );
  }

  Widget _buildErrorWidget() {
    return const Center(child: Text("Error loading drivers"));
  }

  Widget _buildLoading() {
    return const Center(child: CircularProgressIndicator());
  }

  Widget _buildEmptyState() {
    return const Center(child: Text("No drivers available"));
  }

  Future<void> _refreshData() async {
    // Vì Firestore stream tự cập nhật nên chỉ cần gọi refreshCompleted
    _refreshController.refreshCompleted();
  }

  /// Hiệu ứng Transition cho Dialog được tích hợp trong helper này
  Future<T?> _showTransitionDialog<T>(Widget dialog) {
    return showGeneralDialog<T>(
      context: context,
      barrierDismissible: true,
      barrierLabel:
          MaterialLocalizations.of(context).modalBarrierDismissLabel,
      transitionDuration: const Duration(milliseconds: 400),
      pageBuilder: (context, animation, secondaryAnimation) {
        return dialog;
      },
      transitionBuilder: (context, animation, secondaryAnimation, child) {
        return ScaleTransition(
          scale: CurvedAnimation(
            parent: animation,
            curve: Curves.easeOutBack,
            reverseCurve: Curves.easeInBack,
          ),
          child: child,
        );
      },
    );
  }

  void _showAddDriverDialog(BuildContext context) {
    final Map<String, TextEditingController> controllers = {
      'name': TextEditingController(),
      'vehical_id': TextEditingController(),
      'phone_number': TextEditingController(),
      'vehical_load': TextEditingController(),
    };

    _showTransitionDialog(
      Dialog(
        backgroundColor: Colors.white,
        insetPadding: const EdgeInsets.all(24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Add New Driver',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w600,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  _buildFormField(
                    controller: controllers['name']!,
                    label: 'Driver Name',
                    validator: (value) =>
                        value!.isEmpty ? 'Required field' : null,
                  ),
                  const SizedBox(height: 16),
                  _buildFormField(
                    controller: controllers['vehical_id']!,
                    label: 'License Plate',
                    validator: (value) =>
                        value!.isEmpty ? 'Required field' : null,
                  ),
                  const SizedBox(height: 16),
                  _buildFormField(
                    controller: controllers['phone_number']!,
                    label: 'Phone Number',
                    keyboardType: TextInputType.phone,
                    validator: (value) =>
                        value!.isEmpty ? 'Required field' : null,
                  ),
                  const SizedBox(height: 16),
                  _buildFormField(
                    controller: controllers['vehical_load']!,
                    label: 'Vehicle Capacity (kg)',
                    keyboardType: TextInputType.number,
                    validator: (value) {
                      if (value!.isEmpty) return 'Required field';
                      if (int.tryParse(value) == null) return 'Invalid number';
                      return null;
                    },
                  ),
                  const SizedBox(height: 32),
                  ElevatedButton(
                    onPressed: () async {
                      if (_formKey.currentState!.validate()) {
                        try {
                          await driversCollection.add({
                            'name': controllers['name']!.text.trim(),
                            'vehical_id':
                                controllers['vehical_id']!.text.trim(),
                            'phone_number':
                                controllers['phone_number']!.text.trim(),
                            'vehical_load': int.tryParse(
                                    controllers['vehical_load']!.text.trim()) ??
                                0,
                            'available': true,
                          });
                          Navigator.pop(context);
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text("Driver added successfully"),
                              backgroundColor: Colors.greenAccent,
                            ),
                          );
                        } catch (e) {
                          Navigator.pop(context);
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text("Failed to add driver"),
                              backgroundColor: Colors.redAccent,
                            ),
                          );
                        }
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.black,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text('Add Driver'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFormField({
    required TextEditingController controller,
    required String label,
    TextInputType? keyboardType,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      validator: validator,
      decoration: InputDecoration(
        labelText: label,
        floatingLabelBehavior: FloatingLabelBehavior.auto,
        filled: true,
        fillColor: Colors.grey.shade50,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: Colors.grey),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: Colors.grey.shade600),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
    );
  }

  void _showDriverDetailModal(
      BuildContext context, String docId, Map<String, dynamic> driver) {
    _showTransitionDialog(
      Dialog(
        backgroundColor: Colors.white,
        insetPadding: const EdgeInsets.all(24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  driver['name'] ?? 'Driver Details',
                  style: const TextStyle(
                      fontSize: 22, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 16),
                Text("License Plate: ${driver['vehical_id'] ?? '-'}"),
                const SizedBox(height: 8),
                Text("Phone: ${driver['phone_number'] ?? '-'}"),
                const SizedBox(height: 8),
                Text("Capacity: ${driver['vehical_load']?.toString() ?? '-'} kg"),
                const SizedBox(height: 8),
                _buildStatusIndicator(driver['available']),
                const SizedBox(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton(
                      onPressed: () {
                        Navigator.pop(context);
                        _showEditDriverDialog(context, docId, driver);
                      },
                      child: const Text("Edit"),
                    ),
                    const SizedBox(width: 8),
                    TextButton(
                      onPressed: () {
                        Navigator.pop(context);
                        _showDeleteConfirmDialog(context, docId);
                      },
                      child: const Text("Delete",
                          style: TextStyle(color: Colors.red)),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      style:
                          ElevatedButton.styleFrom(backgroundColor: Colors.black),
                      child: const Text("Close"),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showEditDriverDialog(BuildContext context, String docId, Map<String, dynamic> driver) {
  final Map<String, TextEditingController> controllers = {
    'name': TextEditingController(text: driver['name']),
    'vehical_id': TextEditingController(text: driver['vehical_id']),
    'phone_number': TextEditingController(text: driver['phone_number']),
    'vehical_load': TextEditingController(text: driver['vehical_load']?.toString() ?? ''),
  };

  bool available = driver['available'] ?? false;

  _showTransitionDialog(
    Dialog(
      backgroundColor: Colors.white,
      insetPadding: const EdgeInsets.all(24),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: StatefulBuilder(
        builder: (BuildContext context, StateSetter setStateDialog) {
          return Padding(
            padding: const EdgeInsets.all(24),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Edit Driver',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  _buildFormField(
                    controller: controllers['name']!,
                    label: 'Driver Name',
                    validator: (value) => value!.isEmpty ? 'Required field' : null,
                  ),
                  const SizedBox(height: 16),
                  _buildFormField(
                    controller: controllers['vehical_id']!,
                    label: 'License Plate',
                    validator: (value) => value!.isEmpty ? 'Required field' : null,
                  ),
                  const SizedBox(height: 16),
                  _buildFormField(
                    controller: controllers['phone_number']!,
                    label: 'Phone Number',
                    keyboardType: TextInputType.phone,
                    validator: (value) => value!.isEmpty ? 'Required field' : null,
                  ),
                  const SizedBox(height: 16),
                  _buildFormField(
                    controller: controllers['vehical_load']!,
                    label: 'Vehicle Capacity (kg)',
                    keyboardType: TextInputType.number,
                    validator: (value) {
                      if (value!.isEmpty) return 'Required field';
                      if (int.tryParse(value) == null) return 'Invalid number';
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text("Active Status"),
                      Switch(
                        value: available,
                        onChanged: (value) {
                          setStateDialog(() {
                            available = value;
                          });
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: () async {
                      try {
                        await driversCollection.doc(docId).update({
                          'name': controllers['name']!.text.trim(),
                          'vehical_id': controllers['vehical_id']!.text.trim(),
                          'phone_number': controllers['phone_number']!.text.trim(),
                          'vehical_load': int.tryParse(controllers['vehical_load']!.text.trim()) ?? 0,
                          'available': available,
                        });
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text("Driver updated successfully"),
                            backgroundColor: Colors.greenAccent,
                          ),
                        );
                      } catch (e) {
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text("Failed to update driver"),
                            backgroundColor: Colors.redAccent,
                          ),
                        );
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.black,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text("Save Changes"),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    ),
  );
}


  void _showDeleteConfirmDialog(BuildContext context, String docId) {
    _showTransitionDialog(
      Dialog(
        backgroundColor: Colors.red.shade50,
        insetPadding: const EdgeInsets.all(24),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Confirm Delete',
                style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w600,
                    color: Colors.red),
              ),
              const SizedBox(height: 16),
              const Text("Are you sure you want to delete this driver?"),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text("Cancel"),
                  ),
                  const SizedBox(width: 16),
                  ElevatedButton(
                    onPressed: () async {
                      try {
                        await driversCollection.doc(docId).delete();
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text("Driver deleted successfully"),
                            backgroundColor: Colors.greenAccent,
                          ),
                        );
                      } catch (e) {
                        Navigator.pop(context);
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text("Failed to delete driver"),
                            backgroundColor: Colors.redAccent,
                          ),
                        );
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text("Delete"),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Widget Status Indicator với hiệu ứng pulse sử dụng AnimatedContainer
  Widget _buildStatusIndicator(bool? available) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: available == true ? Colors.green.shade100 : Colors.red.shade100,
        borderRadius: BorderRadius.circular(20),
        boxShadow: available == true
            ? [
                BoxShadow(
                  color: Colors.green.shade200,
                  blurRadius: 8,
                  spreadRadius: 1,
                )
              ]
            : [],
      ),
      child: Text(
        available == true ? 'Active' : 'Inactive',
        style: TextStyle(
          color: available == true ? Colors.green.shade800 : Colors.red.shade800,
          fontWeight: FontWeight.w500,
          fontSize: 13,
        ),
      ),
    );
  }
}

/// Widget riêng cho DriverCard với hiệu ứng Hover
class DriverCard extends StatefulWidget {
  final QueryDocumentSnapshot doc;
  final Map<String, dynamic> driver;
  final VoidCallback onTap;

  const DriverCard({
    Key? key,
    required this.doc,
    required this.driver,
    required this.onTap,
  }) : super(key: key);

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
          shadowColor: Colors.black.withOpacity(0.1),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
            side: BorderSide(color: Colors.grey.shade200, width: 1),
          ),
          child: InkWell(
            onTap: widget.onTap,
            borderRadius: BorderRadius.circular(14),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
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
                              widget.driver['name'] ?? '',
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              widget.driver['vehical_id'] ?? '-',
                              style: TextStyle(
                                color: Colors.grey.shade600,
                                fontSize: 15,
                              ),
                            ),
                          ],
                        ),
                      ),
                      // Sử dụng AnimatedContainer cho hiệu ứng pulse của Status Indicator
                      _buildStatusIndicator(widget.driver['available']),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text("Phone: ${widget.driver['phone_number'] ?? '-'}",
                          style: const TextStyle(fontSize: 14)),
                      const SizedBox(height: 4),
                      Text("Capacity: ${widget.driver['vehical_load']?.toString() ?? '-'} kg",
                          style: const TextStyle(fontSize: 14)),
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

  Widget _buildStatusIndicator(bool? available) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: available == true ? Colors.green.shade100 : Colors.red.shade100,
        borderRadius: BorderRadius.circular(20),
        boxShadow: available == true
            ? [
                BoxShadow(
                  color: Colors.green.shade200,
                  blurRadius: 8,
                  spreadRadius: 1,
                )
              ]
            : [],
      ),
      child: Text(
        available == true ? 'Active' : 'Inactive',
        style: TextStyle(
          color: available == true ? Colors.green.shade800 : Colors.red.shade800,
          fontWeight: FontWeight.w500,
          fontSize: 13,
        ),
      ),
    );
  }
}
