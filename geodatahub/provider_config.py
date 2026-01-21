"""
Provider Configuration Tracker

Tracks which EODAG providers are configured and helps users set up new ones.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .eodag_catalog import (
    EODAG_PROVIDERS, EODAG_PRODUCTS, ProviderInfo, ProviderStatus,
    get_providers_for_product, get_alternative_providers, get_provider_auth_guide
)


@dataclass
class ProviderConfigStatus:
    """Status of a provider's configuration."""
    provider: str
    configured: bool
    tested: bool
    has_credentials: bool
    error_message: Optional[str] = None


class ProviderConfigManager:
    """Manages EODAG provider configurations."""

    def __init__(self, eodag_config_path: Optional[str] = None):
        """Initialize with optional custom config path."""
        if eodag_config_path:
            self.config_path = Path(eodag_config_path)
        else:
            # Default EODAG config location
            if os.name == 'nt':  # Windows
                self.config_path = Path.home() / ".config" / "eodag" / "eodag.yml"
            else:  # Linux/Mac
                self.config_path = Path.home() / ".config" / "eodag" / "eodag.yml"

        self._config_cache = None
        self._status_cache: Dict[str, ProviderConfigStatus] = {}

    def _load_config(self) -> Dict:
        """Load EODAG configuration file."""
        if self._config_cache is not None:
            return self._config_cache

        if not self.config_path.exists():
            self._config_cache = {}
            return self._config_cache

        try:
            with open(self.config_path, 'r') as f:
                self._config_cache = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading EODAG config: {e}")
            self._config_cache = {}

        return self._config_cache

    def refresh_config(self):
        """Reload configuration from file."""
        self._config_cache = None
        self._status_cache = {}
        self._load_config()

    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider has credentials configured."""
        config = self._load_config()

        if provider not in config:
            return False

        provider_config = config[provider]
        if not provider_config:
            return False

        # Check for auth credentials
        auth = provider_config.get('auth', {})
        if not auth:
            # Some providers don't need auth (e.g., earth_search)
            if provider in EODAG_PROVIDERS:
                return not EODAG_PROVIDERS[provider].requires_auth
            return False

        # Check for credentials or api_key
        credentials = auth.get('credentials', {})
        if credentials:
            username = credentials.get('username', '')
            password = credentials.get('password', '')
            if username and password:
                return True

        # Check for API key
        api_key = auth.get('api_key', '') or auth.get('apikey', '')
        if api_key:
            return True

        return False

    def get_provider_status(self, provider: str) -> ProviderConfigStatus:
        """Get detailed status of a provider's configuration."""
        if provider in self._status_cache:
            return self._status_cache[provider]

        configured = self.is_provider_configured(provider)

        # Check if provider requires auth
        if provider in EODAG_PROVIDERS:
            needs_auth = EODAG_PROVIDERS[provider].requires_auth
            if not needs_auth:
                configured = True  # No auth needed

        status = ProviderConfigStatus(
            provider=provider,
            configured=configured,
            tested=False,  # Would need actual API call to test
            has_credentials=configured
        )

        self._status_cache[provider] = status
        return status

    def get_all_provider_statuses(self) -> Dict[str, ProviderConfigStatus]:
        """Get status of all known providers."""
        statuses = {}
        for provider in EODAG_PROVIDERS:
            statuses[provider] = self.get_provider_status(provider)
        return statuses

    def get_configured_providers(self) -> List[str]:
        """Get list of configured provider names."""
        return [
            provider for provider in EODAG_PROVIDERS
            if self.is_provider_configured(provider)
        ]

    def get_unconfigured_providers(self) -> List[str]:
        """Get list of unconfigured provider names."""
        return [
            provider for provider in EODAG_PROVIDERS
            if not self.is_provider_configured(provider) and EODAG_PROVIDERS[provider].requires_auth
        ]

    def can_access_product(self, product_id: str) -> Tuple[bool, List[str]]:
        """
        Check if any configured provider can access a product.
        Returns (can_access, list_of_available_providers).
        """
        if product_id not in EODAG_PRODUCTS:
            return False, []

        providers = get_providers_for_product(product_id)
        available = []

        for provider in providers:
            if self.is_provider_configured(provider):
                available.append(provider)

        return len(available) > 0, available

    def get_provider_recommendation(self, product_id: str) -> Dict:
        """
        Get provider recommendation for a product.
        Returns configured providers, and suggests setup for unconfigured ones.
        """
        if product_id not in EODAG_PRODUCTS:
            return {
                "status": "product_not_found",
                "product_id": product_id,
                "message": f"Product {product_id} not found in catalog"
            }

        providers = get_providers_for_product(product_id)
        configured = []
        unconfigured = []
        no_auth_needed = []

        for provider in providers:
            if provider not in EODAG_PROVIDERS:
                continue

            provider_info = EODAG_PROVIDERS[provider]

            if not provider_info.requires_auth:
                no_auth_needed.append(provider)
            elif self.is_provider_configured(provider):
                configured.append(provider)
            else:
                unconfigured.append({
                    "provider": provider,
                    "name": provider_info.name,
                    "url": provider_info.url,
                    "registration_url": provider_info.registration_url,
                    "free_access": provider_info.free_access
                })

        # Determine recommendation
        if no_auth_needed:
            return {
                "status": "available",
                "product_id": product_id,
                "recommended_provider": no_auth_needed[0],
                "message": f"No authentication needed. Using {no_auth_needed[0]}",
                "no_auth_providers": no_auth_needed,
                "configured_providers": configured,
                "setup_required": []
            }
        elif configured:
            # Sort by priority
            sorted_providers = sorted(
                configured,
                key=lambda p: EODAG_PROVIDERS[p].priority if p in EODAG_PROVIDERS else 0,
                reverse=True
            )
            return {
                "status": "available",
                "product_id": product_id,
                "recommended_provider": sorted_providers[0],
                "message": f"Using configured provider: {sorted_providers[0]}",
                "configured_providers": configured,
                "setup_required": []
            }
        else:
            # Need to configure a provider
            # Prioritize free providers
            free_providers = [p for p in unconfigured if p["free_access"]]
            setup_list = free_providers if free_providers else unconfigured

            return {
                "status": "setup_required",
                "product_id": product_id,
                "message": "No configured provider available. Please set up one of the following:",
                "configured_providers": [],
                "setup_required": setup_list[:3]  # Top 3 options
            }

    def generate_config_snippet(self, provider: str) -> str:
        """Generate YAML config snippet for a provider."""
        if provider not in EODAG_PROVIDERS:
            return f"# Provider '{provider}' not found"

        info = EODAG_PROVIDERS[provider]

        snippet = f"# {info.name}\n"
        snippet += f"# {info.url}\n"
        if info.registration_url:
            snippet += f"# Register at: {info.registration_url}\n"
        snippet += f"{provider}:\n"

        if info.auth_type == "credentials":
            snippet += "  auth:\n"
            snippet += "    credentials:\n"
            snippet += "      username: YOUR_USERNAME\n"
            snippet += "      password: YOUR_PASSWORD\n"
        elif info.auth_type == "api_key":
            snippet += "  auth:\n"
            snippet += "    api_key: YOUR_API_KEY\n"
        else:
            snippet += "  # No authentication required\n"

        return snippet

    def get_setup_guide(self, provider: str) -> Dict:
        """Get complete setup guide for a provider."""
        if provider not in EODAG_PROVIDERS:
            return {"error": f"Provider '{provider}' not found"}

        info = EODAG_PROVIDERS[provider]

        return {
            "provider": provider,
            "name": info.name,
            "description": info.description,
            "url": info.url,
            "free_access": info.free_access,
            "steps": [
                f"1. Go to {info.registration_url or info.url}",
                "2. Create a free account" if info.free_access else "2. Create an account (may require payment)",
                "3. Get your credentials (username/password or API key)",
                f"4. Open your EODAG config file: {self.config_path}",
                "5. Add the following configuration:",
            ],
            "config_snippet": self.generate_config_snippet(provider),
            "config_path": str(self.config_path),
            "products_available": [
                p for p, info in EODAG_PRODUCTS.items()
                if provider in info.providers
            ][:10]  # First 10 products
        }


# Singleton instance
_config_manager: Optional[ProviderConfigManager] = None


def get_config_manager() -> ProviderConfigManager:
    """Get the singleton ProviderConfigManager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ProviderConfigManager()
    return _config_manager


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def check_product_access(product_id: str) -> Dict:
    """Quick check if a product is accessible."""
    return get_config_manager().get_provider_recommendation(product_id)


def get_configured_providers_list() -> List[str]:
    """Get list of configured providers."""
    return get_config_manager().get_configured_providers()


def get_setup_instructions(provider: str) -> Dict:
    """Get setup instructions for a provider."""
    return get_config_manager().get_setup_guide(provider)


def suggest_provider_for_analysis(analysis_keywords: List[str]) -> Dict:
    """
    Suggest the best provider setup based on analysis keywords.
    """
    from .eodag_catalog import search_products

    # Find relevant products
    matching_products = []
    for keyword in analysis_keywords:
        matching_products.extend(search_products(keyword))

    # Remove duplicates
    seen = set()
    unique_products = []
    for p in matching_products:
        if p.id not in seen:
            seen.add(p.id)
            unique_products.append(p)

    if not unique_products:
        return {
            "status": "no_products_found",
            "message": "No matching products found for your analysis",
            "keywords": analysis_keywords
        }

    # Check which providers are needed
    manager = get_config_manager()
    needed_providers = set()
    available_products = []
    unavailable_products = []

    for product in unique_products:
        can_access, providers = manager.can_access_product(product.id)
        if can_access:
            available_products.append({
                "product": product.id,
                "providers": providers
            })
        else:
            unavailable_products.append({
                "product": product.id,
                "needs_providers": product.providers
            })
            needed_providers.update(product.providers)

    return {
        "status": "analysis_complete",
        "available_products": available_products,
        "unavailable_products": unavailable_products,
        "providers_to_configure": [
            manager.get_setup_guide(p) for p in list(needed_providers)[:3]
        ]
    }
