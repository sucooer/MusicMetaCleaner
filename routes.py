from route_modules.base import bp, temp_files

# Import route modules for blueprint registration side effects.
from route_modules import settings_routes  # noqa: F401,E402
from route_modules import upload_routes  # noqa: F401,E402
from route_modules import path_routes  # noqa: F401,E402
from route_modules import file_routes  # noqa: F401,E402
