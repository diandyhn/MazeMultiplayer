# launcher.py
import subprocess
import sys
import os
import time

def check_requirements():
    """Check if required packages are installed"""
    try:
        import pygame
        import PIL
        print("✓ All required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing required package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def start_server():
    """Start the maze server"""
    print("🚀 Starting Maze Game Server...")
    if os.path.exists("maze_server.py"):
        try:
            process = subprocess.Popen([sys.executable, "maze_server.py"])
            time.sleep(2)  # Give server time to start
            
            # Check if process is still running
            if process.poll() is None:
                print("✅ Server started successfully on port 55556")
                return True
            else:
                print("❌ Server failed to start (process exited)")
                return False
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    else:
        print("❌ maze_server.py not found!")
        return False

def test_connection():
    """Test if server is responding"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex(('127.0.0.1', 55556))
        sock.close()
        return result == 0
    except:
        return False

def start_client():
    """Start the maze client"""
    print("Starting Maze Game Client...")
    if os.path.exists("maze_client.py"):
        subprocess.run([sys.executable, "maze_client.py"])
        return True
    else:
        print("✗ maze_client.py not found!")
        return False

def main():
    print("=" * 60)
    print("       ESCAPE THE MAZE - Game Launcher")
    print("=" * 60)
    
    if not check_requirements():
        return
    
    print("\nSelect an option:")
    print("1. Start Server Only")
    print("2. Start Client Only") 
    print("3. Start Server + Client (for local play)")
    print("4. Test Connection")
    print("5. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            if start_server():
                print("\n🎮 Server is running. Start clients from other terminals or machines.")
                print("🔗 Connection details:")
                print("   - Port: 55556")
                print("   - Local: 127.0.0.1:55556")
                input("\nPress Enter to exit...")
            break
            
        elif choice == "2":
            print("🔍 Testing server connection first...")
            if test_connection():
                print("✅ Server detected!")
                start_client()
            else:
                print("❌ Cannot connect to server!")
                print("Make sure the server is running (option 1 or 3)")
            break
            
        elif choice == "3":
            if start_server():
                print("⏳ Waiting for server to initialize...")
                time.sleep(3)
                
                if test_connection():
                    print("✅ Server ready! Starting client...")
                    start_client()
                else:
                    print("❌ Server failed to start properly")
            break
            
        elif choice == "4":
            print("🔍 Testing connection to server...")
            if test_connection():
                print("✅ Server is running and responding!")
            else:
                print("❌ No server detected on port 55556")
                print("Start the server first (option 1 or 3)")
            
        elif choice == "5":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()