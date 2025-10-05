import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

# Change to the directory containing the web files
os.chdir(Path(__file__).parent)

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

print("Starting EMIT Data Visualization Server...")
print(f"Server will run on http://localhost:{PORT}")
print("Press Ctrl+C to stop the server")

try:
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Server started successfully!")
        print(f"Open your browser and navigate to: http://localhost:{PORT}")
        
        # Try to open the browser automatically
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            print("Could not open browser automatically. Please open manually.")
        
        httpd.serve_forever()
        
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"Error starting server: {e}")
    print("Make sure port 8000 is not already in use")