# 🎱 NANTE Club - POS & Management System

A modern, desktop-based Point of Sale (POS) and Club Management application built with Python. Designed specifically for Billiard and Gaming (PlayStation) clubs to manage spaces, track time, handle bar inventory, and process payments seamlessly.

![UI Theme](https://img.shields.io/badge/UI-CustomTkinter-blue)
![Database](https://img.shields.io/badge/Database-SQLite-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## ✨ Core Features

* **⏳ Space & Time Management:** 
  * Live timers with precise minute-based cost calculation.
  * Reservation system with active countdowns for upcoming bookings.
* **🛒 Inventory & Bar Management:** 
  * Virtual shopping cart for each active table/room.
  * Automatic stock deduction upon successful checkout.
  * Easy inventory restock and new product creation.
* **💳 Payments & Smart POS Integration:**
  * Support for Split Payments (Cash + Card).
  * Direct TCP Socket integration with local Bank Terminals (ECR Protocol with STX/ETX/LRC validation).
  * Background threading for terminal communication to keep the UI responsive.
* **🖨️ Receipt & Z-Report Printing:** 
  * Cross-platform mock printing (Terminal output) for macOS/Linux.
  * Native hardware support for Thermal Printers on Windows via `win32print`.
* **🔐 Role-Based Access Control:** 
  * `Admin`: Full access to settings, inventory, and financial statistics.
  * `Cashier`: Operational access (Start/Stop, Cart, Checkout, Z-Report).
* **📊 Analytics Dashboard:** 
  * Detailed financial breakdown (Time vs. Bar revenue, Cash vs. TBC/BOG Terminals).
  * Top-performing spaces and best-selling products.

## 🏗️ Project Architecture

The project follows a modular architecture for scalability and maintainability:

```text
nante-club/
├── core/
│   ├── database.py       # SQLite initialization & schemas
│   ├── pos_terminal.py   # Low-level ECR protocol for TCP Socket communication
│   └── printer.py        # Cross-platform receipt printing logic
├── ui/
│   └── gui.py            # CustomTkinter interface, views, and components
├── main.py               # Application entry point
└── requirements.txt      # Dependencies
```

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Luka-Dumbadze/nante-club.git
   cd nante-club
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: For Windows printing support, `pywin32` is required. It is excluded from the default requirements for cross-platform compatibility).*

4. **Run the application:**
   ```bash
   python main.py
   ```

## 📦 Packaging for Production

To compile the application into a standalone executable (e.g., `.exe` for Windows) so it can be deployed on a club's local machine without requiring Python:

```bash
pip install pyinstaller
pyinstaller --name "NANTE_Club" --windowed main.py
```
The compiled executable will be located in the `dist/NANTE_Club/` directory.

## 🔒 Default Credentials
On the first run, the SQLite database is automatically generated with default users:
* **Admin:** `admin` / `admin123`
* **Cashier:** `cashier1` / `cashier123`

---
*Developed with clean code practices and tailored for modern entertainment club management.*
