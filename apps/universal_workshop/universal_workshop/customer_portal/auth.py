# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Authentication System
Provides JWT-based authentication with 2FA support for Oman market
"""

import json
import jwt
import redis
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, Optional

import frappe
from frappe import _
from frappe.utils import (
    cint, validate_email_address, random_string
)

# Redis client for session management
def get_redis_client():
    """Get Redis client for session management"""
    return redis.Redis(
        host=frappe.conf.get('redis_cache') or 'localhost',
        port=6379,
        db=3,  # Use separate DB for portal sessions
        decode_responses=True
    )

class CustomerPortalAuth:
    """Customer portal authentication manager"""
    
    def __init__(self):
        self.jwt_secret = frappe.conf.get('jwt_secret_key') or frappe.conf.encryption_key
        self.jwt_algorithm = 'HS256'
        self.session_duration = cint(frappe.conf.get('portal_session_duration', 86400))  # 24 hours
        self.max_login_attempts = cint(frappe.conf.get('max_login_attempts', 5))
        self.lockout_duration = cint(frappe.conf.get('lockout_duration', 1800))  # 30 minutes
        self.redis_client = get_redis_client()
    
    def authenticate_customer(self, login_id: str, password: str, ip_address: str = None) -> Dict:
        """
        Authenticate customer with email/phone and password
        
        Args:
            login_id: Customer email or phone number
            password: Customer password
            ip_address: Client IP address for security logging
            
        Returns:
            dict: Authentication result with token or error
        """
        try:
            # Check if account is locked
            if self._is_account_locked(login_id):
                return {
                    'success': False,
                    'message': _('Account temporarily locked due to too many failed attempts'),
                    'locked_until': self._get_lockout_expiry(login_id)
                }
            
            # Find customer by email or phone
            customer = self._find_customer_by_login(login_id)
            if not customer:
                self._record_failed_attempt(login_id, ip_address)
                return {
                    'success': False,
                    'message': _('Invalid login credentials')
                }
            
            # Verify password (for now, assume simple password check)
            if not self._verify_customer_password(customer.name, password):
                self._record_failed_attempt(login_id, ip_address)
                return {
                    'success': False,
                    'message': _('Invalid login credentials')
                }
            
            # Clear failed attempts on successful login
            self._clear_failed_attempts(login_id)
            
            # Check if 2FA is enabled
            if customer.get('enable_two_factor_auth'):
                # Generate and send OTP
                otp_token = self._generate_otp_session(customer.name)
                self._send_login_otp(customer, otp_token)
                
                return {
                    'success': True,
                    'requires_2fa': True,
                    'otp_token': otp_token,
                    'message': _('OTP sent to your registered mobile number')
                }
            
            # Generate JWT token for authenticated session
            jwt_token = self._generate_jwt_token(customer)
            
            # Log successful login
            self._log_security_event(customer.name, 'login_success', ip_address)
            
            return {
                'success': True,
                'token': jwt_token,
                'customer': self._get_customer_profile(customer.name),
                'expires_at': (datetime.utcnow() + timedelta(seconds=self.session_duration)).isoformat()
            }
            
        except Exception as e:
            frappe.log_error(f"Customer authentication error: {str(e)}", "Customer Portal Auth")
            return {
                'success': False,
                'message': _('Authentication service temporarily unavailable')
            }
    
    def verify_2fa_otp(self, otp_token: str, otp_code: str, ip_address: str = None) -> Dict:
        """
        Verify 2FA OTP and complete authentication
        
        Args:
            otp_token: OTP session token
            otp_code: User-provided OTP code
            ip_address: Client IP address
            
        Returns:
            dict: Authentication result with JWT token
        """
        try:
            # Validate OTP session
            customer_id = self._validate_otp_session(otp_token, otp_code)
            if not customer_id:
                return {
                    'success': False,
                    'message': _('Invalid or expired OTP')
                }
            
            # Get customer details
            customer = frappe.get_doc('Customer', customer_id)
            
            # Generate JWT token
            jwt_token = self._generate_jwt_token(customer)
            
            # Clean up OTP session
            self._cleanup_otp_session(otp_token)
            
            # Log successful 2FA login
            self._log_security_event(customer_id, '2fa_login_success', ip_address)
            
            return {
                'success': True,
                'token': jwt_token,
                'customer': self._get_customer_profile(customer_id),
                'expires_at': (datetime.utcnow() + timedelta(seconds=self.session_duration)).isoformat()
            }
            
        except Exception as e:
            frappe.log_error(f"2FA verification error: {str(e)}", "Customer Portal Auth")
            return {
                'success': False,
                'message': _('2FA verification failed')
            }
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token and return customer session data
        
        Args:
            token: JWT token to verify
            
        Returns:
            dict: Customer session data or None if invalid
        """
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check if token is blacklisted
            if self._is_token_blacklisted(token):
                return None
            
            # Verify customer still exists and is active
            customer_id = payload.get('customer_id')
            customer = frappe.db.get_value(
                'Customer', 
                customer_id, 
                ['name', 'disabled', 'customer_name', 'customer_name_ar'],
                as_dict=True
            )
            
            if not customer or customer.disabled:
                return None
            
            return {
                'customer_id': customer_id,
                'customer_name': customer.customer_name,
                'customer_name_ar': customer.customer_name_ar,
                'session_id': payload.get('session_id'),
                'expires_at': payload.get('exp')
            }
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            frappe.log_error(f"JWT verification error: {str(e)}", "Customer Portal Auth")
            return None
    
    def logout_customer(self, token: str, ip_address: str = None) -> Dict:
        """
        Logout customer and blacklist token
        
        Args:
            token: JWT token to blacklist
            ip_address: Client IP address
            
        Returns:
            dict: Logout result
        """
        try:
            # Verify token first
            session_data = self.verify_jwt_token(token)
            if not session_data:
                return {
                    'success': False,
                    'message': _('Invalid session')
                }
            
            # Add token to blacklist
            self._blacklist_token(token, session_data['expires_at'])
            
            # Log logout event
            self._log_security_event(session_data['customer_id'], 'logout', ip_address)
            
            return {
                'success': True,
                'message': _('Logged out successfully')
            }
            
        except Exception as e:
            frappe.log_error(f"Customer logout error: {str(e)}", "Customer Portal Auth")
            return {
                'success': False,
                'message': _('Logout failed')
            }
    
    def request_password_reset(self, login_id: str) -> Dict:
        """
        Request password reset for customer
        
        Args:
            login_id: Customer email or phone
            
        Returns:
            dict: Password reset request result
        """
        try:
            # Find customer
            customer = self._find_customer_by_login(login_id)
            if not customer:
                # Don't reveal if customer exists or not
                return {
                    'success': True,
                    'message': _('If the account exists, you will receive password reset instructions')
                }
            
            # Generate reset token
            reset_token = self._generate_password_reset_token(customer.name)
            
            # Send reset link via SMS or email
            self._send_password_reset_link(customer, reset_token)
            
            return {
                'success': True,
                'message': _('Password reset instructions sent to your registered contact information')
            }
            
        except Exception as e:
            frappe.log_error(f"Password reset request error: {str(e)}", "Customer Portal Auth")
            return {
                'success': False,
                'message': _('Password reset service temporarily unavailable')
            }
    
    # Private helper methods
    
    def _find_customer_by_login(self, login_id: str) -> Optional[frappe.Document]:
        """Find customer by email or phone number"""
        try:
            # First try email
            if validate_email_address(login_id):
                customer_id = frappe.db.get_value('Customer', {'email_id': login_id}, 'name')
            else:
                # Try phone number (with or without +968 prefix)
                phone_variants = [login_id]
                if not login_id.startswith('+968'):
                    phone_variants.append(f'+968{login_id.lstrip("0")}')
                if login_id.startswith('+968'):
                    phone_variants.append(login_id[4:])
                
                customer_id = frappe.db.get_value(
                    'Customer', 
                    {'mobile_no': ['in', phone_variants]}, 
                    'name'
                )
            
            if customer_id:
                return frappe.get_doc('Customer', customer_id)
            return None
            
        except Exception:
            return None
    
    def _verify_customer_password(self, customer_id: str, password: str) -> bool:
        """Verify customer password against stored hash"""
        try:
            # For now, use simple password check (will be enhanced)
            stored_password = frappe.db.get_value('Customer', customer_id, 'portal_password')
            return stored_password == password
            
        except Exception:
            return False
    
    def _generate_jwt_token(self, customer: frappe.Document) -> str:
        """Generate JWT token for authenticated customer"""
        session_id = random_string(32)
        payload = {
            'customer_id': customer.name,
            'customer_name': customer.customer_name,
            'session_id': session_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=self.session_duration)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def _generate_otp_session(self, customer_id: str) -> str:
        """Generate OTP session for 2FA authentication"""
        otp_token = random_string(32)
        otp_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        
        # Store OTP session in Redis (5 minutes expiry)
        otp_data = {
            'customer_id': customer_id,
            'otp_code': otp_code,
            'created_at': datetime.utcnow().isoformat(),
            'attempts': 0
        }
        
        self.redis_client.setex(
            f'otp_session:{otp_token}',
            300,  # 5 minutes
            json.dumps(otp_data)
        )
        
        return otp_token
    
    def _send_login_otp(self, customer: frappe.Document, otp_token: str):
        """Send OTP via SMS for login verification"""
        try:
            # Get OTP code from Redis
            otp_data = json.loads(self.redis_client.get(f'otp_session:{otp_token}'))
            otp_code = otp_data['otp_code']
            
            # Send via SMS using communication management
            from universal_workshop.communication_management.api.sms_api import send_sms
            
            if frappe.local.lang == 'ar':
                message = f"رمز التحقق الخاص بك: {otp_code}\nصالح لمدة 5 دقائق فقط"
            else:
                message = f"Your verification code: {otp_code}\nValid for 5 minutes only"
            
            send_sms(
                to_number=customer.mobile_no,
                message=message,
                customer_id=customer.name,
                priority='High'
            )
            
        except Exception as e:
            frappe.log_error(f"Failed to send login OTP: {str(e)}", "Customer Portal Auth")
    
    def _validate_otp_session(self, otp_token: str, otp_code: str) -> Optional[str]:
        """Validate OTP session and code"""
        try:
            # Get OTP session data
            otp_data_str = self.redis_client.get(f'otp_session:{otp_token}')
            if not otp_data_str:
                return None
            
            otp_data = json.loads(otp_data_str)
            
            # Check attempts limit
            if otp_data.get('attempts', 0) >= 3:
                self.redis_client.delete(f'otp_session:{otp_token}')
                return None
            
            # Verify OTP code
            if otp_data['otp_code'] != otp_code:
                # Increment attempts
                otp_data['attempts'] = otp_data.get('attempts', 0) + 1
                self.redis_client.setex(
                    f'otp_session:{otp_token}',
                    self.redis_client.ttl(f'otp_session:{otp_token}'),
                    json.dumps(otp_data)
                )
                return None
            
            return otp_data['customer_id']
            
        except Exception:
            return None
    
    def _cleanup_otp_session(self, otp_token: str):
        """Clean up OTP session after successful verification"""
        self.redis_client.delete(f'otp_session:{otp_token}')
    
    def _is_account_locked(self, login_id: str) -> bool:
        """Check if account is temporarily locked"""
        lockout_key = f'lockout:{login_id}'
        return self.redis_client.exists(lockout_key)
    
    def _get_lockout_expiry(self, login_id: str) -> Optional[str]:
        """Get lockout expiry time"""
        lockout_key = f'lockout:{login_id}'
        ttl = self.redis_client.ttl(lockout_key)
        if ttl > 0:
            return (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
        return None
    
    def _record_failed_attempt(self, login_id: str, ip_address: str = None):
        """Record failed login attempt"""
        attempts_key = f'failed_attempts:{login_id}'
        
        # Increment attempt counter
        attempts = self.redis_client.incr(attempts_key)
        self.redis_client.expire(attempts_key, self.lockout_duration)
        
        # Lock account if max attempts reached
        if attempts >= self.max_login_attempts:
            lockout_key = f'lockout:{login_id}'
            self.redis_client.setex(lockout_key, self.lockout_duration, 'locked')
            self.redis_client.delete(attempts_key)
        
        # Log security event
        self._log_security_event(login_id, 'failed_login', ip_address, {'attempts': attempts})
    
    def _clear_failed_attempts(self, login_id: str):
        """Clear failed login attempts after successful login"""
        self.redis_client.delete(f'failed_attempts:{login_id}')
    
    def _is_token_blacklisted(self, token: str) -> bool:
        """Check if JWT token is blacklisted"""
        token_hash = frappe.utils.sha256_hash(token)
        return self.redis_client.exists(f'blacklisted_token:{token_hash}')
    
    def _blacklist_token(self, token: str, expires_at: int):
        """Add token to blacklist"""
        token_hash = frappe.utils.sha256_hash(token)
        ttl = max(0, expires_at - int(datetime.utcnow().timestamp()))
        if ttl > 0:
            self.redis_client.setex(f'blacklisted_token:{token_hash}', ttl, 'blacklisted')
    
    def _generate_password_reset_token(self, customer_id: str) -> str:
        """Generate password reset token"""
        reset_token = random_string(64)
        
        # Store reset token in Redis (1 hour expiry)
        reset_data = {
            'customer_id': customer_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.redis_client.setex(
            f'password_reset:{reset_token}',
            3600,  # 1 hour
            json.dumps(reset_data)
        )
        
        return reset_token
    
    def _send_password_reset_link(self, customer: frappe.Document, reset_token: str):
        """Send password reset link via SMS or email"""
        try:
            # Generate reset URL
            reset_url = f"{frappe.utils.get_url()}/portal/reset-password?token={reset_token}"
            
            # Send via SMS for Oman customers
            
            if frappe.local.lang == 'ar':
                message = f"لإعادة تعيين كلمة المرور، اضغط على الرابط: {reset_url}\nصالح لمدة ساعة واحدة"
            else:
                message = f"To reset your password, click: {reset_url}\nValid for 1 hour only"
            
            send_sms(
                to_number=customer.mobile_no,
                message=message,
                customer_id=customer.name,
                priority='High'
            )
            
        except Exception as e:
            frappe.log_error(f"Failed to send password reset: {str(e)}", "Customer Portal Auth")
    
    def _get_customer_profile(self, customer_id: str) -> Dict:
        """Get customer profile data for session"""
        customer = frappe.db.get_value(
            'Customer',
            customer_id,
            [
                'name', 'customer_name', 'customer_name_ar', 'email_id',
                'mobile_no', 'customer_group', 'territory'
            ],
            as_dict=True
        )
        
        return {
            'id': customer.name,
            'name': customer.customer_name,
            'name_ar': customer.customer_name_ar,
            'email': customer.email_id,
            'mobile': customer.mobile_no,
            'group': customer.customer_group,
            'territory': customer.territory
        }
    
    def _log_security_event(self, customer_id: str, event_type: str, ip_address: str = None, extra_data: Dict = None):
        """Log security events for audit trail"""
        try:
            log_data = {
                'customer_id': customer_id,
                'event_type': event_type,
                'ip_address': ip_address,
                'timestamp': datetime.utcnow().isoformat(),
                'user_agent': frappe.request.headers.get('User-Agent') if frappe.request else None
            }
            
            if extra_data:
                log_data.update(extra_data)
            
            # Store in Redis for recent events (7 days)
            self.redis_client.lpush(f'security_log:{customer_id}', json.dumps(log_data))
            self.redis_client.ltrim(f'security_log:{customer_id}', 0, 100)  # Keep last 100 events
            self.redis_client.expire(f'security_log:{customer_id}', 604800)  # 7 days
            
        except Exception as e:
            frappe.log_error(f"Failed to log security event: {str(e)}", "Customer Portal Auth")


# API methods for portal authentication

@frappe.whitelist(allow_guest=True)
def portal_login(login_id: str, password: str) -> Dict:
    """
    Customer portal login API
    
    Args:
        login_id: Customer email or phone number
        password: Customer password
        
    Returns:
        dict: Login result with token or 2FA requirement
    """
    auth = CustomerPortalAuth()
    ip_address = frappe.local.request_ip if frappe.local else None
    
    result = auth.authenticate_customer(login_id, password, ip_address)
    
    # Set HTTP-only cookie for web clients
    if result.get('success') and result.get('token'):
        frappe.local.response.set_cookie(
            'portal_token',
            result['token'],
            max_age=auth.session_duration,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
    
    return result


@frappe.whitelist(allow_guest=True)
def verify_2fa(otp_token: str, otp_code: str) -> Dict:
    """
    Verify 2FA OTP for customer login
    
    Args:
        otp_token: OTP session token
        otp_code: 6-digit OTP code
        
    Returns:
        dict: Authentication result with JWT token
    """
    auth = CustomerPortalAuth()
    ip_address = frappe.local.request_ip if frappe.local else None
    
    result = auth.verify_2fa_otp(otp_token, otp_code, ip_address)
    
    # Set HTTP-only cookie for web clients
    if result.get('success') and result.get('token'):
        frappe.local.response.set_cookie(
            'portal_token',
            result['token'],
            max_age=auth.session_duration,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
    
    return result


@frappe.whitelist()
def portal_logout() -> Dict:
    """
    Customer portal logout API
    
    Returns:
        dict: Logout result
    """
    auth = CustomerPortalAuth()
    ip_address = frappe.local.request_ip if frappe.local else None
    
    # Get token from header or cookie
    token = frappe.get_request_header('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    else:
        token = frappe.request.cookies.get('portal_token')
    
    if not token:
        return {'success': False, 'message': _('No active session')}
    
    result = auth.logout_customer(token, ip_address)
    
    # Clear cookie
    if result.get('success'):
        frappe.local.response.set_cookie(
            'portal_token',
            '',
            max_age=0,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
    
    return result


@frappe.whitelist(allow_guest=True)
def request_password_reset(login_id: str) -> Dict:
    """
    Request password reset for customer
    
    Args:
        login_id: Customer email or phone
        
    Returns:
        dict: Password reset request result
    """
    auth = CustomerPortalAuth()
    return auth.request_password_reset(login_id)


def get_current_customer() -> Optional[Dict]:
    """
    Get current authenticated customer from session
    
    Returns:
        dict: Customer session data or None
    """
    auth = CustomerPortalAuth()
    
    # Get token from header or cookie
    token = frappe.get_request_header('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    else:
        token = frappe.request.cookies.get('portal_token')
    
    if not token:
        return None
    
    return auth.verify_jwt_token(token)


def require_customer_auth():
    """
    Decorator function to require customer authentication
    Raises exception if no valid customer session
    """
    customer = get_current_customer()
    if not customer:
        frappe.throw(_('Authentication required'), frappe.AuthenticationError)
    
    frappe.local.customer = customer
    return customer 