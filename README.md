# ops_tracking_toolkit
Operations Tracking Toolkit to monitor down nodes and cables in clusters

## Requirements:
* A user be setup on the Extraview server, usually in the resolver role.
  * Sockets connectivity to Extraview server API (usually in /evj/ExtraView/ev_api.action on the webserver).
* Python3
* [pyextraview](https://github.com/NCAR/pyextraview) (currently required)
* [PIP](https://pypi.python.org/pypi/pip) or [easy_install](https://pypi.python.org/pypi/setuptools)
* make
* [clush](https://github.com/cea-hpc/clustershell)
** Clush must be fully configured to run on cluster.

## Limitations:
This project is currently restricted to sites with PBSPro, SGI ICE, and Mellanox Infiniband. Support is planned for generic Linux clusters and Slurm.

## Tools Provided:
* Bad Cable List
  * Tool to track, control and repair Infiniband cables.
* Bad Node List
  * Tool to track, control and repair PBSPro scheduled compute nodes.
  
## Setup:
1. Clone the repo
  ```bash
  user@host# git clone https://github.com/NCAR/ops_tracking_toolkit.git
  ```
2. Call make to install 
  ```bash
  user@host# make
  ```

## Configuration

TODO
