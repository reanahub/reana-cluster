.. _userguide:

User guide
==========

Prerequisites
-------------

REANA cloud uses `Kubernetes <https://kubernetes.io/>`_ container orchestration
system. The best way to try it out locally on your laptop is to set up `Minikube
<https://kubernetes.io/docs/getting-started-guides/minikube/>`_. How to do this
depends on your operating system.

Versions
~~~~~~~~

For REANA v0.2.0, ``kubectl 1.9.1`` and ``minikube 0.23.0`` are known to work
well. The later versions of Minikube were observed to lead to some networking
troubles.

Arch Linux
~~~~~~~~~~

For example, on Arch Linux, you should install the following packages:

- `docker <https://www.archlinux.org/packages/community/x86_64/docker/>`_
- `kubectl-bin (AUR) <https://aur.archlinux.org/packages/kubectl-bin/>`_
- `minikube (AUR) <https://aur.archlinux.org/packages/minikube/>`_

Moreover, if you plan to run Minikube via the VirtualBox hypervisor, you should
install also:

- `virtualbox <https://www.archlinux.org/packages/community/x86_64/virtualbox/>`_
- `virtualbox-guest-iso <https://www.archlinux.org/packages/community/x86_64/virtualbox-guest-iso/>`_
- `virtualbox-host-modules-arch <https://www.archlinux.org/packages/community/x86_64/virtualbox-host-modules-arch/>`_

Alternatively, if you plan to run Minikube using the KVM2 hypervisor:

- `docker-machine <https://www.archlinux.org/packages/community/x86_64/docker-machine/>`_
- `docker-machine-driver-kvm2 (AUR) <https://aur.archlinux.org/packages/docker-machine-driver-kvm2/>`_
- `libvirt <https://www.archlinux.org/packages/community/x86_64/libvirt/>`_
- `qemu <https://www.archlinux.org/packages/extra/x86_64/qemu/>`_

Here is one example of well-working versions for REANA v0.2.0:

.. code-block:: console

   $ pacman -Q | grep -iE '(docker|virtualbox|kube|qemu|libvirt)'
   docker 1:18.04.0-1
   docker-compose 1.21.0-1
   docker-machine 0.14.0-1
   docker-machine-driver-kvm2 0.25.2-1
   kubectl-bin 1.9.1-1
   libvirt 4.2.0-1
   minikube 0.23.0-1
   python-docker 3.2.1-1
   python-docker-pycreds 0.2.2-1
   python-dockerpty 0.4.1-2
   qemu 2.11.1-2
   virtualbox 5.2.8-1
   virtualbox-guest-iso 5.2.8-1
   virtualbox-host-modules-arch 5.2.8-11

Start minikube
--------------

Once you have installed ``kubectl`` and ``minikube``, you can start minikube by
running:

.. code-block:: console

   $ minikube start --kubernetes-version="v1.6.4"

or, in case of KVM2 hypervisor:

.. code-block:: console

   $ minikube start --kubernetes-version="v1.6.4" --vm-driver=kvm2

You will see an output like:

.. code-block:: console

   Starting local Kubernetes v1.6.4 cluster...
   Starting VM...
   Getting VM IP address...
   Moving files into cluster...
   Setting up certs...
   Connecting to cluster...
   Setting up kubeconfig...
   Starting cluster components...
   Kubectl is now configured to use the cluster.

As seen from the output, Minikube startup routines already configured
``kubectl`` to interact with the newly created Kubernetes deployment, but it
best to test whether ``kubectl`` is indeed configured properly:

.. code-block:: console

   $ kubectl get all
   NAME             TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
   svc/kubernetes   ClusterIP   10.0.0.1     <none>        443/TCP   1m

Install ``reana-cluster`` CLI tool
----------------------------------

``reana-cluster`` command line interface tool is easily installable from PyPI.
You may want to install it into a new virtual environment:

.. code-block:: console

   $ mkvirtualenv reana-cluster
   $ pip install reana-cluster

.. _configure:

Configure REANA cluster
-----------------------

The main function of ``reana-cluster`` command line tool is to initialise a
working REANA cluster, ready to run workflows that users submit via
``reana-client``.

In order to achieve this, ``reana-cluster`` needs to know how the REANA cluster
should be set up; e.g. what versions of REANA components should be deployed and
how the configuration of each component should be set up. ``reana-cluster``
expects to get this information via ``reana-cluster.yaml`` file that comes with
the package:

.. code-block:: yaml

   cluster:
     type: "kubernetes"
     version: "v1.6.4"
     url: "http://localhost"

   components:
     reana-workflow-controller:
       type: "docker"
       image: "reanahub/reana-workflow-controller:0.2.0"
       environment:
         - SHARED_VOLUME_PATH: "/reana"
         - ORGANIZATIONS: "default,alice,atlas,cms,lhcb"

     reana-job-controller:
       type: "docker"
       image: "reanahub/reana-job-controller:0.2.0"
       environment:
         - REANA_STORAGE_BACKEND: "LOCAL"

     reana-server:
       type: "docker"
       image: "reanahub/reana-server:0.2.0"

     reana-message-broker:
       type: "docker"
       image: "reanahub/reana-message-broker:0.2.0"

     reana-workflow-monitor:
       type: "docker"
       image: "reanahub/reana-workflow-monitor:0.2.0"
       environment:
         - ZMQ_PROXY_CONNECT: "tcp://zeromq-msg-proxy.default.svc.cluster.local:8667"

     reana-workflow-engine-yadage:
       type: "docker"
       image: "reanahub/reana-workflow-engine-yadage:0.2.0"
       environment:
         - ZMQ_PROXY_CONNECT: "tcp://zeromq-msg-proxy.default.svc.cluster.local:8666"

     reana-workflow-engine-cwl:
       type: "docker"
       image: "reanahub/reana-workflow-engine-cwl:0.2.0"
       environment:
         - ZMQ_PROXY_CONNECT: "tcp://zeromq-msg-proxy.default.svc.cluster.local:8666"

You can use the supplied ``reana-cluster.yaml``, or create your own custom
configuration. For instance, if you wish to use a different Docker image for the
``reana-server`` component, you can copy the default ``reana-cluster.yaml`` to a
``reana-cluster-custom.yaml`` file and change the image tag
``reanahub/reana-server:0.2.0`` according to your wishes.

Initialise a REANA cluster
--------------------------

Initialising a REANA cluster is just a matter of running ``init`` command:

.. code-block:: console

   $ reana-cluster init
   REANA cluster is initialised

If you have created a custom configuration, you can use the ``-f`` command-line
option and specify your own file in the following way:

.. code-block:: console

  $ reana-cluster -f reana-cluster-custom.yaml init

Verify REANA components
-----------------------

You can verify that components deployed to REANA cluster are set up according to
what is defined in REANA cluster specifications file via the ``verify`` command:

.. code-block:: console

   $ reana-cluster verify components
   COMPONENT               IMAGE
   job-controller          match
   message-broker          match
   server                  match
   workflow-controller     match
   workflow-monitor        match
   zeromq-msg-proxy        match
   yadage-default-worker   match
   yadage-alice-worker     match
   yadage-atlas-worker     match
   yadage-cms-worker       match
   yadage-lhcb-worker      match
   cwl-default-worker      match
   wdb                     match

Verify REANA cluster readiness
------------------------------

You can verify whether the REANA cluster is ready to serve the user requests by
running the ``status`` command:

.. code-block:: console

   $ reana-cluster status
   COMPONENT               STATUS
   job-controller          Running
   message-broker          Running
   server                  Running
   workflow-controller     Running
   workflow-monitor        Running
   zeromq-msg-proxy        Running
   yadage-default-worker   Running
   yadage-alice-worker     Running
   yadage-atlas-worker     Running
   yadage-cms-worker       Running
   yadage-lhcb-worker      Running
   cwl-default-worker      Running
   wdb                     Running
   REANA cluster is ready.

In the above example, everything is running and the REANA cluster is ready for
serving user requests.

Display commands to set up the environment for the REANA client
---------------------------------------------------------------

You can print the list of commands to configure the environment for the
`reana-client <https://reana-client.readthedocs.io/>`_:

.. code-block:: console

   $ reana-cluster env
   export REANA_SERVER_URL=http://192.168.39.247:31106

Delete REANA cluster deployment
-------------------------------

To bring the cluster deployment down, i.e. delete all REANA components that
were deployed during ``init``, you can run:

.. code-block:: console

   $ reana-cluster down
