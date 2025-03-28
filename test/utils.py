import requests
import psycopg2
from typing import Any, Optional, Sequence, Mapping


class Helper:
    """
    Helper class with utilities for tests: requests to the API, creating
    mocks, etc.
    """

    api_url: str = None
    mockserver_url: str = None
    db_connection: psycopg2.extensions.connection = None

    def __init__(
            self,
            api_url: str,
            mockserver_url: str,
            db_port: int,
            ):
        """
        Initialize the Helper class.

        :param api_url: The URL of the API
        :param mockserver_url: The URL of the MockServer
        :param db_port: The port of the database
        """
        self.api_url = api_url
        self.mockserver_url = mockserver_url
        self.db_connection = psycopg2.connect(
            database="test",
            user="test",
            host="localhost",
            password="test",
            port=db_port
        )

    def clean_up_db(self) -> None:
        """
        Clean up the database.
        This is used to remove all data from the db.
        """
        tables_to_clean = [
            "core_user"
        ]
        for table in tables_to_clean:
            query = f"DELETE FROM {table}"
            self.query_db(query)

    def clean_up_mocks(self) -> None:
        """
        Clean up the mocks in the MockServer.
        """
        url = f"{self.mockserver_url}/mockserver/reset"
        requests.put(url)

    def find_user_by_email(self, email: str) -> Optional[dict]:
        """
        Find a user by email.

        :param email: The email of the user to find
        :return: The user object
        """
        lower_email = email.lower()
        query = "SELECT * FROM core_user WHERE email = %s"
        params = (lower_email,)
        result = self.query_db(query, params)
        if len(result) == 0:
            return None
        return result[0]

    def get_request(self, path: str) -> requests.Response:
        """
        Make a request to the API.

        :param path: The path to request

        :return: The response object
        """
        url = f"{self.api_url}{path}"
        response = requests.get(url, allow_redirects=False)
        return response

    def insert_user(self, user: dict[Any]) -> None:
        """
        Insert a user into the database.

        :param user: The user object to insert
        """
        cursor = self.db_connection.cursor()
        query = """
            INSERT INTO core_user (
                email,
                first_name,
                last_name,
                username,
                is_active,
                is_superuser,
                password,
                last_login,
                date_joined
            )
            VALUES (
                %(email)s,
                %(first_name)s,
                %(last_name)s,
                %(username)s,
                %(is_active)s,
                %(is_superuser)s,
                'password',
                NOW(),
                NOW()
            )
        """
        cursor.execute(query, user)
        self.db_connection.commit()
        cursor.close()

    def mock_okta_token_response(
            self,
            response_body: any,
            response_status: int = 200
            ) -> None:
        """
        Mock Okta's token endpoint.

        :param response_body: The response body to return
        :param response_status: The response status code to return
        """

        self.mock_response(
            request_path="/okta/oauth2/default/v1/token",
            request_method="POST",
            response_body=response_body,
            response_status=response_status,
        )

    def mock_response(
            self,
            request_path: str,
            request_method: str = "GET",
            response_body: any = {},
            response_status: int = 200,
            ) -> None:
        """
        Mock a response from the Mockserver

        :param request_path: The path to match
        :param request_method: The method to match
        :param response_body: The response body to return
        :param response_status: The response status code
        """

        url = f"{self.mockserver_url}/mockserver/expectation"
        mock = {
            "httpRequest": {
                "path": request_path,
                "method": request_method,
            },
            "httpResponse": {
                "body": response_body,
                "statusCode": response_status,
            },
        }

        # Send a PUT request to the MockServer to create the expectation
        requests.put(
            url,
            json=mock,
            headers={"Content-Type": "application/json"},
        )

    def query_db(
            self,
            query: str,
            params: Sequence[Any] | Mapping[str, Any] | None = None
            ) -> Optional[list]:
        """
        Query the database.

        :param query: The SQL query to execute
        :param params: The parameters to pass to the query

        :return: The result of the query
        """
        cursor = self.db_connection.cursor()
        cursor.execute(query, params)
        result = None
        try:
            result = cursor.fetchall()
        except psycopg2.ProgrammingError:
            pass
        cursor.close()
        return result
