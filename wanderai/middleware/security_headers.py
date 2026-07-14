"""
wanderai/middleware/security_headers.py
Adds production-grade security headers to every response.
"""


def init_security_headers(app):
    """Register security header injection after every request."""

    @app.after_request
    def _add_security_headers(response):
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # HSTS — HTTPS only for 1 year (production)
        if not app.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=()"
        )
        return response
