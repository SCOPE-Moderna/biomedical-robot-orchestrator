# Installing and Running Vestra

To run Vestra, you must run 4 pieces of software:

- **Node-RED**, an off-the-shelf flow based programming system
- The Python-based **Orchestrator** that runs flows, connects to instruments, and runs the gRPC server that interfaces between Node-RED and the Orchestrator
- A PostgreSQL-compatible database
- A reverse proxy, like Envoy, to allow gRPC-web requests to be sent from the browser and translated to the backend.
This is pre-configured in [/envoy.yaml](/envoy.yaml), but you could use a pre-existing Envoy proxy or another gRPC-compatible proxy to enable this - note that CORS headers must allow requests from your Node-RED host.

## Ports

| Port  | User         | Use                                                                 |
|-------|--------------|---------------------------------------------------------------------|
| 50051 | Orchestrator | gRPC Server                                                         |
| 1880  | Node-RED     | Default port - you can change this in Node-RED's configuration file |
| 8080  | Envoy        | gRPC Web requests that Envoy will proxy to the Orchestrator         |

## Installing Vestra

### Configuring Vestra's Database

Vestra needs access to a PostgreSQL-compatible database with pre-created tables.

To make this easier, we provide [an SQL file](../backend/tables.sql) with the SQL commands needed to create the tables that Vestra needs.

Once you create the tables, pre-fill them with some data, like your instruments.

### Using Docker

Depending on the devices you plan to use Vestra with, you may have trouble running Vestra in Docker.
In order to function, Vestra must connect to a variety of devices, and it contains the ability to communicate with other processes via IPC (Inter-Process Communication).

If you are just using devices that connect over LAN, then Vestra may work inside Docker.

To run Vestra inside Docker, build a container from `/backend/Dockerfile` (this will take a long time due to a large library dependency, `ur_rtde` for controlling Universal Robotics robots, which depends on Boost and CMake), then run the container forwarding port 50051.

### Locally

Running Vestra locally is simple.
However, one of Vestra's dependencies, the Python package `ur_rtde`, used to control Universal Robotics robots, requires a dependency called Boost.
The current version of `ur_rtde` installed requires Boost 1.86.0. To compile it, you will need C/C++ build tools on your machine.

#### Installing Boost on Windows

1. Download Visual Studio, and, when installing, specify the C/C++ apps option.
   - Note that we do not need to use Visual Studio - we just need the developer command prompt, which includes C/C++ build tools.
2. Download CMake >= 3 < 4, and install
3. Download Boost 1.86.0 from [here](https://www.boost.org/users/history/version_1_86_0.html)
4. Extract the file on your machine
5. Move the `boost_1_86_0` folder to `C:\Program Files\` (may require Administrator approval)
6. Open a Developer Command prompt installed by Visual Studio (called `Developer Command Prompt for VS 2022`)
7. Run the following commands in the Developer Command Prompt:

```shell
cd "C:\Program Files\boost_1_86_0"
.\bootstrap
.\b2 --prefix=. --with-system --with-thread --with-program_options
```

This will take a few minutes. Once it completes, Boost is installed.

#### Installing Boost for Linux

Different distributions of Linux may have different steps for install.
Ubuntu users can just `sudo apt-get install libboost-all-dev=1.86.0`.

To see example commands for installing Boost on Linux (debian), refer to the [Dockerfile](/backend/Dockerfile) - it automatically installs Boost.

#### Installing Python Dependencies

The Orchestrator requires Python 3.13 or newer - ensure that Python is installed on your machine before continuing.

We recommend using a virtual environment or something like Conda for the Orchestrator. To create a virtual environment, open a terminal in the base directory of this repository, then run:

```shell
python -m venv venv
# Linux
source venv/bin/activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

pip -r backend/requirements.txt
```

`pip` will now install all the required packages for the Orchestrator.

### Running the Orchestrator

The Orchestrator requires two environment variables to run:

- `DATABASE_URL`: PostgreSQL database connection string to your database, like `postgres://user:pass@192.168.0.250:5432/vestradb`
- `NODE_RED_DIR`: Path to the Node-RED configuration folder, so it can read your flows from Node-RED. By default, this is `~/.node-red`.

Now, to run the orchestrator, open a terminal in the base directory of this repository and run `make backend` or `python -m backend.main`.