# my_logistic_app

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.


## Cài đặt trên Windows

1. **Cài đặt công cụ**:
   - Flutter SDK: [Hướng dẫn cài đặt](https://docs.flutter.dev/get-started/install/windows)
   - Android Studio (với Android SDK và Android Emulator)
   - Visual Studio (nếu build cho Windows)
   - Java JDK 11+

2. **Clone dự án**:
   ```bash
   git clone https://github.com/[username]/[repo-name].git
   cd [repo-name]



   
---

### **4. Kiểm tra cấu hình build**
- **Android**: Đảm bảo file `android/build.gradle` không chứa đường dẫn Linux-specific (ví dụ: `sdk.dir` trong WSL).
- **Windows**: Nếu dự án hỗ trợ Windows, thêm file `windows/CMakeLists.txt` và kiểm tra các dependency.

---

### **5. Ví dụ file pubspec.yaml**
```yaml
name: my_flutter_app
description: A sample Flutter project

version: 1.0.0+1

environment:
  sdk: ">=3.0.0 <4.0.0"  # Đặt phiên bản Dart SDK tương thích

dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0  # Ví dụ package với phiên bản cố định
  provider: ^6.0.5

dev_dependencies:
  flutter_test:
    sdk: flutter
