import docker.models
import docker.models.networks
import pytest
from testcontainers.core.container import DockerContainer  # type: ignore
from testcontainers.core.network import Network  # type: ignore
from testcontainers.core.waiting_utils import wait_for_logs  # type: ignore
import docker
import os
import logging
from .utils import Helper
from . import static

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def tests_helper(request: pytest.FixtureRequest) -> Helper:
    """
    Spin up all necessary containers and return a Helper object to use
    in tests.
    This fixture is automatically used in all tests.
    """
    url = None
    api_container: DockerContainer = None
    client = docker.from_env()
    image = None
    network: Network = None
    db_container: DockerContainer = None
    mockserver_container: DockerContainer = None

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
            if mockserver_container is not None:
                logger.info("Stopping mockserver container")
                mockserver_container.stop()
                mockserver_container._container.remove(force=True)
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

        # Create a MockServer container inside the network
        logger.info("Starting MockServer container")
        mockserver_container = (
            DockerContainer(image="mockserver/mockserver")
            .with_exposed_ports(1080)
            .with_network(network)
            .with_network_aliases(("mockserver"))
            .start()
        )

        # Build the API image
        build_env = os.environ.get("BUILD_ENV", "development")
        logger.info("Building image")
        image, _ = client.images.build(
            path=".",
            buildargs={"BUILD_ENV": build_env}
            )

        # Spin up the API container
        logger.info("Starting container")
        mockserver_url = "http://mockserver:1080"
        api_container = (
            DockerContainer(image=image.id)
            .with_exposed_ports(8000)
            .with_env("DB_HOST", "db")
            .with_env("DB_NAME", "test")
            .with_env("DB_PASSWORD", "test")
            .with_env("DB_PORT", "5432")
            .with_env("DB_USER", "test")
            .with_env("DEBUG", "True")
            .with_env("DJANGO_SECRET_KEY", "test")
            .with_env("FRONT_END_URL", static.FRONT_END_URL)
            .with_env("MOCK_AUTH", "True")
            .with_env("OKTA_CLIENT_ID", "client-id")
            .with_env("OKTA_CLIENT_SECRET", "client-secret")
            .with_env("OKTA_DOMAIN", f"{mockserver_url}/okta")
            .with_env("OKTA_LOGIN_REDIRECT", static.FRONT_END_URL)
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

        # Run the DB migrations
        logger.info("Running migrations")
        exit_code, output = api_container.exec(
            "python /app/manage.py migrate",
        )
        if exit_code != 0:
            logger.error(f"Migration failed: {output.decode()}")
            raise Exception("Failed to apply migrations")
        else:
            logger.info("Migrations applied successfully")

        # Get the external API URL
        api_host = api_container.get_container_host_ip()
        api_port = api_container.get_exposed_port(8000)
        api_url = f"http://{api_host}:{api_port}"
        logger.info("API available at %s", url)

        # Get the external MockServer URL
        mockserver_host = mockserver_container.get_container_host_ip()
        mockserver_port = mockserver_container.get_exposed_port(1080)
        mockserver_external_url = f"http://{mockserver_host}:{mockserver_port}"

        # Get the DB port
        db_port = db_container.get_exposed_port(5432)

        helper = Helper(
            api_url=api_url,
            mockserver_url=mockserver_external_url,
            db_port=db_port,
            )
        return helper
    except Exception as e:
        logger.error("Error starting containerized system: %s", str(e))
        if db_container is not None:
            logs = db_container.get_logs()[0].decode("utf-8")
            logger.error("DB Container logs:\n%s", logs)
        if mockserver_container is not None:
            logs = mockserver_container.get_logs()[0].decode("utf-8")
            logger.error("Mockserver Container logs:\n%s", logs)
        if api_container is not None:
            logs = api_container.get_logs()[0].decode("utf-8")
            logger.error("API Container logs:\n%s", logs)
        raise Exception("Failed to start containerized system")


@pytest.fixture(autouse=True)
def tear_down(request: pytest.FixtureRequest, tests_helper: Helper) -> None:
    """
    Tear down after each test.
    This is used to clean up the database and remove the mocks
    after each test.
    """
    def cleanup() -> None:
        tests_helper.clean_up_mocks()
        tests_helper.clean_up_db()
        pass

    request.addfinalizer(cleanup)
