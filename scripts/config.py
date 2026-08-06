# Local configuration file (Ignored by Git)
import os

USER = os.environ.get("CLUSTER_USER", "jisheng3")
BASE_URL = os.environ.get("CLUSTER_BASE_URL", "sp26-cs525-06")
DOMAIN = os.environ.get("CLUSTER_DOMAIN", ".cs.illinois.edu")
PASSWORD = os.environ.get("CLUSTER_PASSWORD")
