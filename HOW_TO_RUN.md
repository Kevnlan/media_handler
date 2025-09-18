# WorkNomads - How to Run Guide

This guide explains how to run the WorkNomads microservices architecture locally on **Linux** and **macOS**.

## 🏗️ Architecture Overview

- **Auth Server**: Django REST API (Port 8000) - User authentication and JWT management
- **Backend Server**: Django REST API (Port 8001) - Media handling and core business logic  
- **API Gateway**: Python aiohttp (Port 3000) - Routes requests between services
- **Nginx**: Reverse proxy (Port 80) - Production-ready load balancing and static file serving

## 🔧 Prerequisites

### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python 3.11+
sudo apt install python3 python3-pip python3-venv

# Install nginx
sudo apt install nginx

# Install PostgreSQL (recommended for production)
sudo apt install postgresql postgresql-contrib

# Install Docker (optional - for containerized setup)
sudo apt install docker.io docker-compose
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### 🔐 Environment Setup (IMPORTANT!)

Before running the application, you need to configure environment variables:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your settings
nano .env  # or use your preferred editor

# Generate new secure keys for production (recommended)
python3 generate_keys.py
```

**Key Settings to Configure:**
- `AUTH_SECRET_KEY` and `BACKEND_SECRET_KEY` - Django secret keys (generate new ones!)
- `JWT_SIGNING_KEY` - Must be the same for both services  
- `DEBUG` - Set to `False` in production
- `ALLOWED_HOSTS` - Add your domain/IP addresses
- Database credentials if using PostgreSQL

### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+
brew install python@3.11

# Install nginx
brew install nginx

# Install Docker Desktop (optional)
# Download from: https://www.docker.com/products/docker-desktop
```

## 🚀 Running Methods

### Method 1: Quick Start with Gateway (Recommended for Development)

This method uses the included `run_with_gateway.sh` script to start all services with the Python-based API Gateway.

#### Linux
```bash
# Make script executable
chmod +x run_with_gateway.sh

# Run all services
./run_with_gateway.sh
```

#### macOS
```bash
# Make script executable
chmod +x run_with_gateway.sh

# Run all services (same as Linux)
./run_with_gateway.sh
```

**What this does:**
- Creates a Python virtual environment (`venv/`)
- Installs dependencies for both Django apps
- Starts Auth Server on port 8000
- Starts Backend Server on port 8001  
- Starts API Gateway on port 3000
- Opens firewall ports (Linux with UFW)
- Provides unified access point at `http://localhost:3000`

**Access URLs:**
- API Gateway: `http://localhost:3000`
- Auth Service: `http://localhost:8000`
- Backend Service: `http://localhost:8001`
- Mobile/Network Access: `http://[YOUR_IP]:3000`

### Method 2: Manual Service Startup

If you prefer to start services individually:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR for Windows: venv\Scripts\activate

# Install dependencies for both servers
cd auth_server && pip install -r requirements.txt && cd ..
cd backend_server && pip install -r requirements.txt && cd ..

# Start services in separate terminals
# Terminal 1: Auth Server
cd auth_server && python manage.py runserver 0.0.0.0:8000

# Terminal 2: Backend Server  
cd backend_server && python manage.py runserver 0.0.0.0:8001

# Terminal 3: API Gateway
python gateway.py
```

### Method 3: Docker Compose (Production-like)

For a containerized setup with nginx:

```bash
# Create environment file
echo "JWT_SIGNING_KEY=your-secret-key-here" > .env

# Build and run containers
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

**Docker Access URLs:**
- Nginx Proxy: `http://localhost`
- Auth API: `http://localhost/api/auth/`
- Media API: `http://localhost/api/media` (no trailing slash)
- Static Files: `http://localhost/media/`

## 🌐 Setting Up Nginx (Production Setup)

### Linux Setup

1. **Install and start nginx:**
```bash
sudo apt install nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

2. **Configure nginx:**
```bash
# Backup default config
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Copy our config
sudo cp nginx.conf /etc/nginx/sites-available/worknomads
sudo ln -s /etc/nginx/sites-available/worknomads /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### macOS Setup

1. **Install and start nginx:**
```bash
brew install nginx
brew services start nginx
```

2. **Configure nginx:**
```bash
# Backup default config
cp /usr/local/etc/nginx/nginx.conf /usr/local/etc/nginx/nginx.conf.backup

# Copy our config to nginx directory
cp nginx.conf /usr/local/etc/nginx/servers/worknomads.conf

# Test configuration
nginx -t

# Restart nginx
brew services restart nginx
```

### Nginx Configuration Notes

The included `nginx.conf` provides:
- **Reverse proxy** to Django services (Auth with trailing slashes, Media without)
- **CORS headers** for web client support  
- **Media file serving** with caching and direct access
- **Upload size limits** (100MB for media files)
- **Health checks** and error handling
- **Dynamic paths** - automatically uses your project location

**Important Endpoint Differences:**
- **Auth endpoints**: `/api/auth/` (WITH trailing slash)
- **Media endpoints**: `/api/media` (NO trailing slash) 
- **Static files**: `/media/` (direct nginx serving)

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use:**
```bash
# Find process using port
sudo lsof -i :8000
# Kill process
sudo kill -9 [PID]
```

2. **Python virtual environment issues:**
```bash
# Remove and recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

3. **Nginx permission issues (Linux):**
```bash
# Check nginx user
ps aux | grep nginx
# Ensure media directory is readable
chmod -R 755 backend_server/media/
```

4. **macOS firewall blocking connections:**
```bash
# Allow nginx through firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/nginx
```

### Logs and Debugging

- **Application logs:** Check `logs/` directory
- **Nginx logs (Linux):** `/var/log/nginx/`
- **Nginx logs (macOS):** `/usr/local/var/log/nginx/`
- **Django debug:** Set `DEBUG=True` in settings.py

### Network Access for Mobile Testing

1. **Find your IP address:**
```bash
# Linux
hostname -I | awk '{print $1}'

# macOS  
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'
```

2. **Access from mobile device:**
- Use `http://[YOUR_IP]:3000` (with gateway)
- Use `http://[YOUR_IP]` (with nginx)

## 🌐 Smart IP Forwarding & Media URLs

WorkNomads includes intelligent IP forwarding to ensure media URLs work correctly across different network environments (localhost, WiFi, mobile hotspot, etc.).

### How It Works

1. **Client Request**: Mobile app or web client makes request to gateway/nginx
2. **Header Forwarding**: Gateway adds `X-Forwarded-Host` header with original client IP
3. **Dynamic URL Generation**: Backend detects the original IP and generates correct media URLs
4. **Mobile Compatibility**: Media files are accessible from the same IP the client used

### Example Flow

```bash
# Mobile app requests from WiFi network
GET http://192.168.1.100:3000/api/media
X-Forwarded-Host: 192.168.1.100:3000

# Backend response includes correct URLs
{
  "id": 1,
  "title": "My Photo",
  "file_url": "http://192.168.1.100:3000/media/image/photo.jpg"  # ✅ Mobile accessible
}
```

### Supported Scenarios
- **Development**: `localhost:3000` → `localhost:3000/media/...`
- **WiFi Network**: `192.168.1.x:3000` → `192.168.1.x:3000/media/...`  
- **Mobile Hotspot**: `192.168.x.x:3000` → `192.168.x.x:3000/media/...`
- **Nginx Proxy**: `your-ip` → `your-ip/media/...`

This means your mobile app will always receive the correct URLs regardless of network changes!

## 🔒 Security & Environment Configuration

### Environment Variables

WorkNomads uses environment variables to manage all sensitive settings securely:

#### Required Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `AUTH_SECRET_KEY` | Django secret for auth server | `django-insecure-...` |
| `BACKEND_SECRET_KEY` | Django secret for backend server | `django-insecure-...` |
| `JWT_SIGNING_KEY` | Shared JWT key (must be same for both) | `9e7cdbb3a8f14d55...` |
| `DEBUG` | Debug mode | `True` / `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1,yourdomain.com` |
| `DB_PASSWORD` | Database password | `your-secure-password` |

#### Generate Secure Keys

```bash
# Use the included key generator
python3 generate_keys.py

# Manual generation (alternative)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Environment Files

- **`.env`** - Local development settings (not committed)
- **`.env.example`** - Template with safe defaults (committed)
- **`.env.production`** - Production settings (generated by `generate_keys.py`)

### Security Best Practices

- 🚨 **NEVER** commit `.env` files to version control
- 🔄 Use different keys for development, staging, and production
- 🔒 Rotate JWT signing keys regularly in production
- 🌐 Set `DEBUG=False` in production
- 🔐 Use HTTPS in production with SSL certificates
- 🛡️ Configure proper firewall rules
- 📊 Set up monitoring and logging for production
- 🗄️ Use managed database services in production

## 📱 API Endpoints

### Auth Service (`/api/auth/`)
- `POST /api/auth/register/` - User registration  
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Token refresh
- `GET /api/auth/profile/` - User profile

### Media Service (`/api/media`)  
**Note**: Media endpoints do NOT have trailing slashes
- `POST /api/media` - File upload
- `GET /api/media` - List user files  
- `GET /api/media/{id}` - Get specific file details
- `DELETE /api/media/{id}` - Delete file
- `GET /api/media/collection` - List collections

### Direct Media Access
- `GET /media/{type}/{filename}` - Direct file access (served by nginx or gateway)

### Health Check
- `GET /health` - Service status check

---

## 🎯 Quick Commands Reference

```bash
# Start development environment
./run_with_gateway.sh

# Start with Docker
docker-compose up -d

# Check service status  
curl http://localhost:3000/health   # Gateway health
curl http://localhost/health        # Nginx health (if configured)

# Test endpoints (after starting services)
curl -X POST http://localhost:3000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

curl -X GET http://localhost:3000/api/media \
  -H "Authorization: Bearer YOUR_TOKEN"

# View logs
tail -f logs/api_gateway.log
tail -f logs/Auth_Server.log
tail -f logs/Backend_Server.log

# Stop all services
# Ctrl+C (if using run_with_gateway.sh)
# docker-compose down (if using Docker)
```

Need help? Check the logs in the `logs/` directory for detailed error information.
