import 'package:flutter/material.dart';
import '../widgets/side_drawer.dart';

class SchedulePage extends StatefulWidget {
  const SchedulePage({Key? key}) : super(key: key);

  @override
  State<SchedulePage> createState() => _SchedulePageState();
}

class _SchedulePageState extends State<SchedulePage> {
  bool isProcessing = false;
  bool isGenerated = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      drawer: const SideDrawer(),
      appBar: AppBar(
        title: const Text('Schedule'),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Khu vực Upload
            _buildCard(
              title: "Upload Transport Requests",
              child: SizedBox(
                height: 150,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.file_upload, size: 40),
                      const SizedBox(height: 8),
                      ElevatedButton(
                        onPressed: () {
                          // TODO: Thêm logic upload file
                        },
                        child: const Text("Upload Excel File"),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Khu vực Generate Schedule
            _buildCard(
              title: "Generate Schedule",
              child: SizedBox(
                height: 100,
                child: Center(
                  child: ElevatedButton.icon(
                    onPressed: isProcessing
                        ? null
                        : () {
                            setState(() {
                              isProcessing = true;
                            });
                            // Mô phỏng xử lý trong 2 giây
                            Future.delayed(const Duration(seconds: 2), () {
                              setState(() {
                                isProcessing = false;
                                isGenerated = true;
                              });
                            });
                          },
                    icon: const Icon(Icons.schedule),
                    label: isProcessing
                        ? const Text("Processing...")
                        : const Text("Generate Schedule"),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Khu vực Download
            _buildCard(
              title: "Download Schedule",
              child: SizedBox(
                height: 100,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (isGenerated)
                        const Text("Schedule has been generated successfully!"),
                      const SizedBox(height: 8),
                      ElevatedButton(
                        onPressed: isGenerated ? () {} : null,
                        child: const Text("Download Schedule"),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Widget helper tạo card
  Widget _buildCard({required String title, required Widget child}) {
    return Card(
      elevation: 0,
      color: Colors.grey.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text(
              title,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            const SizedBox(height: 8),
            child,
          ],
        ),
      ),
    );
  }
}
