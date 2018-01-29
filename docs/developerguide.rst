.. _developerguide:

Developer guide
===============

Deploying specific component versions
-------------------------------------

If you want to try different versions of REANA components, you can modify your
``reana-cluster.yaml`` configuration file; see :ref:`configure`.

You can check available released versions on `REANA DockerHub
<https://hub.docker.com/u/reanahub/>`_.

Deploying latest ``master`` branch versions
-------------------------------------------

If you want to use latest ``master`` branch of REANA components and have the
code directly editable within pods, you can use ``reana-cluster-dev.yaml``.

1. Clone the REANA component under ``$HOME/reana/sources`` directory on your laptop.

2. Mount your component source code in minikube under `/code` directory:

.. code-block:: console

   $ ls -d $HOME/reana/sources
   reana-client
   reana-cluster
   reana-job-controller
   reana-message-broker
   reana-server
   reana-workflow-controller
   reana-workflow-engine-cwl
   reana-workflow-engine-yadage
   reana-workflow-monitor
   $ minikube mount $HOME/reana/sources:/code

3. Edit sources on your laptop under ``$HOME/reana/sources/reana-<component>/...`` as usual:

.. code-block:: console

   $ vim $HOME/reana/sources/reana-job-controller/reana_job_controller/app.py

4. Delete your pod and see a new pod being deployed with your changes:

.. code-block:: console

   $ kubectl get pods | grep job-controller
   $ kubectl delete pod job-controller-2461563162-r4hgg
   $ sleep 10 # wait some time...
   $ kubectl get pods | grep job-controller
   $ kubectl exec -i -t job-controller-2461563162-h9ptw /bin/bash

Using Minikube running on a remote host
---------------------------------------

The purpose of this documentation is to help set up development environment,
where REANA components are deployed to a Kubernetes created with Minikube on
a remote host, e.g. virtual private server, or other remote computer you can
connect to with SSH and HTTP(S).

This setup enables to offload resource and feature requirements imposed by
Kubernetes and Minikube, such as computing resources (memory, disk space, CPU)
required by Kubernetes and virtualization support required by Minikube, away
from your laptop.

On the remote host, you first setup Minikube and possibly Kubectl the same way
as you would do on local installation. Then you create Kubernetes with Minikube
and expose Kubernetes API server and Docker daemon through SSH port forwards
so you can access them with Docker client, Kubectl and REANA-Cluster
running on laptop.

This documentation expects that Minikube virtual machine is created as a
Virtualbox virtual machine (not as e.g. kvm virtual machine). If you want to
use other virtualization technologies supported by Minikube you have to figure
out how to setup port forwarding from remote host to the virtual machine using
that technology.

Note that you can also create a non-virtualized deployment of Kubernetes with
Minikube for systems that don't support virtualization, aka
``minikube --vm-driver=none`` deployments, where Minikube doesn't create a
separate virtual machine for Kubernetes.
Steps needed to setup REANA development environment in non-virtualized and
virtualized Kubernetes differ and this documentation takes that into account.

Expose K8S API on the remote host running Minikube
++++++++++++++++++++++++++++++++++++++++++++++++++

After running ``minikube start`` on the remote host.

**AT REMOTE HOST:**

1. Forward port 8443 to VM created by Minikube.

   If Minikube has been started with ``--vm-driver=none`` skip this step.

   Otherwise forward port 8443 to VM created by Minikube:

.. code-block:: console

   $ vboxmanage controlvm "minikube" natpf1 "minikube-https,tcp,,8443,,8443"

2. Get service-account-token to use for authentication instead of certificate files.

   Run following command and copy output for later use.

.. code-block:: console

   $ kubectl get secret --namespace=kube-system -o jsonpath={.items[0].data.token} | base64 -d


**AT LOCAL MACHINE:**

3. Make an SSH port forward from localhost:8443 to remote host running Minikube

   Run following command, where ``$FQDN`` is URL to and ``$USER`` is your username
   at remote host running Minikube.

.. code-block:: console

   $ ssh -L 8443:localhost:8443 $USER@$FQDM


4. Configure ``reana-cluster`` to connect to K8S API on the remote host running Minikube

   For reana-cluster to be able to access exposed K8S API on remote host you
   need to provide reana-cluster with a configuration file that describes where
   reana-cluster should connect and how to authenticate to the API.
   Straigthforward way is to create two new files, ``reana-cluster-dev.yaml`` file
   which gets Kubernetes (K8S API url and authentication details) configuration
   from ``development-kubeconfig.yaml`` file. Below is copy-pasteable contents of
   the two files. Create them on your working directory.

.. code-block:: yaml

   #reana-cluster-dev.yaml
   cluster:
     type: "kubernetes"
     config: "./development-kubeconfig.yaml"
     config_context: "minikube"
     version: "v1.6.4"
     url: "https://localhost:8443"

   components:
     reana-workflow-controller:
       type: "docker"
       image: "reanahub/reana-workflow-controller:0.1.0"
       mountpoints:
         - type: hostPath
           name: reana-workflow-controller-code
           path: "/code/reana-workflow-controller:/code"
       environment:
         - SHARED_VOLUME_PATH: "/reana"
         - ORGANIZATIONS: "default,alice,atlas,cms,lhcb"
         - WDB_SOCKET_SERVER: "wdb"
         - WDB_NO_BROWSER_AUTO_OPEN: "True"
         - FLASK_DEBUG: "1"

     reana-job-controller:
       type: "docker"
       image: "reanahub/reana-job-controller:0.1.0"
       mountpoints:
         - type: hostPath
           name: reana-job-controller-code
           path: "/code/reana-job-controller:/code"
       environment:
         - REANA_STORAGE_BACKEND: "LOCAL"
         - WDB_SOCKET_SERVER: "wdb"
         - WDB_NO_BROWSER_AUTO_OPEN: "True"
         - FLASK_DEBUG:  "1"

     reana-server:
       type: "docker"
       image: "reanahub/reana-server:0.1.0"
       mountpoints:
         - type: hostPath
           name: reana-server-code
           path: "/code/reana-server:/code"
       environment:
         - WDB_SOCKET_SERVER: "wdb"
         - WDB_NO_BROWSER_AUTO_OPEN: "True"
         - FLASK_DEBUG: "1"

     reana-message-broker:
       type: "docker"
       image: "reanahub/reana-message-broker:0.1.0"
       mountpoints:
         - type: hostPath
           name: reana-message-broker-code
           path: "/code/reana-message-broker:/code"
       environment:
         - WDB_SOCKET_SERVER: "wdb"
         - WDB_NO_BROWSER_AUTO_OPEN: "True"

     reana-workflow-monitor:
       type: "docker"
       image: "reanahub/reana-workflow-monitor:0.1.0"
       mountpoints:
         - type: hostPath
           name: reana-workflow-monitor-code
           path: "/code/reana-workflow-monitor:/code"
       environment:
         - ZMQ_PROXY_CONNECT: tcp://zeromq-msg-proxy.default.svc.cluster.local:8667
         - WDB_SOCKET_SERVER: "wdb"
         - WDB_NO_BROWSER_AUTO_OPEN: "True"
         - FLASK_DEBUG: "1"

     reana-workflow-engine-yadage:
       type: "docker"
       image: "reanahub/reana-workflow-engine-yadage:0.1.0"
       mountpoints:
         - type: hostPath
           name: reana-workflow-engine-yadage-code
           path: "/code/reana-workflow-engine-yadage:/code"
       environment:
         - ZMQ_PROXY_CONNECT: "tcp://zeromq-msg-proxy.default.svc.cluster.local:8666"
         - WDB_SOCKET_SERVER: "wdb"
         - WDB_NO_BROWSER_AUTO_OPEN: "True"

.. code-block:: yaml

   #development-kubeconfig.yaml
   apiVersion: v1
   clusters:
   - cluster:
       # Since minikube generates self-signed certificate that doesn't include
       # hostname `localhost` TLS hostname verification has to be skipped.
       insecure-skip-tls-verify: true
       server: https://localhost:8443
     name: minikube
   contexts:
   - context:
       cluster: minikube
       user: minikube
     name: minikube
   current-context: minikube
   kind: Config
   preferences: {}
   users:
   - name: minikube
     user:
       as-user-extra: {}
       token: $TOKEN

Note that you must change the value of ``$TOKEN`` to the token you acquired in step 2.

6. Instruct ``reana-cluster`` to use your own reana-cluster.yaml by using ``-f`` flag:

.. code-block:: console

   $ reana-cluster -f $(pwd)/reana-cluster-dev.yaml verify backend

7. Configure ``kubectl`` to connect to K8S API on the remote host running Minikube

Kubectl supports defining configuration by supplying path to kubeconfig
configuration file by ``$KUBECONFIG`` environment variable.
(https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/#set-the-kubeconfig-environment-variable)

.. code-block:: console

   $ export KUBECONFIG=$(pwd)/development-kubeconfig.yaml
   $ kubectl cluster-info
   > Kubernetes master is running at https://localhost:8443

You should now be able interact with Kubernetes API of your Minikube VM on
remote host with both ``reana-cluster`` and ``kubectl``.

Expose Docker daemon on the remote host running Minikube
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

**AT REMOTE HOST:**

Run alpine/socat docker container that maps your docker.sock to tcp port 2375.
Note that docker.sock is exposed as plain HTTP without authentication, so
don't expose it outside 127.0.0.1 of remote host running Minikube.
SSH port forwarding is used to provide a secure connection to port.

1. Share docker.sock by HTTP at port 2375

   If Minikube has been started with ``--vm-driver=none`` run following command.

.. code-block:: console

   $ docker run -d --restart=always \
       -p 127.0.0.1:2375:2375 \
       -v /var/run/docker.sock:/var/run/docker.sock \
       alpine/socat \
       TCP4-LISTEN:2375,fork,reuseaddr UNIX-CONNECT:/var/run/docker.sock

\
   Otherwise run

.. code-block:: console

   $ minikube ssh 'docker run -d --restart=always -p 2375:2375 \
       -v /var/run/docker.sock:/var/run/docker.sock alpine/socat \
       TCP4-LISTEN:2375,fork,reuseaddr UNIX-CONNECT:/var/run/docker.sock'

2. Forward port 2375 to Minikube VM

   If Minikube has been started with ``--vm-driver=none`` skip this step.

   Otherwise forward port 2375 to VM created by Minikube:

.. code-block:: console

   $ vboxmanage controlvm "minikube" natpf1 "docker-http,tcp,127.0.0.1,2375,,2375"


**AT LOCAL MACHINE:**

Make your local Docker client connect to Docker daemon at remote host
running Minikube

3. Make an SSH port forward from localhost:2375 to remote host running Minikube

   Run following command, where ``$FQDN`` is URL to and ``$USER`` is your username
   at remote host running Minikube:

.. code-block:: console

   $ ssh -L 2375:localhost:2375 $USER@$FQDM


4. Set ``$DOCKER_HOST`` and ``$DOCKER_API_VERSION`` environment variables

.. code-block:: console

   $ export DOCKER_API_VERSION="1.23"
   $ export DOCKER_HOST="tcp://localhost:2375"

5. Test Docker client

.. code-block:: console

   $ docker info | grep Name:

You should now be able to control docker daemon of your Minikube VM running on
remote host for e.g. building, tagging and deleting of images.

Expose API of REANA-Server on remote host
+++++++++++++++++++++++++++++++++++++++++

After you have deployed REANA components to your remote host, you must expose
API of REANA-Server in order for reana-client to be able to interact with it.

1. If you used ``--vm-driver=none`` when creating Kubernetes deployment with
Minikube you don't need to setup port forwarding. Otherwise run

.. code-block:: console

   $ vboxmanage controlvm "minikube" natpf1 "rs-http,tcp,,32767,,32767"

2. Next patch K8S Service of REANA-Server to use port 32767 for incoming
connections:

.. code-block:: console

   $ kubectl patch svc server --patch \
     "spec:
       ports:
       - port: 80
         nodePort: 32767"

(https://kubernetes.io/docs/tasks/run-application/update-api-object-kubectl-patch/)

3. Make an SSH port forward from localhost:32767 to remote host running Minikube

   Run following command, where ``$FQDN`` is URL to and ``$USER`` is your username
   at remote host running Minikube:

.. code-block:: console

   $ ssh -L 32767:localhost:32767 $USER@$FQDM

4. Finally setup REANA-Client to use ``$FQDN:32767`` as URL for connecting to
REANA-Server

Locally mount folders at remote host
++++++++++++++++++++++++++++++++++++

It is useful to locally mount folders at remote host that are mounted to
Minikube VM (and through K8S hostPath-configuration to Pods running
REANA components) to avoid needing to manually upload files to remote host
every time you make a code change.
You can use technologies such as NFS or SSHFS to achieve such mounting.
This guide provides example of a working SSHFS setup.

After setting up SSHFS mounts you would directly edit or replace sources of
REANA components in the mounted path, delete Pod(s) of edited REANA components
and see your code changes on the new Pod which is created automatically.

Note that you must manually mount the SSHFS mounts everytime you start working
on REANA sources. It is also recommended that you unmount the sources when
you stop working.

To mount sources folder on remote host you would run the following command:

.. code-block:: console

   $ sshfs $USER@$FQDM:$REMOTE_PATH $LOCAL_PATH \
       -o Compression=yes \
       -o cache=yes \
       -o kernel_cache \
       -o follow_symlinks \
       -o idmap=user \
       -o no_remote_lock \
       -o ServerAliveInterval=60 \
       -o reconnect

``$FQDN`` is URL to and ``$USER`` is your username at remote host running Minikube.
``$REMOTE_PATH`` is the path on remote host where you will clone git
repositories of REANA components and which will be later mounted to
Minikube VM.
``$LOCAL_PATH`` is the path on local machine which you want to map to remote host.

To unmount you would run the following command:

.. code-block:: console

   $ fusermount -uzq $LOCAL_PATH

where ``$LOCAL_PATH`` is the path on local machine where you have previously mounted
sources of REANA components on remote host.

**Use keyfile for authentication**

In case you want to authenticate by a key file specify on with
``-o IdentityFile=$KEYFILE_PATH`` option, where ``$KEYFILE_PATH`` is path to keyfile
used to authenticate to remote host.

**SSHFS and conenction encryption**

SSHFS encrypts connections to remote host and depending on the encryption your
local machine uses, file updates might be slow. To make file access faster
one can use weaker encryption algorith for SSHFS connection using
``-o Ciphers=arcfour`` option, but note that you must also enable this weak
arcfour cipher on sshd config on remote host. Usually this is accomplished
by adding set of allowed ciphers on sshd configuration file, which can usually
be found in ``/etc/ssh/sshd_config``.

Add following snippet to your sshd configuration file to allow use of arcfour
cipher. Sshd evaluates values from left to right, so stronger ciphers will
take preference and SSH client connecting to remote host will most likely
have explicitly specify use of arcfour (as done with SSHFS).

.. code-block:: none

   # Defaults recommended by https://www.ssh.com/ssh/sshd_config/
   # with addition of arcfour for fast SSHFS connections.
   Ciphers aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr,chacha20-poly1305@openssh.com,arcfour

**SSHFS and caching**

In some setups one might benefit from explicitly configuring cache
configuration values of SSHFS. Since file changes usually will happen only at
local machine one can define quite long cache periods which prevent SSHFS
to sync information about files that you haven't edited.
SSHFS automatically invalidates cache on file that you edit.
Following options have been observed to work OK, but no real performance
measurements have been concluded.

.. code-block:: console

   -o cache_timeout=115200 \
   -o attr_timeout=115200 \
   -o entry_timeout=1200 \
   -o max_readahead=90000 \

More information on SSHFS can be found, for example, from these URLs:
- https://github.com/libfuse/sshfs
- https://wiki.archlinux.org/index.php/SSHFS
