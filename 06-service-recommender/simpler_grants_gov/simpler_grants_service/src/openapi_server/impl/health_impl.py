
from openapi_server.apis.health_api_base import BaseHealthApi
from openapi_server.models.healthcheck_response import HealthcheckResponse
# from fastapi import HTTPException

BASE_URL = "https://api.simpler.grants.gov/"

class HealthImpl(BaseHealthApi):
    async def health_get(self) -> HealthcheckResponse:
        """
        Returns the health status of the service.
        
        :return: HealthcheckResponse indicating the service is healthy.
        :rtype: HealthcheckResponse
        """
        # Here we can implement actual health checks if needed
        # For now, we return a simple healthy response
        return HealthcheckResponse(
            data={
                "base_url": BASE_URL,
                "version": "v0",
                "status": "healthy"
            },
            message="The service is running smoothly.",
            status_code=200,
        )
