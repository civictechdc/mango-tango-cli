from pathlib import Path


def create_vue_dist_path(file_path: str, js_path: str) -> str:
    return (Path(file_path).parent / js_path).resolve().as_posix()
