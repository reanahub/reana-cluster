.. _userguide:

User guide
==========

Prerequisites
-------------

REANA cloud uses `Kubernetes <https://kubernetes.io/>`_ container orchestration
system. The best way to try it out locally on your laptop is to set up `Minikube
<https://kubernetes.io/docs/getting-started-guides/minikube/>`_ with
`Helm <https://docs.helm.sh/using_helm/#install-helm>`_ and
`Traefik <https://github.com/helm/charts/tree/master/stable/traefik>`_
installed inside. How to do this depends on your operating system.

Versions
~~~~~~~~

For REANA v0.5, ``kubectl 1.13.1`` and ``minikube 0.32.0`` are known to work
well.

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

Here is one example of well-working versions for REANA v0.5.0:

.. code-block:: console

   $ pacman -Q | grep -iE '(docker|virtualbox|kube|qemu|libvirt)'
   docker 1:18.09.1-1
   docker-compose 1.23.2-1
   docker-machine 0.16.1-1
   docker-machine-driver-kvm2 0.32.0-1
   kubectl-bin 1.13.1-1
   libvirt 4.9.0-2
   minikube 0.32.0-1
   python-docker 3.7.0-1
   python-docker-pycreds 0.4.0-1
   python-dockerpty 0.4.1-3
   qemu 3.1.0-1
   virtualbox 6.0.2-1
   virtualbox-guest-iso 6.0.2-1
   virtualbox-host-modules-arch 6.0.2-2

Start minikube
--------------

Once you have installed ``kubectl`` and ``minikube``, you can start minikube by
running:

.. code-block:: console

   $ minikube config set memory 4096
   $ minikube start --kubernetes-version="v1.12.1" --feature-gates="TTLAfterFinished=true"

or, in case of KVM2 hypervisor:

.. code-block:: console

   $ minikube start --kubernetes-version="v1.12.1" --vm-driver=kvm2 --feature-gates="TTLAfterFinished=true"

You will see an output like:

.. code-block:: console

   Starting local Kubernetes v1.12.1 cluster...
   Starting VM...
   Getting VM IP address...
   Moving files into cluster...
   Setting up certs...
   Connecting to cluster...
   Setting up kubeconfig...
   Starting cluster components...
   Kubectl is now configured to use the cluster.
   Loading cached images from config file.

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

   $ # create new virtual environment
   $ virtualenv ~/.virtualenvs/myreana
   $ source ~/.virtualenvs/myreana/bin/activate
   $ # install reana-cluster utility
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

.. literalinclude:: ../reana_cluster/configurations/reana-cluster.yaml
   :language: yaml

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
   REANA cluster is initialised.

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
   wdb                     match
   db                      match

Verify REANA cluster readiness
------------------------------

You can verify whether the REANA cluster is ready to serve the user requests by
running the ``status`` command:

.. code-block:: console

   $ reana-cluster status
   job-controller          Running
   message-broker          Running
   server                  Running
   workflow-controller     Running
   workflow-monitor        Running
   zeromq-msg-proxy        Running
   wdb                     Running
   db                      Running
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

You can execute the displayed command easily as follows:

.. code-block:: console

   $ eval $(reana-cluster env)

Delete REANA cluster deployment
-------------------------------

To bring the cluster deployment down, i.e. delete all REANA components that
were deployed during ``init``, you can run:

.. code-block:: console

   $ reana-cluster down
