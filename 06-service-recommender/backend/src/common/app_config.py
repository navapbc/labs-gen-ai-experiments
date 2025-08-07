import os


class AppConfig:
    # If None, then phoenix.client.Client defaults to PHOENIX_COLLECTOR_ENDPOINT env variable value or "http://localhost:6006"
    phoenix_base_url = os.environ.get(
        "PHOENIX_COLLECTOR_ENDPOINT", "https://phoenix:6006"
    )
    disable_ssl_verification = (
        os.environ.get("DISABLE_SSL_VERIFICATION", "false").lower() == "true"
    )


config = AppConfig()

print("Using Phoenix endpoint:", config.phoenix_base_url)
