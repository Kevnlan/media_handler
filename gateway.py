# gateway.py
import aiohttp
from aiohttp import web
import logging
import json

# === Setup Logging ===
logging.basicConfig(
    filename="logs/gateway.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# === Service URLs ===
AUTH_SERVICE = "http://127.0.0.1:8000"
BACKEND_SERVICE = "http://127.0.0.1:8001"

routes = web.RouteTableDef()

# === Health Check ===
@routes.get("/health")
async def health(request):
    return web.json_response({"status": "ok", "gateway": True})

# === Proxy Utility ===
async def proxy_request(service_url, path, method, request):
    """
    Proxy HTTP request to target service with proper error handling
    """
    url = f"{service_url}{path}"
    logging.info(f"🔄 Proxying {method} {request.path} → {url}")
    logging.info(f"📋 Headers: {dict(request.headers)}")
    
    try:
        # Clean headers (remove hop-by-hop) but preserve original Host as X-Forwarded-Host
        headers = {k: v for k, v in request.headers.items() 
                   if k.lower() not in ["transfer-encoding", "host", "content-length"]}
        
        # Add X-Forwarded-Host so backend knows original host/IP
        if "host" in request.headers:
            headers["X-Forwarded-Host"] = request.headers["host"]

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, params=request.query, headers=headers) as resp:
                    data = await resp.read()
                    status = resp.status
                    resp_headers = dict(resp.headers)

            elif method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("Content-Type", "")

                if content_type.startswith("multipart/"):
                    # === File Uploads (raw multipart) ===
                    body = await request.read()
                    forward_headers = headers.copy()
                    forward_headers["Content-Type"] = request.headers.get("Content-Type")

                    logging.info(f"Forwarding multipart upload to {url}")

                    async with session.request(
                        method,
                        url,
                        data=body,  # ✅ send raw bytes unchanged
                        headers=forward_headers
                    ) as resp:
                        data = await resp.read()
                        status = resp.status
                        resp_headers = dict(resp.headers)

                        if status >= 400:
                            logging.error(f"Multipart error {status}: {data[:500]}")

                elif "application/json" in content_type:
                    # === JSON Requests ===
                    raw_body = await request.read()
                    try:
                        json_data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
                        logging.info(f"Forwarding JSON request to {url}: {json_data}")

                        async with session.request(
                            method,
                            url,
                            json=json_data,  # ✅ aiohttp serializes correctly
                            headers=headers
                        ) as resp:
                            data = await resp.read()
                            status = resp.status
                            resp_headers = dict(resp.headers)

                            if status >= 400:
                                logging.error(f"JSON error {status}: {data[:500]}")

                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logging.error(f"Invalid JSON: {e}")
                        return web.json_response({"error": "Invalid JSON"}, status=400)

                else:
                    # === Other / Raw Bodies (XML, text, protobuf, etc.) ===
                    body = await request.read()
                    logging.info(f"Forwarding raw body request to {url}")

                    async with session.request(
                        method,
                        url,
                        data=body,  # ✅ pass through unchanged
                        headers=headers
                    ) as resp:
                        data = await resp.read()
                        status = resp.status
                        resp_headers = dict(resp.headers)

            elif method == "DELETE":
                async with session.delete(url, headers=headers) as resp:
                    data = await resp.read()
                    status = resp.status
                    resp_headers = dict(resp.headers)

            else:
                return web.json_response({"error": "Unsupported method"}, status=405)

        if not data:
            return web.json_response({"message": "No data available"}, status=204)

        # Strip problematic headers before sending back
        resp_headers = {k: v for k, v in resp_headers.items()
                        if k.lower() not in ["content-encoding", "content-length", "transfer-encoding"]}

        # Add CORS headers for mobile app access
        resp_headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        })

        logging.info(f"✅ Response: {status} ({len(data)} bytes)")
        return web.Response(body=data, status=status, headers=resp_headers)

    except aiohttp.ClientConnectorError as e:
        logging.error(f"❌ Cannot connect to {url}: {e}")
        return web.json_response({"error": f"Service unavailable: {service_url}"}, status=503)
    except Exception as e:
        logging.error(f"❌ Error proxying {method} {url}: {e}", exc_info=True)
        return web.json_response({"error": str(e)}, status=500)

# === Auth Routes (Django auth URLs have trailing slashes) ===
@routes.route("*", "/api/auth/{path:.*}")
async def auth_proxy_with_path(request):
    """Route /api/auth/something to auth service"""
    path = request.match_info["path"]
    logging.info(f"🔐 Auth request with path: {request.method} /api/auth/{path}")
    return await proxy_request(AUTH_SERVICE, f"/api/auth/{path}", request.method, request)

@routes.route("*", "/api/auth/")  
async def auth_proxy_trailing_slash(request):
    """Route /api/auth/ to auth service"""
    logging.info(f"🔐 Auth request: {request.method} /api/auth/")
    return await proxy_request(AUTH_SERVICE, "/api/auth/", request.method, request)

@routes.route("*", "/api/auth")
async def auth_root_proxy(request):
    """Route /api/auth to auth service - redirect to trailing slash version"""
    logging.info(f"🔐 Auth root request: {request.method} /api/auth → /api/auth/")
    return await proxy_request(AUTH_SERVICE, "/api/auth/", request.method, request)

# === OPTIONS Handler for CORS ===
@routes.options("/{path:.*}")
async def handle_options(request):
    """Handle CORS preflight requests"""
    logging.info(f"🔄 CORS preflight: {request.path}")
    return web.Response(
        status=200,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '86400',
        }
    )

# === Media/Backend Routes ===
@routes.route("*", "/api/media/{path:.*}")
async def media_proxy_with_path(request):
    """Route /api/media/something to backend service"""
    path = request.match_info["path"]
    logging.info(f"📁 Media request with path: {request.method} /api/media/{path}")
    return await proxy_request(BACKEND_SERVICE, f"/api/media/{path}", request.method, request)

@routes.route("*", "/api/media")
async def media_root_proxy(request):
    """Route /api/media to backend service (no trailing slash)"""
    logging.info(f"📁 Media root request: {request.method} /api/media")
    return await proxy_request(BACKEND_SERVICE, "/api/media", request.method, request)

@routes.route("GET", "/media/{type}/{filename}")
async def media_file_proxy(request):
    """Proxy media file requests to backend media server, preserving Authorization header."""
    media_type = request.match_info["type"]
    filename = request.match_info["filename"]
    backend_url = f"/media/{media_type}/{filename}"
    logging.info(f"🖼️ Proxying media file: {request.method} {backend_url}")
    return await proxy_request(BACKEND_SERVICE, backend_url, request.method, request)

# === Welcome Route ===
@routes.get("/")
async def welcome(request):
    """Gateway welcome page"""
    return web.Response(
        text="""
🚀 WorkNomads API Gateway

Available endpoints:
- /api/auth/* → Authentication Service (port 8000) [WITH trailing slashes]
- /api/media → Media list/create (port 8001) [NO trailing slashes]  
- /api/media/<id> → Media detail operations (port 8001) [NO trailing slashes]
- /api/media/collection → Collection list/create (port 8001) [NO trailing slashes]
- /health → Gateway health check

📖 API Documentation:
- Auth API: http://localhost:8000/api/schema/swagger-ui/
- Media API: http://localhost:8001/api/schema/swagger-ui/

🧪 Usage Examples:
curl -X POST http://192.168.100.9:3000/api/auth/login/ \\
  -H "Content-Type: application/json" \\
  -d '{"email":"test@example.com","password":"password"}'

curl -X POST http://192.168.100.9:3000/api/media \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -F "file=@image.jpg" \\
  -F "title=My Upload"

curl -X GET http://192.168.100.9:3000/api/media \\
  -H "Authorization: Bearer YOUR_TOKEN"
        """,
        content_type='text/plain',
        headers={
            'Access-Control-Allow-Origin': '*',
        }
    )

# === Start Server ===
app = web.Application(client_max_size=1024**2*100)  # 100MB max upload
app.add_routes(routes)

if __name__ == "__main__":
    import os
    os.makedirs("logs", exist_ok=True)
    
    print("🚀 WorkNomads Gateway starting...")
    print("🌐 Access at: http://localhost:3000")
    print("📱 Mobile access: http://192.168.100.9:3000")
    print("💚 Health check: http://localhost:3000/health")
    print("📝 Logs: logs/gateway.log")
    print("")
    print("📋 Your endpoints:")
    print("  🔐 Auth (WITH trailing slashes):")
    print("    POST /api/auth/login/")
    print("    POST /api/auth/register/") 
    print("    POST /api/auth/refresh/")
    print("    GET  /api/auth/profile/")
    print("  📁 Media (NO trailing slashes):")
    print("    POST /api/media (file upload)")
    print("    GET  /api/media (list)")
    print("    GET  /api/media/<id> (detail)")
    print("    GET  /api/media/collection (collections)")
    print("")
    
    web.run_app(app, host="0.0.0.0", port=3000)

