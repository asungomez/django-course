import docker.models
import docker.models.networks
import pytest
from testcontainers.core.container import DockerContainer  # type: ignore
from testcontainers.core.network import Network  # type: ignore
from testcontainers.core.waiting_utils import wait_for_logs  # type: ignore
import docker
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def api_url(request: pytest.FixtureRequest) -> str:
    """Spin up all necessary containers and return the API URL."""
    url = None
    api_container: DockerContainer = None
    client = docker.from_env()
    image = None
    network: Network = None
    db_container: DockerContainer = None

    def cleanup() -> None:
        try:
            if api_container is not None:
                logger.info("Stopping API container")
                api_container.stop()
                api_container._container.remove(force=True)
            if db_container is not None:
                logger.info("Stopping database container")
                db_container.stop()
                db_container._container.remove(force=True)
            if network is not None:
                logger.info("Removing network")
                network.remove()
            if image is not None:
                logger.info("Removing image")
                client.images.remove(image.id, force=True)
        except Exception as e:
            logger.error("Error during cleanup: %s", str(e))

    request.addfinalizer(cleanup)

    try:
        # Create Docker Network
        network = Network().create()

        # Create a Posgres container inside the network
        logger.info("Starting PostgreSQL container")
        db_container = (
            DockerContainer(image="postgres:17-alpine")
            .with_exposed_ports(5432)
            .with_env("POSTGRES_DB", "test")
            .with_env("POSTGRES_USER", "test")
            .with_env("POSTGRES_PASSWORD", "test")
            .with_network(network)
            .with_network_aliases(("db"))
            .start()
        )
        # Get the exposed port for the database
        db_port = db_container.get_exposed_port(5432)

        # Build the API image
        build_env = os.environ.get("BUILD_ENV", "development")
        logger.info("Building image")
        image, _ = client.images.build(
            path=".",
            buildargs={"BUILD_ENV": build_env}
            )

        # Spin up the API container
        logger.info("Starting container")
        api_container = (
            DockerContainer(image=image.id)
            .with_exposed_ports(8000)
            .with_env("DB_HOST", "db")
            .with_env("DB_NAME", "test")
            .with_env("DB_PASSWORD", "test")
            .with_env("DB_PORT", db_port)
            .with_env("DB_USER", "test")
            .with_env("DEBUG", "True")
            .with_env("DJANGO_SECRET_KEY", "test")
            .with_env("FRONT_END_URL", "http://fake-front-end.net")
            .with_env("OKTA_CLIENT_ID", "client-id")
            .with_env("OKTA_CLIENT_SECRET", "client-secret")
            .with_env("OKTA_DOMAIN", "http://fake-okta.net")
            .with_env("OKTA_LOGIN_REDIRECT", "http://fake-front-end.net")
            .with_env("USE_HTTPS", False)
            .with_network(network)
            .start()
        )

        # Wait for Gunicorn to start
        logger.info("Waiting for Gunicorn to start")
        wait_for_logs(
            api_container,
            "Listening at: http://0.0.0.0:8000",
            timeout=30,
        )

        # Get the API URL
        host = api_container.get_container_host_ip()
        port = api_container.get_exposed_port(8000)
        url = f"http://{host}:{port}"
        logger.info("API available at %s", url)
        return url
    except Exception as e:
        logger.error("Error starting containerized system: %s", str(e))
        if api_container is not None:
            logs = api_container.get_logs().decode("utf-8")
            logger.error("Container logs:\n%s", logs)
        if network is not None:
            network.remove()
        if db_container is not None:
            logs = db_container.get_logs().decode("utf-8")
            logger.error("Container logs:\n%s", logs)
        raise Exception("Failed to start containerized system")
