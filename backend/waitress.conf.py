# Waitress Production Configuration
# This file configures Waitress for production use

# Server binding
host = "0.0.0.0"  # Listen on all interfaces
port = 5000        # Port to listen on

# Performance settings
threads = 4        # Number of worker threads
connection_limit = 1000  # Maximum concurrent connections
cleanup_interval = 30    # Cleanup interval in seconds
channel_timeout = 120    # Channel timeout in seconds

# Logging
log_level = "INFO"
log_file = "waitress.log"  # Log file path (optional)

# Security
max_request_body_size = 1073741824  # 1GB max request size
url_scheme = "http"  # Change to "https" if using SSL

# Production optimizations
buffer_size = 16384  # Buffer size for I/O operations
