// drivers/widgets/dialogs/edit_driver_dialog.dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../models/driver_model.dart';
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../models/driver_model.dart';
class EditDriverDialog {
  static void show(BuildContext context, Driver driver, CollectionReference collection) {
    showDialog(
      context: context,
      builder: (context) => _EditDriverDialogContent(
        driver: driver,
        collection: collection,
      ),
    );
  }
}

class _EditDriverDialogContent extends StatefulWidget {
  final Driver driver;
  final CollectionReference collection;

  const _EditDriverDialogContent({
    required this.driver,
    required this.collection,
  });

  @override
  State<_EditDriverDialogContent> createState() => __EditDriverDialogContentState();
}

class __EditDriverDialogContentState extends State<_EditDriverDialogContent> {
  late final Map<String, TextEditingController> _controllers;
  late bool _isActive;

  @override
  void initState() {
    super.initState();
    _isActive = widget.driver.available;
    _controllers = {
      'name': TextEditingController(text: widget.driver.name),
      'vehical_id': TextEditingController(text: widget.driver.vehicleId),
      'phone_number': TextEditingController(text: widget.driver.phoneNumber),
      'vehical_load': TextEditingController(text: widget.driver.vehicleLoad.toString()),
    };
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Edit Driver'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _buildFormField('Driver Name', 'name'),
            _buildFormField('License Plate', 'vehical_id'),
            _buildFormField('Phone Number', 'phone_number',
                keyboardType: TextInputType.phone),
            _buildFormField('Vehicle Capacity', 'vehical_load',
                keyboardType: TextInputType.number),
            _buildActiveSwitch(),
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
          child: const Text('Save Changes'),
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

  Widget _buildActiveSwitch() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        const Text('Active Status'),
        Switch(
          value: _isActive,
          onChanged: (value) => setState(() => _isActive = value),
        ),
      ],
    );
  }

  void _submitForm() {
    if (_validateForm()) {
      widget.collection.doc(widget.driver.id).update({
        'name': _controllers['name']!.text.trim(),
        'vehical_id': _controllers['vehical_id']!.text.trim(),
        'phone_number': _controllers['phone_number']!.text.trim(),
        'vehical_load': int.parse(_controllers['vehical_load']!.text.trim()),
        'available': _isActive,
      }).then((_) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Driver updated successfully'),
            backgroundColor: Colors.green,
          ),
        );
      }).catchError((error) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Update failed: ${error.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      });
    }
  }

  bool _validateForm() {
    return _controllers.values.every((controller) => controller.text.isNotEmpty);
  }
}