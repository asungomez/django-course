import logging
import pytest
from testcontainers.core.container import DockerContainer  # type: ignore
from testcontainers.core.waiting_utils import wait_for_logs  # type: ignore
import requests
import docker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
def api_url(request: pytest.FixtureRequest) -> str:
    """Spin up all necessary containers and return the API URL."""
    url = None
    api_container = None
    client = docker.from_env()
    image = None

    def cleanup() -> None:
        try:
            if api_container is not None:
                logger.info("Stopping container")
                api_container.stop()
                api_container.remove()
            if image is not None:
                logger.info("Removing image")
                client.images.remove(image.id, force=True)
        except Exception as e:
            logger.error("Error during cleanup: %s", str(e))

    request.addfinalizer(cleanup)

    try:
        # Build the image
        logger.info("Building image")
        image, _ = client.images.build(path=".")

        # Spin up the API container
        logger.info("Starting container")
        api_container = DockerContainer(image=image.id)
        api_container.with_exposed_ports(8000)
        api_container.start()

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
        logger.error("Error starting container: %s", str(e))
        if api_container is not None:
            logs = api_container.get_logs().decode("utf-8")
            logger.error("Container logs:\n%s", logs)
        raise Exception("Failed to start API container")


def test_404(api_url: str) -> None:
    """Test that unknown routes return 404."""
    path = "/unknown"
    url = f"{api_url}{path}"
    response = requests.get(url)
    assert response.status_code == 404
