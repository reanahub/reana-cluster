.. _developerguide:

Developer guide
===============

Using Docker with Minikube
--------------------------

When you are developing you will probably want to connect your shell session to
talk to the Docker daemon inside the Minikube. You can achieve this by
running:

.. code-block:: console

   $ eval "$(minikube docker-env)"

In this way you can build Docker images of REANA cluster components directly
inside your Minikube virtual machine and deploy them very quickly without having
to pull images from remote registries.

Deploying specific component versions
-------------------------------------

If you want to try different versions of REANA components, you can modify your
``reana-cluster-minikube.yaml`` configuration file; see :ref:`configure`.

You can check available released versions on `REANA DockerHub
<https://hub.docker.com/u/reanahub/>`_.

Deploying latest ``master`` branch versions
-------------------------------------------

If you want to use latest ``master`` branch of REANA components and have the
code directly editable within pods, you can use ``reana-cluster-minikube.yaml``
(in production-like conditions) or ``reana-cluster-minikube-dev.yaml`` (in
development-like conditions with the debugger and live editing of component
sources).

1. Clone the REANA component under ``$HOME/reana/sources`` directory on your laptop.

2. Mount your component source code in minikube under `/code` directory:

.. code-block:: console

   $ ls -d $HOME/reana/sources
   reana-client
   reana-cluster
   reana-message-broker
   reana-server
   reana-workflow-controller
   $ minikube mount $HOME/reana/sources:/code

3. Edit sources on your laptop under ``$HOME/reana/sources/reana-<component>/...`` as usual:

.. code-block:: console

   $ vim $HOME/reana/sources/reana-workflow-controller/reana_workflow_controller/app.py

4. Delete your pod and see a new pod being deployed with your changes:

.. code-block:: console

   $ kubectl get pods | grep workflow-controller
   $ kubectl delete pod workflow-controller-2461563162-r4hgg
   $ sleep 10 # wait some time...
   $ kubectl get pods | grep workflow-controller
   $ kubectl exec -i -t workflow-controller-2461563162-h9ptw /bin/bash

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
   Straigthforward way is to create two new files, ``reana-cluster-minikube-dev.yaml`` file
   which gets Kubernetes (K8S API url and authentication details) configuration
   from ``development-kubeconfig.yaml`` file. Below is copy-pasteable contents of
   the two files. Create them on your working directory.

.. code-block:: yaml

   #reana-cluster-minikube-dev.yaml
   cluster:
     type: "kubernetes"
     config: "./development-kubeconfig.yaml"
     config_context: "minikube"
     version: "v1.16.3"
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
         - WDB_SOCKET_SERVER: "wdb"
         - WDB_NO_BROWSER_AUTO_OPEN: "True"
         - FLASK_DEBUG: "1"

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

6. Instruct ``reana-cluster`` to use your own reana-cluster-minikube.yaml by using ``-f`` flag:

.. code-block:: console

   $ reana-cluster -f $(pwd)/reana-cluster-minikube-dev.yaml verify backend

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

Managing multiple REANA clusters inside Minikube
------------------------------------------------

Creating a new cluster
++++++++++++++++++++++

Stop current cluster (``minikube``, which if you didn't change it, is the default one):

.. code:: console

    $ kubectl get pods
    NAME                                     READY     STATUS    RESTARTS   AGE
    message-broker-1926055025-4jjdm          1/1       Running   0          7m
    server-1390351625-dxk52                  1/1       Running   0          7m
    wdb-3285397567-1c8p0                     1/1       Running   0          7m
    workflow-controller-2663988704-3cjlm     1/1       Running   4          7m
    $ minikube stop
    Stopping local Kubernetes cluster...
    Machine stopped.

Now we create a new cluster to host a new ``reana`` version (0.1.0):

.. code:: console

    $ minikube start --profile reana-0.1.0 --feature-gates="TTLAfterFinished=true"
    Starting local Kubernetes v1.16.3 cluster...
    Starting VM...
    Getting VM IP address...
    Moving files into cluster...
    Setting up certs...
    Connecting to cluster...
    Setting up kubeconfig...
    Starting cluster components...
    Kubectl is now configured to use the cluster.

.. warning::

   Use lower case alphanumeric characters, '-' or '.' to name your ``profile``
   since Kubernetes specification for ``Nodes`` follows this schema. This
   problem is hard to spot since everything looks like it is working but
   ``pods`` are indifindefinitely pending, you have to run ``minikube logs``
   to find out.

   .. code:: console

      $ minikube logs
      ...
      Node "reana_0.1.0" is invalid: metadata.name: Invalid value: "reana_0.1.0": a DNS-1123 subdomain must consist of lower case alphanumeric characters, '-' or '.',
      ...


We can now switch to use the profile (which is a new Kubernetes cluster running
on ag new and fresh VM):

.. code:: console

    $ minikube profile reana-0.1.0
    minikube profile was successfully set to reana-0.1.0
    $ minikube status
    minikube: Running
    cluster: Running
    kubectl: Correctly Configured: pointing to minikube-vm at 192.168.99.101

Since we have a new cluster, there won't be any ``pod``:

.. code:: console

    $ kubectl get pod
    No resources found.

The ``minikube`` concept of ``--profile`` maps to Kubernetes
``contexts``, so now we have to amend ``reana-cluster`` config
(``reana_cluster/configuration/reana-cluster-minikube.yaml``) to use this new
context:

.. code:: diff

    cluster:
      type: "kubernetes"
      # Can be used to specify kubeconfig configuration that reana-cluster will
      # use to connecting to K8S cluster. If not specified, will default to
      # '$HOME/.kube/config', which is default location of `kubectl` tool.
      #config: "./development-kubeconfig.yaml"

      # Specifies which K8S context from the kubeconfig configuration will be used.
      # If not specified will use the value of `current-context:` key of kubeconfig.
    - # config_context: "minikube"
    + config_context: "reana-0.1.0"
      version: "v1.16.3"
      url: "http://localhost"

And now you can start the cluster as ``reana-cluster`` docs say:

.. code:: console

    $ reana-cluster init
    REANA cluster is initialised

Check that all components are created:

.. code:: console

    $ kubectl get pods
    NAME                                     READY     STATUS              RESTARTS   AGE
    message-broker-3641009106-c2rzx          1/1       Running             0          17m
    server-2623620487-15pqq                  1/1       Running             0          17m
    wdb-3285397567-cs8tv                     1/1       Running             0          17m
    workflow-controller-3501752780-h327m     1/1       Running             0          5m

Switching to previous cluster
+++++++++++++++++++++++++++++

We can pause the cluster we have just created:

.. code:: console

    $ minikube stop
    Stopping local Kubernetes cluster...
    Machine stopped.
    $ minikube status
    minikube: Stopped
    cluster:
    kubectl:

We switch to the profile which holds the previous cluster (which was the
default one, ``minikube``:

.. code:: console

    $ minikube profile minikube
    minikube profile was successfully set to minikube
    $ minikube status
    minikube: Stopped
    cluster:
    kubectl:

Now we can restart the cluster:

.. code:: console

    $ minikube start --profile minikube --feature-gates="TTLAfterFinished=true"
    Starting local Kubernetes v1.16.3 cluster...
    Starting VM...
    Getting VM IP address...
    Moving files into cluster...
    Setting up certs...
    Connecting to cluster...
    Setting up kubeconfig...
    Starting cluster components...
    Kubectl is now configured to use the cluster.

If we list now the pods, we can see that they are the original ones:

.. code:: console

    $ kubectl get pods
    NAME                                     READY     STATUS    RESTARTS   AGE
    message-broker-1926055025-4jjdm          1/1       Running   1          58m
    server-1390351625-dxk52                  1/1       Running   1          58m
    wdb-3285397567-1c8p0                     1/1       Running   1          58m
    workflow-controller-2663988704-3cjlm     1/1       Running   5          58m
