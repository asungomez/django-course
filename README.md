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

### Installing dependencies

To install the dependencies, you can use the following command:

```bash
pip install -r requirements.txt
```

### Installing dev dependencies

If you want to use dev dependencies such as flake8 for linting, you can use the following command:

```bash
pip install -r requirements.dev.txt
```

### Running the application

Run the application with the following command:

```bash
cd src
python manage.py runserver 0.0.0.0:8000
```


### Running the linter

To run the linter, you can use the following command:

```bash
cd src
flake8
```

## Running the application using Docker

The benefits of using Docker is that the application will run in the exact same environment it would when deployed, making it easier to debug issues. It also doesn't require you to install Python or create a virtual environment. It does not integrate easily with VSCode debugging, though.

### Spinning up the container

To spin up the container, you can use the following command:

```bash
docker compose up app
```

### Running the linter inside the container

You can run the linter using:

```bash
docker compose run --rm app sh -c "flake8"
```