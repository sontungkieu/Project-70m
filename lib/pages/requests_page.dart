import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:pull_to_refresh/pull_to_refresh.dart';
import '../../widgets/side_drawer.dart';

/// -------------------- Model: Request --------------------
class Request {
  final String id; // Firestore doc ID
  final DateTime date;
  final bool deliveryStatus;
  final String deliveryTime;
  final String endPlace;
  final String name;
  final String note;
  final String requestId;
  final String splitId;
  final String staffId;
  final String startPlace;
  final String timeframe;
  final int weight;

  Request({
    required this.id,
    required this.date,
    required this.deliveryStatus,
    required this.deliveryTime,
    required this.endPlace,
    required this.name,
    required this.note,
    required this.requestId,
    required this.splitId,
    required this.staffId,
    required this.startPlace,
    required this.timeframe,
    required this.weight,
  });

  factory Request.fromFirestore(QueryDocumentSnapshot doc) {
    final data = doc.data() as Map<String, dynamic>;
    return Request(
      id: doc.id,
      date: (data['date'] as Timestamp).toDate(),
      deliveryStatus: data['delivery_status'] ?? false,
      deliveryTime: data['delivery_time'] ?? '',
      endPlace: data['end_place'] ?? '',
      name: data['name'] ?? '',
      note: data['note'] ?? '',
      requestId: data['request_id'] ?? '',
      splitId: data['split_id'] ?? '',
      staffId: data['staff_id'] ?? '',
      startPlace: data['start_place'] ?? '',
      timeframe: data['timeframe'] ?? '',
      weight: data['weight'] ?? 0,
    );
  }
}

/// -------------------- Widget: RequestCard --------------------

// import '../models/request_model.dart';

class RequestCard extends StatelessWidget {
  final Request request;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;
   // Thêm callback onEdit

  const RequestCard({
    Key? key,
    required this.request,
    this.onTap,
    this.onDelete,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Card(
        margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        color: const Color(0xFFF8F5FE), // Ví dụ màu tím nhạt (tùy ý)
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Phần text hiển thị thông tin
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Tên đơn hàng
                    Text(
                      request.name,
                      style: const TextStyle(
                        fontSize: 18, 
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 6),
                    // Từ đâu
                    Text("From: ${request.startPlace}"),
                    // Tới đâu
                    Text("To: ${request.endPlace}"),
                    // Ngày
                    Text("Date: ${request.date.toLocal().toString().split(' ')[0]}"),
                    // Thời gian giao (nếu muốn)
                    Text("Delivery Time: ${request.deliveryTime}"),
                    // Trạng thái giao (Pending/Done)
                    Text("Status: ${request.deliveryStatus ? 'Done' : 'Pending'}"),
                    // Staff ID (nếu muốn hiển thị)
                    if (request.staffId.isNotEmpty)
                      Text("Staff: ${request.staffId}"),
                    // Weight (trọng lượng)
                    if (request.weight > 0)
                      Text("Weight: ${request.weight} kg"),
                  ],
                ),
              ),
              // Nút xóa ở góc phải
              // 2 nút: Edit & Delete
            
              IconButton(
                icon: const Icon(Icons.delete, color: Colors.red),
                onPressed: onDelete,
              ),
            ],
          ),
        ),
      ),
    );
  }
}


/// -------------------- Trang: RequestsPage --------------------
class RequestsPage extends StatefulWidget {
  const RequestsPage({Key? key}) : super(key: key);

  @override
  State<RequestsPage> createState() => _RequestsPageState();
}

class _RequestsPageState extends State<RequestsPage> {
  final RefreshController _refreshController = RefreshController();
  final TextEditingController _searchController = TextEditingController();

  /// Tên collection "Requests" (chữ R viết hoa)
  final CollectionReference _requestsCollection =
      FirebaseFirestore.instance.collection('Requests');

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const SideDrawer(),
      appBar: AppBar(
        title: const Text('Requests Management'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildHeader(),
            const SizedBox(height: 24),
            Expanded(child: _buildRequestList()),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Row(
      children: [
        ElevatedButton(
          onPressed: () => AddRequestDialog.show(context, _requestsCollection),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.black,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
          child: const Text("Add Request"),
        ),
        const Spacer(),
        SizedBox(
          width: 280,
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              filled: true,
              fillColor: Colors.grey[100],
              hintText: "Search by date (e.g. 2025-02)",
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              prefixIcon: const Icon(Icons.search, color: Colors.grey),
              contentPadding: const EdgeInsets.symmetric(vertical: 14),
            ),
            onChanged: (value) => setState(() {}), 
          ),
        ),
      ],
    );
  }

  Widget _buildRequestList() {
    return StreamBuilder<QuerySnapshot>(
      stream: _requestsCollection.snapshots(),
      builder: (context, snapshot) {
        if (snapshot.hasError) return _buildErrorWidget();
        if (snapshot.connectionState == ConnectionState.waiting) {
          return _buildLoading();
        }
        if (!snapshot.hasData || snapshot.data!.docs.isEmpty) {
          return _buildEmptySearch(); // Hoặc 1 widget "No data"
        }

        final allRequests = _parseRequests(snapshot.data!.docs);
        final filtered = _filterByDate(allRequests, _searchController.text);

        if (filtered.isEmpty) return _buildEmptySearch();

        return _buildRefreshableList(filtered);
      },
    );
  }

  List<Request> _parseRequests(List<QueryDocumentSnapshot> docs) {
    return docs.map((doc) => Request.fromFirestore(doc)).toList();
  }

  /// Lọc request theo date (chuỗi so sánh)
  List<Request> _filterByDate(List<Request> requests, String query) {
    final dateQuery = query.toLowerCase().trim();
    if (dateQuery.isEmpty) return requests;

    return requests.where((req) {
      final dateStr = req.date.toLocal().toString().split(' ')[0]; 
      return dateStr.toLowerCase().contains(dateQuery);
    }).toList();
  }

  Widget _buildRefreshableList(List<Request> requests) {
    return SmartRefresher(
      controller: _refreshController,
      onRefresh: _refreshData,
      child: ListView.builder(
        itemCount: requests.length,
        itemBuilder: (context, index) {
          return RequestCard(
            request: requests[index],
            onTap: () => _showRequestDetails(requests[index]),
            onDelete: () => _handleDelete(requests[index]),
          );
        },
      ),
    );
  }

  void _showRequestDetails(Request req) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(req.name),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Request ID: ${req.requestId}"),
              Text("Staff ID: ${req.staffId}"),
              Text("Date: ${req.date.toLocal()}"),
              Text("Start: ${req.startPlace}"),
              Text("End: ${req.endPlace}"),
              Text("Weight: ${req.weight}"),
              Text("Delivery Status: ${req.deliveryStatus ? 'Done' : 'Pending'}"),
              Text("Note: ${req.note}"),
            ],
          ),
        ),
        actions: [
          // Nút Edit
        TextButton(
          onPressed: () {
            Navigator.pop(ctx); // đóng dialog detail
            // Mở dialog edit
            EditRequestDialog.show(context, req, _requestsCollection);
          },
          child: const Text("Edit"),
        ),
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Close"),
          ),
        ],
      ),
    );
  }

  void _handleDelete(Request req) async {
    try {
      await _requestsCollection.doc(req.id).delete();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Request deleted successfully"),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Delete failed: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _refreshData() async {
    _refreshController.refreshCompleted();
  }

  Widget _buildEmptySearch() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search_off, size: 50, color: Colors.grey.shade400),
          const SizedBox(height: 16),
          Text(
            "No matching requests found",
            style: TextStyle(
              color: Colors.grey.shade600,
              fontSize: 16,
            ),
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
          CircularProgressIndicator(valueColor: AlwaysStoppedAnimation<Color>(Colors.black)),
          SizedBox(height: 16),
          Text('Loading...'),
        ],
      ),
    );
  }
}

/// -------------------- Dialog: AddRequestDialog --------------------
class AddRequestDialog extends StatefulWidget {
  final CollectionReference requestsCollection;

  const AddRequestDialog._({Key? key, required this.requestsCollection})
      : super(key: key);

  /// Hàm tĩnh tiện lợi để show dialog
  static void show(BuildContext context, CollectionReference collection) {
    showDialog(
      context: context,
      builder: (ctx) => AddRequestDialog._(requestsCollection: collection),
    );
  }

  @override
  State<AddRequestDialog> createState() => _AddRequestDialogState();
}

class _AddRequestDialogState extends State<AddRequestDialog> {
  final _formKey = GlobalKey<FormState>();

  // Các TextEditingController cho trường request
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _requestIdController = TextEditingController();
  final TextEditingController _staffIdController = TextEditingController();
  final TextEditingController _startPlaceController = TextEditingController();
  final TextEditingController _endPlaceController = TextEditingController();
  final TextEditingController _noteController = TextEditingController();
  final TextEditingController _deliveryTimeController = TextEditingController();
  final TextEditingController _timeframeController = TextEditingController();
  final TextEditingController _splitIdController = TextEditingController();
  final TextEditingController _weightController = TextEditingController();

  bool _deliveryStatus = false;
  DateTime _selectedDate = DateTime.now();

  // Xử lý thêm request vào Firestore
  Future<void> _addRequest() async {
    if (!_formKey.currentState!.validate()) return;

    // Tạo map data
    final data = {
      'name': _nameController.text.trim(),
      'request_id': _requestIdController.text.trim(),
      'staff_id': _staffIdController.text.trim(),
      'start_place': _startPlaceController.text.trim(),
      'end_place': _endPlaceController.text.trim(),
      'note': _noteController.text.trim(),
      'delivery_time': _deliveryTimeController.text.trim(),
      'timeframe': _timeframeController.text.trim(),
      'split_id': _splitIdController.text.trim(),
      'weight': int.tryParse(_weightController.text.trim()) ?? 0,
      'delivery_status': _deliveryStatus,
      'date': Timestamp.fromDate(_selectedDate),
    };

    try {
      await widget.requestsCollection.add(data);
      Navigator.pop(context); // đóng dialog
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Request added successfully"),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Failed to add request: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      setState(() {
        _selectedDate = picked;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text("Add New Request"),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildTextField(_nameController, "Name", true),
              _buildTextField(_requestIdController, "Request ID", true),
              _buildTextField(_staffIdController, "Staff ID", false),
              _buildTextField(_startPlaceController, "Start Place", false),
              _buildTextField(_endPlaceController, "End Place", false),
              _buildTextField(_noteController, "Note", false),
              _buildTextField(_deliveryTimeController, "Delivery Time", false),
              _buildTextField(_timeframeController, "Timeframe", false),
              _buildTextField(_splitIdController, "Split ID", false),
              _buildTextField(_weightController, "Weight", false, number: true),
              // Date
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text("Date: ${_selectedDate.toLocal().toString().split(' ')[0]}"),
                  TextButton(
                    onPressed: _pickDate,
                    child: const Text("Pick Date"),
                  ),
                ],
              ),
              // Delivery Status
              Row(
                children: [
                  const Text("Delivery Status: "),
                  Switch(
                    value: _deliveryStatus,
                    onChanged: (val) {
                      setState(() {
                        _deliveryStatus = val;
                      });
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text("Cancel"),
        ),
        ElevatedButton(
          onPressed: _addRequest,
          child: const Text("Add"),
        ),
      ],
    );
  }

  Widget _buildTextField(
    TextEditingController controller,
    String label,
    bool requiredField, {
    bool number = false,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: number ? TextInputType.number : TextInputType.text,
      decoration: InputDecoration(
        labelText: label,
      ),
      validator: (value) {
        if (requiredField && (value == null || value.trim().isEmpty)) {
          return "Field is required";
        }
        return null;
      },
    );
  }
}



class EditRequestDialog extends StatefulWidget {
  final Request request;                   // Dữ liệu gốc của request
  final CollectionReference requestsCollection; // Reference tới collection

  const EditRequestDialog._({
    Key? key,
    required this.request,
    required this.requestsCollection,
  }) : super(key: key);

  /// Hàm tiện ích static để mở dialog
  static void show(
    BuildContext context,
    Request request,
    CollectionReference requestsCollection,
  ) {
    showDialog(
      context: context,
      builder: (ctx) => EditRequestDialog._(
        request: request,
        requestsCollection: requestsCollection,
      ),
    );
  }

  @override
  State<EditRequestDialog> createState() => _EditRequestDialogState();
}

//editdialog------------------------------------------------------------

class _EditRequestDialogState extends State<EditRequestDialog> {
  final _formKey = GlobalKey<FormState>();

  // Các TextEditingController, khởi tạo giá trị ban đầu
  late TextEditingController _nameController;
  late TextEditingController _staffIdController;
  late TextEditingController _startPlaceController;
  late TextEditingController _endPlaceController;
  late TextEditingController _deliveryTimeController;
  late TextEditingController _timeframeController;
  late TextEditingController _noteController;
  late TextEditingController _weightController;

  bool _deliveryStatus = false;
  DateTime _selectedDate = DateTime.now(); // user có thể chọn ngày

  @override
  void initState() {
    super.initState();
    // Gán dữ liệu ban đầu từ request
    final req = widget.request;
    _nameController = TextEditingController(text: req.name);
    _staffIdController = TextEditingController(text: req.staffId);
    _startPlaceController = TextEditingController(text: req.startPlace);
    _endPlaceController = TextEditingController(text: req.endPlace);
    _deliveryTimeController = TextEditingController(text: req.deliveryTime);
    _timeframeController = TextEditingController(text: req.timeframe);
    _noteController = TextEditingController(text: req.note);
    _weightController = TextEditingController(text: req.weight.toString());

    _deliveryStatus = req.deliveryStatus;
    // Lấy date cũ (nếu có) thay vì now
    _selectedDate = req.date;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _staffIdController.dispose();
    _startPlaceController.dispose();
    _endPlaceController.dispose();
    _deliveryTimeController.dispose();
    _timeframeController.dispose();
    _noteController.dispose();
    _weightController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      setState(() {
        _selectedDate = picked;
      });
    }
  }

  Future<void> _updateRequest() async {
    if (!_formKey.currentState!.validate()) return;

    final updatedData = {
      'name': _nameController.text.trim(),
      'staff_id': _staffIdController.text.trim(),
      'start_place': _startPlaceController.text.trim(),
      'end_place': _endPlaceController.text.trim(),
      'delivery_time': _deliveryTimeController.text.trim(),
      'timeframe': _timeframeController.text.trim(),
      'note': _noteController.text.trim(),
      'weight': int.tryParse(_weightController.text.trim()) ?? 0,
      'delivery_status': _deliveryStatus,
      'date': Timestamp.fromDate(_selectedDate),
      // request_id, split_id,... nếu muốn cập nhật
    };

    try {
      // Cập nhật document với ID = widget.request.id
      await widget.requestsCollection.doc(widget.request.id).update(updatedData);
      Navigator.pop(context); 
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Request updated successfully"),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Failed to update request: $e"),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text("Edit Request"),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildTextField(_nameController, "Name", true),
              _buildTextField(_staffIdController, "Staff ID", false),
              _buildTextField(_startPlaceController, "Start Place", false),
              _buildTextField(_endPlaceController, "End Place", false),
              _buildTextField(_deliveryTimeController, "Delivery Time", false),
              _buildTextField(_timeframeController, "Timeframe", false),
              _buildTextField(_noteController, "Note", false),
              _buildTextField(_weightController, "Weight", false, number: true),
              const SizedBox(height: 10),
              // Date
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text("Date: ${_selectedDate.toLocal().toString().split(' ')[0]}"),
                  TextButton(
                    onPressed: _pickDate,
                    child: const Text("Pick Date"),
                  ),
                ],
              ),
              // Delivery status
              Row(
                children: [
                  const Text("Delivery Status: "),
                  Switch(
                    value: _deliveryStatus,
                    onChanged: (val) {
                      setState(() {
                        _deliveryStatus = val;
                      });
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text("Cancel"),
        ),
        ElevatedButton(
          onPressed: _updateRequest,
          child: const Text("Save"),
        ),
      ],
    );
  }

  Widget _buildTextField(
    TextEditingController controller,
    String label,
    bool requiredField, {
    bool number = false,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: number ? TextInputType.number : TextInputType.text,
      decoration: InputDecoration(labelText: label),
      validator: (value) {
        if (requiredField && (value == null || value.trim().isEmpty)) {
          return "Field is required";
        }
        return null;
      },
    );
  }
}
