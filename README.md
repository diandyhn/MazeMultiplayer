# **Maze Multiplayer**

Kami membuat game dengan judul “Multiplayer Maze”. Game ini merupakan game multiplayer di mana setiap player beradu cepat untuk menavigasi beberapa level maze yang sudah tergenerate. Tidak hanya itu, di dalam maze terdapat collectibles yang dapat diambil oleh pemain untuk mendapatkan poin tambahan.

![image](https://github.com/user-attachments/assets/72ba17ad-3eb8-45d8-9123-3273286b6050)

## 📦 Requirements

### System Requirements
- Python 3.7+
- Desktop environment (untuk GUI client)
- Network connectivity

### Python Dependencies
```bash
pip install pygame pillow
```

**Required Packages:**
- `pygame`: Game client GUI dan graphics
- `pillow`: Avatar generation dan image processing
- `socket`: Network communication (built-in)
- `threading`: Concurrent request handling (built-in)
- `json`: API data serialization (built-in)

## 🚀 Instalasi

### 1. Clone atau Download
```bash
# Jika menggunakan git
git clone <repository-url>
cd maze-multiplayer-game

# Atau download semua file ke satu folder
```

### 2. Install Dependencies
```bash
pip install pygame pillow
```

### 3. Verify Installation
```bash
python -c "import pygame, PIL; print('Dependencies OK')"
```

## 🎮 Cara Menjalankan

### Step 1: Jalankan Server
```bash
# Default port (55556)
python maze_server.py

# Custom port
python maze_server.py 8080
```

**Output yang diharapkan:**
```
============================================================
    🎮 MAZE GAME SERVER
============================================================
Maze HTTP Server running on port 55556
Game endpoints available:
   GET  http://localhost:55556/api/status
   GET  http://localhost:55556/api/gamestate
   POST http://localhost:55556/api/player/add
   POST http://localhost:55556/api/player/move
```

### Step 2: Jalankan Client
```bash
python maze_client.py
```

### Step 3: Game Setup
1. **Enter Player Name**: Masukkan nama pemain (max 20 karakter)
2. **Enter Server Address**: Format `hostname:port` (default: localhost:55556)
3. **Start Playing**: Gunakan arrow keys atau WASD untuk bergerak

### Step 4: Mengundang Pemain Lain
- Berikan server address kepada pemain lain
- Setiap pemain menjalankan `python maze_client.py`
- Pemain akan otomatis muncul di maze yang sama
