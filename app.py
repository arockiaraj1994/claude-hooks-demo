"""A tiny app, so Claude has something to look at during the demo."""


def greet(name: str) -> str:
    return f"Vanakkam, {name}!"


if __name__ == "__main__":
    print(greet("Chennaipy"))
