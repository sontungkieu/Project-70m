import 'package:flutter/material.dart';
import '../widgets/side_drawer.dart';

class PayrollPage extends StatelessWidget {
  const PayrollPage({Key? key}) : super(key: key);

  // Dữ liệu giả
  final List<Map<String, dynamic>> samplePayroll = const [
    {
      "name": "John Driver",
      "id": "DRV-001",
      "base": 3000,
      "overtime": 500,
      "deductions": 200,
      "total": 3300,
    },
    {
      "name": "Sarah Smith",
      "id": "DRV-002",
      "base": 3000,
      "overtime": 300,
      "deductions": 150,
      "total": 3150,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const SideDrawer(),
      appBar: AppBar(
      title: const Text('Payroll'),
      backgroundColor: Colors.black,
      foregroundColor: Colors.white,
      elevation: 0,
    )
    ,
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Tiêu đề tháng, vv.
            Row(
              children: [
                Text(
                  "January 2025",
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const Spacer(),
                // Dropdown chọn tháng
                DropdownButton<String>(
                  value: "January 2025",
                  items: const [
                    DropdownMenuItem(child: Text("January 2025"), value: "January 2025"),
                    DropdownMenuItem(child: Text("February 2025"), value: "February 2025"),
                  ],
                  onChanged: (value) {
                    // TODO: Xử lý tháng
                  },
                ),
                const SizedBox(width: 8),
                // Tìm kiếm
                SizedBox(
                  width: 200,
                  child: TextField(
                    decoration: InputDecoration(
                      labelText: "Search driver...",
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      prefixIcon: const Icon(Icons.search),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Bảng lương
            Expanded(
              child: Card(
                child: Column(
                  children: [
                    Expanded(
                      child: ListView.builder(
                        itemCount: samplePayroll.length,
                        itemBuilder: (context, index) {
                          final p = samplePayroll[index];
                          return ListTile(
                            leading: CircleAvatar(
                              child: Text(p["id"].toString().split('-').last),
                            ),
                            title: Text("${p["name"]}"),
                            subtitle: Text("ID: ${p["id"]}"),
                            trailing: Text("\$${p["total"]}"),
                          );
                        },
                      ),
                    ),
                    // Tổng hợp lương
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: const [
                              Text("Total Amount Payable"),
                              SizedBox(height: 4),
                              Text(
                                "\$56,450",
                                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: const [
                              Text("Drivers Paid"),
                              SizedBox(height: 4),
                              Text(
                                "18/20",
                                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Hàng nút
            Row(
              children: [
                ElevatedButton(
                  onPressed: () {
                    // TODO: Export to CSV
                  },
                  child: const Text("Export to CSV"),
                ),
                const SizedBox(width: 16),
                ElevatedButton(
                  onPressed: () {
                    // TODO: In bảng lương
                  },
                  child: const Text("Print Salary Sheet"),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
