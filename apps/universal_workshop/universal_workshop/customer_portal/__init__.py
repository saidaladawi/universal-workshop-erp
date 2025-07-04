# Universal Workshop Customer Portal Module
# Arabic-first customer service portal with mobile optimization

__version__ = "1.0.0"

# Import main portal components
from .portal_framework import CustomerPortalFramework
from .portal_routes import setup_portal_routes

__all__ = ["CustomerPortalFramework", "setup_portal_routes"]
