#!/bin/bash
# Run Django Auth + Backend servers and API Gateway
# Usage: ./run_with_gateway.sh

echo "🚀 Starting WorkNomads servers with API Gateway..."

# === Setup Virtual Environment ===
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# Ensure logs directory exists
mkdir -p logs

# === Function to start Django server ===
start_django_server() {
    local name=$1
    local port=$2
    local dir=$3
    local logfile="logs/${name// /_}.log"

    if [ ! -d "$dir" ]; then
        echo "❌ Directory $dir not found. Skipping $name."
        return
    fi

    echo "▶️ Starting $name on port $port..."
    (cd "$dir" && python manage.py runserver "0.0.0.0:$port") > "$logfile" 2>&1 &
    local pid=$!
    echo "✅ $name started (PID: $pid) → logging to $logfile"
    echo $pid
}

# === Firewall Rules (Optional) ===
if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status | grep -q "Status: active"; then
        echo "🔒 UFW active. Ensuring required ports are open..."
        for port in 8000 8001 3000; do
            sudo ufw allow $port/tcp >/dev/null
        done
    fi
fi

# === Start Services ===
AUTH_PID=$(start_django_server "Auth Server" 8000 "auth_server")
BACKEND_PID=$(start_django_server "Backend Server" 8001 "backend_server")

sleep 3  # give Django servers time to boot

echo "▶️ Starting API Gateway on port 3000..."
python gateway.py > "logs/api_gateway.log" 2>&1 &
GATEWAY_PID=$!
echo "✅ API Gateway started (PID: $GATEWAY_PID) → logging to logs/api_gateway.log"

# === Print Service Info ===
LOCAL_IP=$(hostname -I | awk '{print $1}')
cat <<EOF

🎉 All services started!

📡 API Gateway: http://$LOCAL_IP:3000
🔐 Auth Service: http://$LOCAL_IP:8000
📁 Backend Service: http://$LOCAL_IP:8001

📖 API Documentation:
  - Auth:   http://$LOCAL_IP:8000/api/docs
  - Media:  http://$LOCAL_IP:8001/api/docs

💚 Health Check:
  - Local:   http://localhost:3000/health
  - Mobile:  http://$LOCAL_IP:3000/health

🔥 Test on your phone using:
   http://$LOCAL_IP:3000
EOF

# === Cleanup on Exit ===
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $AUTH_PID $BACKEND_PID $GATEWAY_PID 2>/dev/null
    deactivate
    echo "👋 All services stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM

# === Keep Script Running ===
echo "Press Ctrl+C to stop all services"
wait

