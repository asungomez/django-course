# Example DJango application

This is a pet project I'm using to learn some Django concepts.

## Running the application in your host machine

The application can run either on a Docker container or in your host machine. Host machine allows some perks such as VSCode debugging. Docker container is more portable and can be used in a CI/CD pipeline, but for local development adds more overhead.

### Installing Python and creating a virtual environment

This application uses Python 3.13. It is recommended to use a virtual environment to run this application.

You can install python3.13 from the official website: https://www.python.org/downloads/ or using pyenv:

```bash
pyenv install 3.13.1
```

To create a new virtual environment, you can use the following command:

```bash
python3.13 -m venv venv
```

Enable the virtual environment:

```bash
source venv/bin/activate
```

For a freshly created virtual environment, it is recommended to upgrade pip:

```bash
pip install --upgrade pip
```

### Running the application

The dependencies for running the application can be installed using the following command:

```bash
pip install -r requirements.txt
```

You need a DB to run the application. You can create a DB container by running:

```bash
docker compose up db
```

The app needs an .env file like the following:

```env
DEBUG=True
DB_HOST=localhost
DB_NAME=django_course
DB_USER=django_course
DB_PASSWORD=django_course
DJANGO_SECRET_KEY="django-insecure-trkc%c14mv8b%95!spl5n&sg51f7wsyvasx%7ddl$07-f-iynh"
```

Then you can run a dev server using:

```bash
cd src
python manage.py runserver 0.0.0.0:8000
```

### Validating the code

The dependencies for validations can be installed using:

```bash
pip install -r requirements.dev.txt
```

To run the linter, you can use the following command:

```bash
flake8
```

And to run the static type checker, you can use the following command:

```bash
mypy . --strict
```

### Installing test dependencies

If you want to run the tests, you can install the test dependencies using the following command:

```bash
pip install -r requirements.test.txt
```

### Running the tests

To run the tests, you can use the following command:

```bash
pytest
```

## Running the application using Docker

The benefits of using Docker is that the application will run in the exact same environment it would when deployed, making it easier to debug issues. It also doesn't require you to install Python or create a virtual environment. It does not integrate easily with VSCode debugging, though.

### Importing self-signed certificates

When working on a company computer, there are self-signed certificates that can make the Docker image build to fail. To prevent this, follow the steps below:

- Enter JLL Self-Service
- Execute the Netskope Developer Tool Configuration
- Create a directory at the root of the project called `.certs`
- Copy the certificate file netskope-cert-bundle.pem into `.certs/netskope-cert-bundle.pem`

### Spinning up the container

To spin up the container, you can use the following command:

```bash
docker compose up app
```
