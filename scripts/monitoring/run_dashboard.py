#!/usr/bin/env python3
import http.server
import socketserver

PORT = 8002

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        
        # Serve dashboard for multiple paths
        if path in ['/', '/index.html', '/dashboard']:
            try:
                with open('/root/landslide-system/web_dashboard_simple.html', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Cache-Control', 'no-cache, no-store, max-age=0')
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Error loading dashboard")
                return
        
        elif path == '/api/results':
            try:
                with open('/root/landslide-system/results/demo_data.json', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(content)
                return
            except:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>404 Not Found</h1><p>Go to <a href='/dashboard'>/dashboard</a></p></body></html>")

    def log_message(self, format, *args):
        pass  # Suppress logging

if __name__ == '__main__':
    with socketserver.TCPServer(("0.0.0.0", PORT), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
