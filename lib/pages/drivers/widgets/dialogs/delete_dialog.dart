

// drivers/widgets/dialogs/delete_dialog.dart
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
class DeleteDialog {
  static void show(BuildContext context, String driverId, CollectionReference collection) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Delete'),
        content: const Text('Are you sure you want to delete this driver?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => _deleteDriver(context, driverId, collection),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  static void _deleteDriver(BuildContext context, String driverId, CollectionReference collection) {
    collection.doc(driverId).delete().then((_) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Driver deleted successfully'),
          backgroundColor: Colors.green,
        ),
      );
    }).catchError((error) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Delete failed: ${error.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    });
  }
}