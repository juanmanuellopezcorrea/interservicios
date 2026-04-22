"""
Endpoint para Vercel Cron Jobs.
Reemplaza al APScheduler que no funciona en entornos serverless.

Configurar en vercel.json:
{
  "crons": [{
    "path": "/api/cron/informe_mensual",
    "schedule": "0 8 1 * *"
  }]
}
"""
import os
import sys
from http.server import BaseHTTPRequestHandler

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Verificar que la petición viene de Vercel Cron
        auth_header = self.headers.get('Authorization')
        cron_secret = os.environ.get('CRON_SECRET')
        
        if cron_secret and auth_header != f'Bearer {cron_secret}':
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized"}')
            return
        
        try:
            from app import app, _enviar_informe_pendientes_admin
            
            with app.app_context():
                _enviar_informe_pendientes_admin()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"success": true, "message": "Informe enviado"}')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"error": "{str(e)}"}}'.encode())
