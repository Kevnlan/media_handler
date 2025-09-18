#!/usr/bin/env python3
"""
Generate secure keys for WorkNomads Django applications.
Run this script to generate new SECRET_KEYs and JWT_SIGNING_KEY for production use.
"""

import secrets
import sys

def generate_django_secret_key():
    """Generate a Django SECRET_KEY"""
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))

def generate_jwt_signing_key():
    """Generate a JWT signing key (hex format)"""
    return secrets.token_hex(32)

def main():
    print("🔐 WorkNomads Security Key Generator")
    print("=" * 50)
    
    # Generate keys
    auth_secret = generate_django_secret_key()
    backend_secret = generate_django_secret_key()
    jwt_key = generate_jwt_signing_key()
    
    print("\n📋 Generated Keys (copy these to your .env file):")
    print("-" * 50)
    print(f"AUTH_SECRET_KEY={auth_secret}")
    print(f"BACKEND_SECRET_KEY={backend_secret}")
    print(f"JWT_SIGNING_KEY={jwt_key}")
    
    print("\n⚠️  IMPORTANT SECURITY NOTES:")
    print("-" * 50)
    print("1. 🚨 NEVER commit these keys to version control")
    print("2. 🔒 Use different keys for each environment (dev, staging, prod)")
    print("3. 🔄 Rotate keys regularly in production")
    print("4. 💾 Store production keys securely (e.g., in a secrets manager)")
    print("5. 🌐 The JWT_SIGNING_KEY must be the same across all services")
    
    print("\n📝 How to use:")
    print("-" * 50)
    print("1. Copy the generated keys above")
    print("2. Update your .env file with the new values")
    print("3. Restart your Django services")
    print("4. For production: use your hosting platform's secrets management")
    
    # Option to write to .env.production
    while True:
        try:
            response = input("\n💾 Create .env.production file with these keys? [y/N]: ").strip().lower()
            if response in ['y', 'yes']:
                create_production_env(auth_secret, backend_secret, jwt_key)
                break
            elif response in ['n', 'no', '']:
                print("\n✅ Keys generated successfully!")
                break
            else:
                print("Please enter 'y' or 'n'")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            sys.exit(0)

def create_production_env(auth_secret, backend_secret, jwt_key):
    """Create a .env.production file with secure keys"""
    production_env_content = f"""# WorkNomads Production Environment Configuration
# ⚠️  DO NOT COMMIT THIS FILE TO VERSION CONTROL
# Generated on: $(date)

# =================================================================
# DJANGO SETTINGS (PRODUCTION)
# =================================================================

# Django Secret Keys (SECURE - generated for production)
AUTH_SECRET_KEY={auth_secret}
BACKEND_SECRET_KEY={backend_secret}

# JWT Shared Signing Key (SECURE - generated for production)
JWT_SIGNING_KEY={jwt_key}

# Environment Settings (PRODUCTION)
DEBUG=False
DJANGO_ENV=production

# Allowed Hosts (UPDATE WITH YOUR DOMAINS)
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# =================================================================
# DATABASE CONFIGURATION (UPDATE FOR PRODUCTION)
# =================================================================

# PostgreSQL Database Settings
DB_ENGINE=django.db.backends.postgresql
DB_HOST=your-production-db-host
DB_PORT=5432
DB_USER=your-production-db-user
DB_PASSWORD=your-secure-production-db-password

# Database Names
AUTH_DB_NAME=worknomads_auth_prod
BACKEND_DB_NAME=worknomads_backend_prod

# =================================================================
# CORS & SECURITY SETTINGS (PRODUCTION)
# =================================================================

# CORS Origins (SECURE - only allow your frontend domains)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_ALL_ORIGINS=False

# =================================================================
# JWT TOKEN SETTINGS (PRODUCTION)
# =================================================================

# Token Lifetimes (consider shorter for production)
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
JWT_ROTATE_REFRESH_TOKENS=True
JWT_BLACKLIST_AFTER_ROTATION=True

# =================================================================
# PRODUCTION CHECKLIST
# =================================================================
# 1. ✅ Secure keys generated
# 2. 🔄 Update ALLOWED_HOSTS with your domains
# 3. 🔄 Update database credentials
# 4. 🔄 Update CORS_ALLOWED_ORIGINS
# 5. 🔄 Set up SSL certificates (HTTPS)
# 6. 🔄 Configure static/media file serving
# 7. 🔄 Set up monitoring and logging
# 8. 🔄 Test all endpoints
# 9. 🔒 Secure this file (proper permissions)
# 10. 🚨 NEVER commit this file to version control
"""
    
    try:
        with open('.env.production', 'w') as f:
            f.write(production_env_content)
        print("\n✅ Created .env.production file!")
        print("📝 Please update the database and domain settings in the file.")
        print("🚨 Remember: NEVER commit .env.production to version control!")
    except Exception as e:
        print(f"\n❌ Error creating .env.production: {e}")

if __name__ == "__main__":
    main()
