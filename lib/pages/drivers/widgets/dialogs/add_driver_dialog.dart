// drivers/widgets/dialogs/add_driver_dialog.dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class AddDriverDialog {
  static void show(BuildContext context, CollectionReference collection) {
    showDialog(
      context: context,
      builder: (context) => _AddDriverDialogContent(collection: collection),
    );
  }
}

class _AddDriverDialogContent extends StatefulWidget {
  final CollectionReference collection;

  const _AddDriverDialogContent({required this.collection});

  @override
  State<_AddDriverDialogContent> createState() => __AddDriverDialogContentState();
}

class __AddDriverDialogContentState extends State<_AddDriverDialogContent> {
  final _formKey = GlobalKey<FormState>();
  late final Map<String, TextEditingController> _controllers;

  
  @override
  void initState() {
    super.initState();
    _controllers = {
      'name': TextEditingController(),
      'cccd': TextEditingController(), // Thêm controller CCCD
      'vehical_id': TextEditingController(),
      'phone_number': TextEditingController(),
      'vehical_load': TextEditingController(),
    };
  }


  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add New Driver'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildFormField('Driver Name', 'name'),
            _buildFormField('License Plate', 'vehical_id'),
            _buildFormField('Phone Number', 'phone_number',
                keyboardType: TextInputType.phone),
            _buildFormField('CCCD', 'cccd'), // Thêm trường CCCD
            _buildFormField('Vehicle Capacity', 'vehical_load',
                keyboardType: TextInputType.number),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _submitForm,
          child: const Text('Save'),
        ),
      ],
    );
  }

  Widget _buildFormField(String label, String key,
      {TextInputType? keyboardType}) {
    return TextFormField(
      controller: _controllers[key],
      decoration: InputDecoration(labelText: label),
      keyboardType: keyboardType,
      validator: (value) => value!.isEmpty ? 'Required field' : null,
    );
  }

 void _submitForm() {
    if (_formKey.currentState!.validate()) {
      widget.collection.add({
        'name': _controllers['name']!.text.trim(),
        'cccd': _controllers['cccd']!.text.trim(), // Thêm CCCD
        'vehical_id': _controllers['vehical_id']!.text.trim(),
        'phone_number': _controllers['phone_number']!.text.trim(),
        'vehical_load': int.parse(_controllers['vehical_load']!.text.trim()),
        'salary': 0, // Mặc định salary = 0
        'available': true,
        'route_by_day': null,
        'route_by_month': null,
        'all_route_history': null,
      });
      Navigator.pop(context);
    }
  }

}