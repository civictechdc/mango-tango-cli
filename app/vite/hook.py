from os import getcwd, listdir, path
from subprocess import CalledProcessError, run


def init_dashboard_build():
    templates_path = path.join(getcwd(), "web_templates")
    build_path = path.join(templates_path, "build")
    bundled_path = path.join(build_path, "bundled")

    if path.exists(path.join(build_path, "manifest.json")) and path.isdir(bundled_path):
        if len(listdir(bundled_path)) > 0:
            return None

    try:
        run(["npm", "--version"], check=True, capture_output=True)

    except CalledProcessError:
        raise RuntimeError("Node.JS must be installed to build the dashboard.")

    try:
        run(
            ["npm", "run", "build"], check=True, capture_output=True, cwd=templates_path
        )

    except CalledProcessError:
        raise RuntimeError(
            """
            The dashboard was not built successfully. Please review the logs and try again after the errors have been resolved...\n
            If the issue still persists please open an issue at: https://https://github.com/civictechdc/mango-tango-cli/issues/new\n
            to receive support on this error.
            """
        )
