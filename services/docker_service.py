import docker
# from utils.helpers import find_available_port
from utils.nginx_helper import update_nginx_config, restart_nginx
import os
import re
from docker.types import TaskTemplate, ContainerSpec, Mount, RestartPolicy, Placement
from config import mapping_path, nginx_conf_path, docker_client

if mapping_path[-1] == "/":
    mapping_path = mapping_path[:-1]

def create_container(username: str):
    """
    Create a new service in Docker Swarm with a unique username as the service name.
    """
    try:
        # Ensure the folder for the user exists in mapping_path
        container_mount_path = os.path.join(mapping_path, username)
        user_folder_path = os.path.join("/code-spaces-mapping", username)
        print(f"User folder path: {user_folder_path}")
        if not os.path.exists(user_folder_path):
            print(f"Creating user folder: {user_folder_path}")
            os.makedirs(user_folder_path)

        # Check if a service with the same name already exists
        try:
            existing_service = docker_client.services.get(f"{username}-code-server")
            print(existing_service)
            if existing_service:
                print("Comming to if")
                raise ValueError(f"A service with the name '{username}' already exists.")
        except docker.errors.NotFound:
            pass  # No existing service with this name

        # Create the service
        container_spec = ContainerSpec(
            image="taasheeadmin/code-server",
            user="root",
            mounts=[Mount(type="bind", source=container_mount_path, target="/home/coder")],
            tty=True,
            command=["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none"]
        )

        # Define task template with placement
        task_template = TaskTemplate(
            container_spec=container_spec,
            restart_policy=RestartPolicy(condition="any"),
            placement=Placement(constraints=["node.role == worker"])
        )

        # Create the service using low-level API
        service = docker_client.api.create_service(
            task_template=task_template,
            name=f"{username}-code-server",
            networks=["code-spaces"]
        )

        # Update Nginx config
        update_nginx_config(username)

        # Restart Nginx to apply changes
        restart_nginx()

        # Return service details
        return {
            "message": "Service created successfully!",
            "service_id": service["ID"],
            "service_name": f"{username}-code-server",
            "access_url": f"/{username}/",
            "password": f"coder-{username}"
        }

    except Exception as e:
        raise Exception(f"Error creating service: {str(e)}")

def get_container(service_name: str):
    """
    Retrieve details of a service by its name.
    """
    try:
        service = docker_client.services.get(service_name)
        return {
            "service_id": service.id,
            "service_name": service_name,
            "status": service.attrs['UpdateStatus']['State'] if 'UpdateStatus' in service.attrs else "active",
        }
    except docker.errors.NotFound:
        return None
    except Exception as e:
        raise Exception(f"Error retrieving service: {str(e)}")

def remove_container(service_name: str):
    """
    Remove a service by its name.
    Also removes the corresponding location block from nginx.conf and restarts Nginx.
    """
    try:
        # Remove the service
        service = docker_client.services.get(service_name)
        service.remove()
        
        # Remove location from nginx.conf
        location_block_pattern = rf"\n\s*location /{service_name.replace('-code-server', '')}/ \{{.*?\n\s*\}}"
        
        with open(nginx_conf_path, "r") as file:
            nginx_conf = file.read()

        updated_conf = re.sub(location_block_pattern, "", nginx_conf, flags=re.DOTALL)

        with open(nginx_conf_path, "w") as file:
            file.write(updated_conf)

        # Restart Nginx to apply changes
        os.system("docker restart nginx")

        return {"message": f"Service '{service_name}' removed successfully and Nginx updated!"}

    except docker.errors.NotFound:
        return {"error": f"Service '{service_name}' not found."}
    except Exception as e:
        raise Exception(f"Error removing service: {str(e)}")

def list_containers():
    """
    List all services in the Docker Swarm.
    """
    try:
        services = docker_client.services.list()  # List all services
        service_list = []

        for s in services:
            if "code-server" not in s.name:
                continue
            
            # Append service details to the list
            service_list.append({
                "id": s.id,
                "name": s.name,
                "status": s.attrs['UpdateStatus']['State'] if 'UpdateStatus' in s.attrs else "active",
            })
        
        return service_list

    except Exception as e:
        raise Exception(f"Error listing services: {str(e)}")
