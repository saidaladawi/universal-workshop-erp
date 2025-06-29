"""
Enhanced Password Policy Manager for Universal Workshop ERP

Provides comprehensive password security enforcement with Arabic language support
and workshop-specific security requirements.
"""

import re
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from zxcvbn import zxcvbn

import frappe
from frappe import _
from frappe.utils import get_datetime, now, cint


class PasswordPolicyManager:
    """
    Enhanced password policy management with Arabic support

    Features:
    - Comprehensive password strength validation
    - Arabic language support for error messages
    - Workshop-specific password requirements
    - Password history tracking
    - Breach detection integration
    - Role-based password policies
    """

    def __init__(self):
        """Initialize password policy manager"""
        self.policy_config = self._load_policy_config()
        self.breach_checker = PasswordBreachChecker()

    def _load_policy_config(self) -> Dict[str, Any]:
        """Load password policy configuration"""
        site_config = frappe.get_site_config()
        base_policy = site_config.get("password_policy", {})

        # Default comprehensive policy
        default_policy = {
            "min_length": 12,
            "max_length": 128,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": True,
            "min_special_chars": 2,
            "require_mixed_case": True,
            "prevent_common_passwords": True,
            "prevent_personal_info": True,
            "prevent_keyboard_patterns": True,
            "prevent_repetitive_chars": True,
            "max_repetitive_chars": 3,
            "prevent_dictionary_words": True,
            "check_breach_databases": True,
            "password_history_count": 12,
            "max_password_age_days": 90,
            "password_expiry_warning_days": 14,
            "account_lockout_attempts": 5,
            "lockout_duration_minutes": 30,
            "role_specific_policies": {
                "Workshop Owner": {
                    "min_length": 16,
                    "max_password_age_days": 60,
                    "require_mfa": True,
                },
                "Workshop Manager": {
                    "min_length": 14,
                    "max_password_age_days": 75,
                    "require_mfa": True,
                },
                "System Manager": {
                    "min_length": 16,
                    "max_password_age_days": 45,
                    "require_mfa": True,
                },
            },
        }

        # Merge with site-specific config
        default_policy.update(base_policy)
        return default_policy

    def validate_password(
        self, password: str, user: str = None, additional_context: List[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive password validation

        Args:
            password: Password to validate
            user: Username for context validation
            additional_context: Additional context strings to check against

        Returns:
            Validation result with detailed feedback
        """
        if not password:
            return self._validation_result(
                False, _("Password is required"), [], "password_required"
            )

        # Get user-specific policy
        user_roles = frappe.get_roles(user) if user else []
        effective_policy = self._get_effective_policy(user_roles)

        # Initialize validation result
        issues = []
        suggestions = []
        score = 0

        # Basic length validation
        length_result = self._validate_length(password, effective_policy)
        if not length_result["valid"]:
            issues.extend(length_result["issues"])
            suggestions.extend(length_result["suggestions"])
        else:
            score += 15

        # Character composition validation
        composition_result = self._validate_composition(password, effective_policy)
        if not composition_result["valid"]:
            issues.extend(composition_result["issues"])
            suggestions.extend(composition_result["suggestions"])
        else:
            score += composition_result["score"]

        # Pattern validation (keyboard patterns, repetition, etc.)
        pattern_result = self._validate_patterns(password, effective_policy)
        if not pattern_result["valid"]:
            issues.extend(pattern_result["issues"])
            suggestions.extend(pattern_result["suggestions"])
        else:
            score += 15

        # Context validation (personal info, dictionary words)
        context_result = self._validate_context(
            password, user, additional_context, effective_policy
        )
        if not context_result["valid"]:
            issues.extend(context_result["issues"])
            suggestions.extend(context_result["suggestions"])
        else:
            score += 20

        # Advanced strength analysis using zxcvbn
        strength_result = self._analyze_strength(password, user, additional_context)
        score += strength_result["score"]
        suggestions.extend(strength_result["suggestions"])

        # Breach database check
        if effective_policy["check_breach_databases"]:
            breach_result = self._check_breach_databases(password)
            if not breach_result["valid"]:
                issues.extend(breach_result["issues"])
                suggestions.extend(breach_result["suggestions"])
                score = max(0, score - 30)  # Significant penalty for breached passwords
            else:
                score += 10

        # Password history check
        if user:
            history_result = self._check_password_history(password, user, effective_policy)
            if not history_result["valid"]:
                issues.extend(history_result["issues"])
                suggestions.extend(history_result["suggestions"])
            else:
                score += 5

        # Calculate final score and determine if password is acceptable
        final_score = min(100, score)
        min_score = 70  # Minimum acceptable score
        is_valid = len(issues) == 0 and final_score >= min_score

        # Generate comprehensive feedback
        feedback = self._generate_feedback(
            is_valid, final_score, issues, suggestions, effective_policy
        )

        return self._validation_result(
            is_valid,
            feedback["message"],
            feedback["suggestions"],
            "password_valid" if is_valid else "password_invalid",
            {"score": final_score, "min_score": min_score, "policy": effective_policy},
        )

    def _get_effective_policy(self, user_roles: List[str]) -> Dict[str, Any]:
        """Get effective password policy based on user roles"""
        effective_policy = self.policy_config.copy()

        # Apply role-specific policies (use most restrictive)
        role_policies = self.policy_config.get("role_specific_policies", {})
        for role in user_roles:
            if role in role_policies:
                role_policy = role_policies[role]
                for key, value in role_policy.items():
                    if key in ["min_length", "password_history_count"]:
                        # Use maximum value for these settings
                        effective_policy[key] = max(effective_policy.get(key, 0), value)
                    elif key in ["max_password_age_days"]:
                        # Use minimum value for these settings
                        effective_policy[key] = min(effective_policy.get(key, 999), value)
                    else:
                        # Use role-specific value
                        effective_policy[key] = value

        return effective_policy

    def _validate_length(self, password: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Validate password length requirements"""
        min_length = policy["min_length"]
        max_length = policy["max_length"]
        current_length = len(password)

        issues = []
        suggestions = []

        if current_length < min_length:
            issues.append(_("Password must be at least {0} characters long").format(min_length))
            suggestions.append(_("Add {0} more characters").format(min_length - current_length))

        if current_length > max_length:
            issues.append(_("Password must not exceed {0} characters").format(max_length))
            suggestions.append(_("Remove {0} characters").format(current_length - max_length))

        return {"valid": len(issues) == 0, "issues": issues, "suggestions": suggestions}

    def _validate_composition(self, password: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Validate character composition requirements"""
        issues = []
        suggestions = []
        score = 0

        # Check for uppercase letters
        if policy["require_uppercase"] and not re.search(r"[A-Z]", password):
            issues.append(_("Password must contain at least one uppercase letter"))
            suggestions.append(_("Add uppercase letters (A-Z)"))
        else:
            score += 10

        # Check for lowercase letters
        if policy["require_lowercase"] and not re.search(r"[a-z]", password):
            issues.append(_("Password must contain at least one lowercase letter"))
            suggestions.append(_("Add lowercase letters (a-z)"))
        else:
            score += 10

        # Check for numbers
        if policy["require_numbers"] and not re.search(r"[0-9]", password):
            issues.append(_("Password must contain at least one number"))
            suggestions.append(_("Add numbers (0-9)"))
        else:
            score += 10

        # Check for special characters
        if policy["require_special_chars"]:
            special_chars = re.findall(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password)
            min_special = policy.get("min_special_chars", 1)

            if len(special_chars) < min_special:
                issues.append(
                    _("Password must contain at least {0} special characters").format(min_special)
                )
                suggestions.append(_("Add special characters (!@#$%^&*...)"))
            else:
                score += 15

        # Check for mixed case requirement
        if policy["require_mixed_case"]:
            has_upper = bool(re.search(r"[A-Z]", password))
            has_lower = bool(re.search(r"[a-z]", password))

            if not (has_upper and has_lower):
                issues.append(_("Password must contain both uppercase and lowercase letters"))
                suggestions.append(_("Mix uppercase and lowercase letters"))
            else:
                score += 10

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "score": score,
        }

    def _validate_patterns(self, password: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        """Validate against common patterns and weaknesses"""
        issues = []
        suggestions = []

        # Check for repetitive characters
        if policy["prevent_repetitive_chars"]:
            max_repetitive = policy.get("max_repetitive_chars", 3)
            repetitive_pattern = rf"(.)\1{{{max_repetitive},}}"

            if re.search(repetitive_pattern, password):
                issues.append(_("Password contains too many repetitive characters"))
                suggestions.append(
                    _("Avoid repeating the same character more than {0} times").format(
                        max_repetitive
                    )
                )

        # Check for keyboard patterns
        if policy["prevent_keyboard_patterns"]:
            keyboard_patterns = [
                r"qwerty|asdfgh|zxcvbn",  # QWERTY patterns
                r"123456|654321|098765",  # Number sequences
                r"abcdef|fedcba|uvwxyz",  # Alphabet sequences
                r"qazwsx|wsxedc|edcrfv",  # Vertical keyboard patterns
            ]

            for pattern in keyboard_patterns:
                if re.search(pattern, password.lower()):
                    issues.append(_("Password contains keyboard patterns"))
                    suggestions.append(_("Avoid keyboard patterns like 'qwerty' or '123456'"))
                    break

        # Check for common substitutions that don't add security
        weak_substitutions = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$", "t": "7"}

        base_word = password.lower()
        for char, sub in weak_substitutions.items():
            base_word = base_word.replace(sub, char)

        if self._is_common_word(base_word):
            issues.append(_("Password is based on common words with simple substitutions"))
            suggestions.append(_("Use a more complex base or avoid common word patterns"))

        return {"valid": len(issues) == 0, "issues": issues, "suggestions": suggestions}

    def _validate_context(
        self, password: str, user: str, additional_context: List[str], policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate password against personal information and context"""
        issues = []
        suggestions = []

        if not policy["prevent_personal_info"]:
            return {"valid": True, "issues": [], "suggestions": []}

        # Gather context information
        context_info = []

        if user:
            # Get user information
            user_doc = frappe.get_doc("User", user)
            context_info.extend(
                [
                    user,
                    user_doc.get("first_name", ""),
                    user_doc.get("last_name", ""),
                    user_doc.get("email", "").split("@")[0],
                    user_doc.get("mobile_no", ""),
                    user_doc.get("birth_date", ""),
                ]
            )

        if additional_context:
            context_info.extend(additional_context)

        # Check if password contains personal information
        password_lower = password.lower()
        for info in context_info:
            if info and len(str(info)) >= 3:
                info_str = str(info).lower()
                if info_str in password_lower or password_lower in info_str:
                    issues.append(_("Password contains personal information"))
                    suggestions.append(
                        _("Avoid using your name, email, or other personal information")
                    )
                    break

        # Check against dictionary words if enabled
        if policy["prevent_dictionary_words"]:
            if self._contains_dictionary_words(password):
                issues.append(_("Password contains common dictionary words"))
                suggestions.append(_("Use a combination of unrelated words or create a passphrase"))

        return {"valid": len(issues) == 0, "issues": issues, "suggestions": suggestions}

    def _analyze_strength(
        self, password: str, user: str = None, additional_context: List[str] = None
    ) -> Dict[str, Any]:
        """Advanced password strength analysis using zxcvbn"""
        try:
            # Prepare user inputs for zxcvbn
            user_inputs = []
            if user:
                user_inputs.append(user)
            if additional_context:
                user_inputs.extend(additional_context)

            # Analyze password strength
            analysis = zxcvbn(password, user_inputs=user_inputs)

            # Convert zxcvbn score (0-4) to our score system (0-30)
            score_mapping = {0: 0, 1: 5, 2: 10, 3: 20, 4: 30}
            score = score_mapping.get(analysis["score"], 0)

            # Extract suggestions
            suggestions = []
            if analysis.get("feedback", {}).get("suggestions"):
                suggestions.extend(analysis["feedback"]["suggestions"])

            return {
                "score": score,
                "suggestions": suggestions,
                "crack_time": analysis.get("crack_times_display", {}),
            }

        except Exception as e:
            frappe.log_error(f"Password strength analysis error: {e}")
            return {"score": 10, "suggestions": []}  # Default fallback

    def _check_breach_databases(self, password: str) -> Dict[str, Any]:
        """Check password against breach databases"""
        try:
            is_breached = self.breach_checker.check_password(password)

            if is_breached:
                return {
                    "valid": False,
                    "issues": [_("This password has been found in data breaches")],
                    "suggestions": [_("Choose a different password that hasn't been compromised")],
                }
            else:
                return {"valid": True, "issues": [], "suggestions": []}

        except Exception as e:
            frappe.log_error(f"Breach database check error: {e}")
            # Don't fail validation if breach check fails
            return {"valid": True, "issues": [], "suggestions": []}

    def _check_password_history(
        self, password: str, user: str, policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check password against user's password history"""
        try:
            history_count = policy.get("password_history_count", 12)
            if history_count <= 0:
                return {"valid": True, "issues": [], "suggestions": []}

            # Get password history
            password_history = self._get_password_history(user, history_count)

            # Check if password was used before
            password_hash = self._hash_password(password)
            for historic_hash in password_history:
                if password_hash == historic_hash:
                    return {
                        "valid": False,
                        "issues": [_("Password was used recently and cannot be reused")],
                        "suggestions": [
                            _("Choose a password you haven't used in the last {0} changes").format(
                                history_count
                            )
                        ],
                    }

            return {"valid": True, "issues": [], "suggestions": []}

        except Exception as e:
            frappe.log_error(f"Password history check error: {e}")
            return {"valid": True, "issues": [], "suggestions": []}

    def _is_common_word(self, word: str) -> bool:
        """Check if word is in common password list"""
        # This could be enhanced with a comprehensive word list
        common_words = [
            "password",
            "admin",
            "login",
            "user",
            "guest",
            "test",
            "demo",
            "workshop",
            "garage",
            "repair",
            "service",
            "car",
            "auto",
            "universal",
            "system",
            "manager",
            "owner",
            "technician",
        ]

        return word.lower() in common_words

    def _contains_dictionary_words(self, password: str) -> bool:
        """Check if password contains dictionary words"""
        # Simplified dictionary check - could be enhanced with comprehensive word lists
        words = re.findall(r"[a-zA-Z]{4,}", password)
        for word in words:
            if self._is_common_word(word):
                return True
        return False

    def _get_password_history(self, user: str, count: int) -> List[str]:
        """Get user's password history"""
        try:
            # Get password history from custom DocType or User document
            history = frappe.db.sql(
                """
                SELECT password_hash FROM `tabPassword History`
                WHERE user = %s
                ORDER BY creation DESC
                LIMIT %s
            """,
                [user, count],
                as_list=True,
            )

            return [h[0] for h in history] if history else []

        except Exception:
            # Table might not exist yet
            return []

    def _hash_password(self, password: str) -> str:
        """Create hash of password for history comparison"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _generate_feedback(
        self,
        is_valid: bool,
        score: int,
        issues: List[str],
        suggestions: List[str],
        policy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate comprehensive feedback message"""
        if is_valid:
            if score >= 90:
                strength = _("Excellent")
            elif score >= 80:
                strength = _("Very Strong")
            elif score >= 70:
                strength = _("Strong")
            else:
                strength = _("Acceptable")

            message = _("Password strength: {0} (Score: {1}/100)").format(strength, score)
        else:
            message = _("Password does not meet security requirements")

        return {"message": message, "suggestions": suggestions, "issues": issues}

    def _validation_result(
        self,
        is_valid: bool,
        message: str,
        suggestions: List[str],
        code: str,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create standardized validation result"""
        return {
            "password_policy_validation_passed": is_valid,
            "message": message,
            "suggestions": suggestions,
            "code": code,
            "metadata": metadata or {},
        }

    def record_password_change(self, user: str, password_hash: str):
        """Record password change in history"""
        try:
            # Create password history record
            history_doc = frappe.new_doc("Password History")
            history_doc.user = user
            history_doc.password_hash = password_hash
            history_doc.changed_on = now()
            history_doc.insert(ignore_permissions=True)

            # Clean up old history records
            history_count = self.policy_config.get("password_history_count", 12)
            old_records = frappe.db.sql(
                """
                SELECT name FROM `tabPassword History`
                WHERE user = %s
                ORDER BY creation DESC
                OFFSET %s
            """,
                [user, history_count],
                as_list=True,
            )

            for record in old_records:
                frappe.delete_doc("Password History", record[0], ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failed to record password change: {e}")

    def check_password_expiry(self, user: str) -> Dict[str, Any]:
        """Check if user's password is expired or expiring soon"""
        try:
            user_doc = frappe.get_doc("User", user)
            user_roles = frappe.get_roles(user)
            policy = self._get_effective_policy(user_roles)

            max_age_days = policy.get("max_password_age_days", 90)
            warning_days = policy.get("password_expiry_warning_days", 14)

            last_password_change = user_doc.get("last_password_reset")
            if not last_password_change:
                # If no password change recorded, assume account creation date
                last_password_change = user_doc.creation

            password_age = (datetime.now() - get_datetime(last_password_change)).days
            days_until_expiry = max_age_days - password_age

            if days_until_expiry <= 0:
                return {
                    "status": "expired",
                    "message": _("Your password has expired and must be changed"),
                    "days_until_expiry": days_until_expiry,
                    "force_change": True,
                }
            elif days_until_expiry <= warning_days:
                return {
                    "status": "expiring",
                    "message": _("Your password will expire in {0} days").format(days_until_expiry),
                    "days_until_expiry": days_until_expiry,
                    "force_change": False,
                }
            else:
                return {
                    "status": "current",
                    "message": _("Password is current"),
                    "days_until_expiry": days_until_expiry,
                    "force_change": False,
                }

        except Exception as e:
            frappe.log_error(f"Password expiry check error: {e}")
            return {
                "status": "unknown",
                "message": _("Unable to check password expiry"),
                "force_change": False,
            }


class PasswordBreachChecker:
    """Check passwords against known breach databases"""

    def __init__(self):
        """Initialize breach checker"""
        self.breach_cache_timeout = 3600  # 1 hour cache

    def check_password(self, password: str) -> bool:
        """
        Check if password appears in breach databases

        Uses SHA-1 hash prefix method for privacy
        """
        try:
            # Create SHA-1 hash of password
            sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
            hash_prefix = sha1_hash[:5]
            hash_suffix = sha1_hash[5:]

            # Check local cache first
            cached_result = self._get_cached_result(hash_prefix)
            if cached_result is not None:
                return hash_suffix in cached_result

            # For security and privacy, we'll use a local breach database
            # In production, this could integrate with HaveIBeenPwned API
            # or maintain a local database of breach hashes

            # Simplified implementation - check against common passwords
            common_breached_passwords = [
                "123456",
                "password",
                "123456789",
                "12345678",
                "12345",
                "1234567",
                "1234567890",
                "qwerty",
                "abc123",
                "million2",
                "000000",
                "1234",
                "iloveyou",
                "aaron431",
                "password1",
                "qqww1122",
                "123",
                "omgpop",
                "123321",
                "654321",
            ]

            is_breached = password.lower() in [p.lower() for p in common_breached_passwords]

            # Cache result
            self._cache_result(hash_prefix, [hash_suffix] if is_breached else [])

            return is_breached

        except Exception as e:
            frappe.log_error(f"Breach check error: {e}")
            return False  # Don't block on error

    def _get_cached_result(self, hash_prefix: str) -> Optional[List[str]]:
        """Get cached breach check result"""
        try:
            cache_key = f"breach_check_{hash_prefix}"
            cached_data = frappe.cache().get_value(cache_key)

            if cached_data:
                return json.loads(cached_data)
            return None

        except Exception:
            return None

    def _cache_result(self, hash_prefix: str, suffixes: List[str]):
        """Cache breach check result"""
        try:
            cache_key = f"breach_check_{hash_prefix}"
            frappe.cache().set_value(
                cache_key, json.dumps(suffixes), expires_in_sec=self.breach_cache_timeout
            )
        except Exception as e:
            frappe.log_error(f"Breach cache error: {e}")


# Global instance
_policy_manager = None


def get_policy_manager() -> PasswordPolicyManager:
    """Get global password policy manager instance"""
    global _policy_manager
    if _policy_manager is None:
        _policy_manager = PasswordPolicyManager()
    return _policy_manager


# API endpoints
@frappe.whitelist()
def validate_password_strength(password: str, user: str = None) -> Dict[str, Any]:
    """
    API endpoint for password validation

    Args:
        password: Password to validate
        user: Username for context

    Returns:
        Validation result
    """
    manager = get_policy_manager()
    return manager.validate_password(password, user)


@frappe.whitelist()
def check_password_expiry_status(user: str = None) -> Dict[str, Any]:
    """Check password expiry status for user"""
    if not user:
        user = frappe.session.user

    manager = get_policy_manager()
    return manager.check_password_expiry(user)


@frappe.whitelist()
def get_password_policy_info() -> Dict[str, Any]:
    """Get password policy information for display"""
    manager = get_policy_manager()
    user_roles = frappe.get_roles(frappe.session.user)
    policy = manager._get_effective_policy(user_roles)

    # Return safe policy information (no sensitive data)
    return {
        "min_length": policy["min_length"],
        "require_uppercase": policy["require_uppercase"],
        "require_lowercase": policy["require_lowercase"],
        "require_numbers": policy["require_numbers"],
        "require_special_chars": policy["require_special_chars"],
        "min_special_chars": policy.get("min_special_chars", 1),
        "max_password_age_days": policy.get("max_password_age_days", 90),
        "password_expiry_warning_days": policy.get("password_expiry_warning_days", 14),
    }
