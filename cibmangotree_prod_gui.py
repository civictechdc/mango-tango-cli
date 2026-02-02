from threading import Thread
from fastapi import FastAPI
from uvicorn import run
from webview import create_window, start
from prod_gui.pages import index


def main() -> None:
    app = FastAPI()

    app.include_router(index.router)

    def start_server() -> None:
        run(app, host="localhost", port=8080)

    server_thread = Thread(target=start_server, daemon=True)

    server_thread.start()
    create_window("Hello world!", "http://localhost:8080")
    start()


if __name__ == "__main__":
    main()
