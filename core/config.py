import os

### Variable settings. Adjust to your liking
# Default and max length of the chart
DEFAULT_CHART = 10
MAX_CHART = 100

# Print log messages additionally to console
PRINT_LOG = False
# Set the log level; "ERROR": Only errors; "INFO": Standard; "DEBUG": Verbose;
LOG_LEVEL = "INFO"
# Shorten URLs
MAX_URL_LENGTH = 60

### Static settings. Please don't alter
# Paths
ROOT_DIR = os.path.dirname(__file__).strip("core")

LOG_DIR = os.path.join(ROOT_DIR, "log")
DATA_DIR = os.path.join(ROOT_DIR, "data")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
HTML_TEMPLATE = "base.html"
HTML_OUTPUT = os.path.join(ROOT_DIR, "my_charts.html")

USER_PATH = os.environ["USERPROFILE"]
DB_PATH = os.path.join(USER_PATH, "AppData/Local/Google/Chrome/User Data/Default/History")
DB_PATH_LOCAL = os.path.join(DATA_DIR, "History.sqlite")

LOG_FILE = os.path.join(LOG_DIR, "history_charts.log")
