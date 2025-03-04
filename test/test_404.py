import pytest
from testcontainers.core.image import DockerImage
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
import requests
import docker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module", autouse=True)
def api_url(request):
    """Spin up all necessary containers and return the API URL."""
    url = None
    api_container = None
    client = docker.from_env()
    image = None

    def cleanup():
        try:
            if api_container is not None:
                if api_container._container.status == "running":
                    logger.info("Stopping container")
                    api_container.stop()
                else:
                    logger.info(f"Container status: {api_container._container.status}")
            if image is not None:
                logger.info("Removing image")
                client.images.remove(image.id, force=True)
        except Exception as e:
            logger.error("Error during cleanup:", e)

    request.addfinalizer(cleanup)

    try:
        # Build the image
        image, _ = client.images.build(path=".", buildargs={"BUILD_ENV": "production"})

        # Spin up the API container
        api_container = DockerContainer(image=image.id)
        api_container.with_exposed_ports(8000)
        api_container.start()
        
        # Wait for Gunicorn to start
        wait_for_logs(api_container, "Listening at: http://0.0.0.0:8000", timeout=30)

        # Get the API URL
        host = api_container.get_container_host_ip()
        port = api_container.get_exposed_port(8000)
        url = f"http://{host}:{port}"
        return url
    except Exception as e:
        logger.error("Error starting container:", e)
        if api_container is not None:
            logs = api_container._container.logs().decode("utf-8")
            logger.error("Container logs")
            logger.error(logs)
        raise Exception("Failed to start API container")


def test_404(api_url):
    """Test that unknown routes return 404."""
    path = "/unknown"
    url = f"{api_url}{path}"
    response = requests.get(url)
    assert response.status_code == 404
