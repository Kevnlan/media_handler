#!/bin/bash
# setup_nginx.sh - Configure nginx for WorkNomads
# Usage: ./setup_nginx.sh [install|configure|start|stop|restart|status]

set -e

# Get the directory where this script is located (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGINX_CONF="$PROJECT_DIR/nginx.conf"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
SERVICE_NAME="worknomads"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root. Please run as your regular user."
        print_status "The script will use sudo when necessary."
        exit 1
    fi
}

install_nginx() {
    print_status "Installing nginx..."
    
    # Update package list
    sudo apt update
    
    # Install nginx
    if ! command -v nginx &> /dev/null; then
        sudo apt install nginx -y
        print_success "Nginx installed successfully"
    else
        print_warning "Nginx is already installed"
    fi
    
    # Enable and start nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx
    
    print_success "Nginx installation completed"
}

configure_nginx() {
    print_status "Configuring nginx for WorkNomads..."
    
    # Check if nginx is installed
    if ! command -v nginx &> /dev/null; then
        print_error "Nginx is not installed. Run: ./setup_nginx.sh install"
        exit 1
    fi
    
    # Backup default config if it exists
    if [[ -f "$NGINX_SITES_AVAILABLE/default" ]]; then
        sudo cp "$NGINX_SITES_AVAILABLE/default" "$NGINX_SITES_AVAILABLE/default.backup.$(date +%Y%m%d_%H%M%S)"
        print_status "Backed up default nginx config"
    fi
    
    # Copy our configuration and replace project directory placeholder
    sudo cp "$NGINX_CONF" "/tmp/nginx_worknomads_temp.conf"
    sudo sed "s|__PROJECT_DIR__|${PROJECT_DIR}|g" "/tmp/nginx_worknomads_temp.conf" > "/tmp/nginx_worknomads_final.conf"
    sudo cp "/tmp/nginx_worknomads_final.conf" "$NGINX_SITES_AVAILABLE/$SERVICE_NAME"
    sudo rm "/tmp/nginx_worknomads_temp.conf" "/tmp/nginx_worknomads_final.conf"
    print_status "Copied WorkNomads nginx config with dynamic paths"
    
    # Create symbolic link
    if [[ -L "$NGINX_SITES_ENABLED/$SERVICE_NAME" ]]; then
        sudo rm "$NGINX_SITES_ENABLED/$SERVICE_NAME"
    fi
    sudo ln -s "$NGINX_SITES_AVAILABLE/$SERVICE_NAME" "$NGINX_SITES_ENABLED/"
    print_status "Enabled WorkNomads site"
    
    # Optionally disable default site
    if [[ -L "$NGINX_SITES_ENABLED/default" ]]; then
        print_status "Disabling default nginx site..."
        sudo rm "$NGINX_SITES_ENABLED/default"
    fi
    
    # Test nginx configuration
    print_status "Testing nginx configuration..."
    if sudo nginx -t; then
        print_success "Nginx configuration is valid"
    else
        print_error "Nginx configuration test failed"
        exit 1
    fi
    
    print_success "Nginx configured successfully"
}

start_nginx() {
    print_status "Starting nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    print_success "Nginx started and enabled"
}

stop_nginx() {
    print_status "Stopping nginx..."
    sudo systemctl stop nginx
    print_success "Nginx stopped"
}

restart_nginx() {
    print_status "Restarting nginx..."
    sudo systemctl restart nginx
    print_success "Nginx restarted"
}

check_status() {
    print_status "Checking nginx status..."
    echo ""
    
    # Service status
    if systemctl is-active --quiet nginx; then
        print_success "Nginx service is running"
    else
        print_error "Nginx service is not running"
    fi
    
    # Port 80 check
    if ss -tlnp | grep :80 > /dev/null; then
        print_success "Port 80 is listening"
    else
        print_warning "Port 80 is not listening"
    fi
    
    # Configuration test
    if sudo nginx -t &> /dev/null; then
        print_success "Nginx configuration is valid"
    else
        print_error "Nginx configuration has errors"
        sudo nginx -t
    fi
    
    # Show service status
    echo ""
    print_status "Detailed service status:"
    systemctl status nginx --no-pager -l
    
    echo ""
    print_status "Testing HTTP connection..."
    if curl -s http://localhost/health > /dev/null; then
        print_success "HTTP health check passed"
    else
        print_warning "HTTP health check failed (services may not be running)"
    fi
}

setup_firewall() {
    print_status "Configuring firewall for nginx..."
    
    if command -v ufw &> /dev/null; then
        # Check if UFW is active
        if sudo ufw status | grep -q "Status: active"; then
            print_status "UFW is active, adding nginx rules..."
            sudo ufw allow 'Nginx Full'
            sudo ufw allow 80/tcp
            sudo ufw allow 443/tcp
            print_success "Firewall rules added for nginx"
        else
            print_warning "UFW is installed but not active"
        fi
    else
        print_warning "UFW not found. You may need to manually configure firewall."
    fi
}

show_help() {
    echo "WorkNomads Nginx Setup Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  install    - Install nginx"
    echo "  configure  - Configure nginx for WorkNomads"
    echo "  start      - Start nginx service"
    echo "  stop       - Stop nginx service" 
    echo "  restart    - Restart nginx service"
    echo "  status     - Check nginx status"
    echo "  firewall   - Configure firewall rules"
    echo "  full       - Install, configure, and start (recommended)"
    echo "  help       - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 full      # Complete setup"
    echo "  $0 configure # Just update configuration"
    echo "  $0 status    # Check if everything is working"
}

full_setup() {
    print_status "Starting full nginx setup for WorkNomads..."
    install_nginx
    configure_nginx
    setup_firewall
    restart_nginx
    sleep 2
    check_status
    
    echo ""
    print_success "🎉 Full nginx setup completed!"
    echo ""
    print_status "Next steps:"
    echo "1. Start your Django services: ./run_with_gateway.sh"
    echo "2. Access your API at: http://localhost"
    echo "3. Check health: http://localhost/health"
    echo "4. View API docs: http://localhost/api/docs/"
}

# Main script logic
case "${1:-help}" in
    install)
        check_root
        install_nginx
        ;;
    configure)
        check_root
        configure_nginx
        ;;
    start)
        check_root
        start_nginx
        ;;
    stop)
        check_root
        stop_nginx
        ;;
    restart)
        check_root
        restart_nginx
        ;;
    status)
        check_status
        ;;
    firewall)
        check_root
        setup_firewall
        ;;
    full)
        check_root
        full_setup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
