# 🚚 Optimized Delivery Dispatching System

An intelligent and efficient solution designed to streamline vehicle dispatching, optimize delivery routes, and enhance driver productivity using advanced algorithms and cloud-based technologies.
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://github.com/sontungkieu/Project-70m)
## 🌟 Key Features

- **Intelligent Route Optimization:** Utilizes Google's OR-Tools to calculate optimal delivery routes, minimizing distance and balancing driver workloads.
- **Real-time Dispatch Management:** Allows dispatchers to easily manage, upload, and modify delivery schedules through an intuitive interface.
- **Driver Mobile Application:** Provides drivers with clear daily delivery schedules, route details, and real-time notifications via Firebase Cloud Messaging (FCM).
- **Advanced Analytics:** Tracks and visualizes delivery metrics, driver efficiency, and monthly accumulated salaries based on distances traveled.

## 🛠️ Technology Stack

- **Frontend:** Flutter & FlutterFlow for a beautiful, responsive, and cross-platform UI (iOS, Android, Web, and Desktop).
- **Backend:** Python (Flask) running on Google Cloud Run, integrating Google's OR-Tools for route optimization.
- **Database & Storage:** Firebase Firestore for real-time data storage and synchronization.
- **Authentication & Security:** Firebase Authentication and App Check ensure secure, authorized access.
- **Notifications:** Firebase Cloud Messaging (FCM) for real-time driver notifications.

## ⚙️ Project Structure
```
- app.py (Flask API)
- optimization_engine.py (OR-Tools integration)
- config.py (Route configuration and parameters)
- utilities/
  ├── firestore_helpers.py
  ├── data_processing.py
  └── distance_calculation/
      └── goong_api.py
```

## 🚀 Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/delivery-dispatch-system.git
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Deploy to Google Cloud Run using the provided Dockerfile.

## 🤝 Contributions

Contributions are welcome! Please fork the repository and submit pull requests for review.

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

