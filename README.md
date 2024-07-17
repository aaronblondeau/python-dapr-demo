# python-dapr-demo

Demo app that uses [Dapr](https://dapr.io/) with [FastAPI](https://fastapi.tiangolo.com/).

This is for a blog post : [https://aaronblondeau.com/posts/july_2024/python_dapr/](https://aaronblondeau.com/posts/july_2024/python_dapr/)

## Getting Started

First create a virtual environment, install poetry, and use poetry to install dependencies.

Mac/Linux

```sh
python3 -m venv venv
source venv/bin/activate
pip install poetry
poetry install
```

Windows: 

```powershell
python3 -m venv venv
.\venv\Scripts\activate.ps1
pip install poetry
poetry install
```

Next, start dapr by following instructions here : https://docs.dapr.io/getting-started/install-dapr-cli/

Make sure dapr is running

```
dapr init
```

Then start a dapr app

```
dapr run --app-id air_display --app-port 30212 --dapr-http-port 3500 --dapr-grpc-port 50001 --resources-path ./resources
```

**Note that --app-port must match port of python service!**

Once the dapr app is running launch fastapi

```
export DAPR_GRPC_ENDPOINT="localhost:50001?tls=false"
export DAPR_HTTP_PORT=3500
export DAPR_RUNTIME_HOST=localhost
fastapi dev server.py --port 30212
```

View the UI : http://localhost:30212/

Navigate here to use the API : http://localhost:30212/docs

When done with the application and dapr, run this to cleanup all containers and shutdown dapr:

```
dapr uninstall --all
```

## Redis insight

You can use redis insight to view data in the datastore.  Launch it with this:

```
docker run --rm -d --name redisinsight -p 5540:5540 redis/redisinsight:latest
```

Then navigate to:

http://localhost:5540/

Use port 6379

On linux use host = 172.17.0.1

On win/mac use host = docker.host.internal
