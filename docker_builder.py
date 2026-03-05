import requests, sys, subprocess

def get_latest_version_gemfury(gemfury_url, api_token=None):
    try:
        headers = {}
        if api_token:  # If your Gemfury repo requires authentication
            headers["Authorization"] = f"Bearer {api_token}"

        url = f"{gemfury_url}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return data[0]["version"]  # The latest version
    except Exception as e:
        print(f"Error fetching package version from Gemfury: {e}")
        return None

def docker_login(username, token, registry="https://index.docker.io/v1/"):
    try:
        # Run the docker login command
        result = subprocess.run(
            ["docker", "login", "-u", username, "--password-stdin", registry],
            input=token,  # Pass the token via stdin
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            print(f"Successfully logged into Docker registry: {registry}")
            return True
        else:
            print(f"Error logging into Docker registry: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error during Docker login: {e}")
        return False

def build_and_push_docker_image(image_name, sc_version, py_version, dockerfile_path="."):
    try:
        # Build the Docker image
        result = subprocess.run(
            ["docker", "buildx" ,"build",
             "--platform", "linux/amd64",
             "--no-cache",
             "-t", image_name, "-t", "ghcr.io/disys-lab/gustavo:latest",
             dockerfile_path,
             "--build-arg", f"gustavo_version={sc_version}", "--build-arg", f"py_version={py_version}",
             "--push"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            print(f"Successfully built Docker image: {image_name}")
            return True
        else:
            print(f"Error building Docker image: {result.stderr}")
    except Exception as e:
        print(f"Error: {e}")
    return False

def tag_docker_image(image_name1, image_name2):
    try:
        # Tag the image as `latest`
        result = subprocess.run(
            ["docker", "tag", image_name1, image_name2],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            print(f"Successfully tagged image as {image_name2}")
            return True
        else:
            print(f"Error tagging image: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def push_docker_image(image_name):
    try:
        # Push the Docker image to the registry
        result = subprocess.run(
            ["docker", "push", image_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            print(f"Successfully pushed Docker image: {image_name}")
        else:
            print(f"Error pushing Docker image: {result.stderr}")
    except Exception as e:
        print(f"Error: {e}")

docker_username = str(sys.argv[1])
fury_api_token = str(sys.argv[2])
docker_token=str(sys.argv[3])


package_name = "gustavo"
gemfury_url = "https://api.fury.io/1/packages/gustavo/versions"  # Adjust as needed
latest_gustavo_version = get_latest_version_gemfury(gemfury_url, fury_api_token)
docker_registry = "https://ghcr.io"
py_version="python3.11"

if latest_gustavo_version:
    print(f"Latest version of {package_name}: {latest_gustavo_version}")
    docker_image_name = f"ghcr.io/disys-lab/gustavo:{latest_gustavo_version}"
    if docker_login(docker_username, docker_token, docker_registry):
        print("Docker login success!")
        if not build_and_push_docker_image(docker_image_name,latest_gustavo_version,py_version,"."):
            print("Docker image build failure")
            raise Exception("DockerImageBuildFailure:Could not build docker image")
    else:
        print("Could not login to docker")
        raise Exception("DockerLoginFailure:Could not login to docker")


else:
    print(f"Could not fetch the latest version of {package_name}.")
    raise Exception(f"FuryVersionRetreivalError:Could not fetch the latest version of {package_name}.")
