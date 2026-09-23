"""PromptRelay package entrypoint."""

def main() -> None:
    from backend.app.main import main as run_server
    run_server()
