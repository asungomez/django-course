from typing import Any


def user_factory(overrides: dict[Any]) -> dict[Any]:
    user = {
        "email": "fake-user@email.net",
        "first_name": "Fake",
        "last_name": "User",
        "is_active": True,
        "is_superuser": False,
    }
    user.update(overrides)

    overrides_email = overrides.get("email")
    if overrides_email is not None:
        lower_email = overrides_email.lower()
        username = lower_email.split("@")[0]
        user["email"] = lower_email
        user["username"] = username

    return user
