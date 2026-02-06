"""EdgeAdapter -- macOS Apple Silicon platform adapter for the Nebulus ecosystem."""

import os
from pathlib import Path

from nebulus_core.platform.base import ServiceInfo


class EdgeAdapter:
    """macOS Apple Silicon platform adapter using PM2."""

    @property
    def platform_name(self) -> str:
        """Platform identifier."""
        return "edge"

    @property
    def llm_base_url(self) -> str:
        """OpenAI-compatible endpoint base URL."""
        host = os.getenv("NEBULUS_LLM_HOST", "localhost")
        port = os.getenv("NEBULUS_LLM_PORT", "8080")
        return f"http://{host}:{port}/v1"

    @property
    def chroma_settings(self) -> dict:
        """ChromaDB embedded-mode connection config."""
        default_path = str(
            Path(__file__).parent.parent / "intelligence" / "storage" / "vectors"
        )
        return {
            "mode": "embedded",
            "path": os.getenv("NEBULUS_CHROMA_PATH", default_path),
        }

    @property
    def default_model(self) -> str:
        """Default LLM model name for Apple Silicon."""
        return os.getenv("NEBULUS_MODEL", "mlx-community/Meta-Llama-3.1-8B-Instruct")

    @property
    def data_dir(self) -> Path:
        """Root directory for persistent data."""
        return Path(
            os.getenv(
                "NEBULUS_DATA_DIR",
                str(Path(__file__).parent.parent / "intelligence" / "storage"),
            )
        )

    @property
    def services(self) -> list[ServiceInfo]:
        """All services managed by this platform."""
        return [
            ServiceInfo(
                name="brain",
                port=8080,
                health_endpoint="http://localhost:8080/v1/models",
                description="MLX LLM inference server",
            ),
            ServiceInfo(
                name="intelligence",
                port=8081,
                health_endpoint="http://localhost:8081/health",
                description="Intelligence data analysis service",
            ),
        ]

    def start_services(self) -> None:
        """Start all platform services via PM2."""
        import subprocess

        subprocess.run(
            ["pm2", "start", "infrastructure/pm2_config.json"], check=True
        )

    def stop_services(self) -> None:
        """Stop all platform services via PM2."""
        import subprocess

        subprocess.run(["pm2", "stop", "all"], check=True)

    def restart_services(self, service: str | None = None) -> None:
        """Restart one or all services via PM2.

        Args:
            service: Specific service name, or None for all.
        """
        import subprocess

        cmd = ["pm2", "restart"]
        cmd.append(service if service else "all")
        subprocess.run(cmd, check=True)

    def get_logs(self, service: str, follow: bool = False) -> None:
        """Stream logs for a service via PM2.

        Args:
            service: Service name to get logs for.
            follow: Whether to follow/tail the log output.
        """
        import subprocess

        cmd = ["pm2", "logs", service]
        if not follow:
            cmd.append("--nostream")
        subprocess.run(cmd)

    def platform_specific_commands(self) -> list:
        """Return additional Click commands for this platform."""
        return []
