class OddsProviderError(Exception):
    """Base error for failures while fetching or normalizing provider data."""

    error_type = "provider_error"


class ProviderTimeoutError(OddsProviderError):
    error_type = "timeout"


class ProviderAuthError(OddsProviderError):
    error_type = "auth_failed"


class ProviderRateLimitError(OddsProviderError):
    error_type = "rate_limited"


class ProviderQuotaError(OddsProviderError):
    error_type = "quota_low"


class ProviderUpstreamError(OddsProviderError):
    error_type = "upstream_error"


class ProviderPayloadError(OddsProviderError):
    error_type = "invalid_payload"