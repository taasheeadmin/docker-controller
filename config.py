import os

import docker
docker_client = docker.from_env()

from dotenv import load_dotenv
load_dotenv()

mapping_path = os.getenv("MAPPING_PATH", "~/code-spaces-mapping")
nginx_conf_path = os.getenv("NGINX_CONF_PATH", "/nginx.conf")
