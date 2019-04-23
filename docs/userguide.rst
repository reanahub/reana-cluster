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

For REANA v0.5, ``kubectl 1.14.0`` and ``minikube 1.0.0`` are known to work
well.

Arch Linux
~~~~~~~~~~

For example, on Arch Linux, you should install the following packages:

- `docker <https://www.archlinux.org/packages/community/x86_64/docker/>`_
- `kubectl <https://www.archlinux.org/packages/community/x86_64/kubectl/>`_
- `minikube <https://www.archlinux.org/packages/community/x86_64/minikube/>`_
- `kubernetes-helm <https://aur.archlinux.org/packages/kubernetes-helm/>`_

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
   docker 1:18.09.5-1
   docker-compose 1.24.0-1
   docker-machine 0.16.1-2
   docker-machine-driver-kvm2 1.0.0-1
   kubectl-bin 1.14.0-1
   kubernetes-helm-bin 2.13.1-1
   libvirt 5.2.0-1
   minikube-bin 1.0.0-1
   python-docker 3.7.2-1
   python-docker-pycreds 0.4.0-1
   python-dockerpty 0.4.1-4
   qemu 3.1.0-2
   virtualbox 6.0.6-1
   virtualbox-guest-iso 6.0.6-1
   virtualbox-host-modules-arch 6.0.6-1

MacOS
~~~~~

For example, on MacOS, you should install the following packages:

- `docker <https://docs.docker.com/docker-for-mac/install/>`_
- `kubernetes-cli <https://kubernetes.io/docs/tasks/tools/install-kubectl/#install-with-homebrew-on-macos>`_
- `hyperkit <https://github.com/moby/hyperkit>`_
- `minikube <https://kubernetes.io/docs/tasks/tools/install-minikube/#macos>`_
- `helm <https://helm.sh/docs/using_helm/#from-homebrew-macos>`_

.. code-block:: console

   $ brew install kubernetes-cli
   $ brew install hyperkit
   $ brew cask install minikube
   $ brew install kubernetes-helm


Start minikube
--------------

Once you have installed ``kubectl`` and ``minikube``, you can start minikube by
running:

.. code-block:: console

   $ minikube config set memory 4096
   $ minikube start --feature-gates="TTLAfterFinished=true"

in case of KVM2 hypervisor:

.. code-block:: console

   $ minikube start --vm-driver=kvm2 --feature-gates="TTLAfterFinished=true"

or, in case of Hyperkit hypervisor:

.. code-block:: console

  $ minikube start --vm-driver=hyperkit --feature-gates="TTLAfterFinished=true"

You will see an output like:

.. code-block:: console

   Starting local Kubernetes v1.14.0 cluster...
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

   $ reana-cluster init --traefik
   REANA cluster is initialised.

If you have created a custom configuration, you can use the ``-f`` command-line
option and specify your own file. In the same way you can set URL for REANA cluster
``--url <cluster_url>``.

.. code-block:: console

  $ reana-cluster -f reana-cluster-custom.yaml --url reana.cern.ch init --traefik


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

Delete interactive sessions
---------------------------

Interactive sessions that were not closed after work have been finished leave
active Kubernetes objects (`pod`, `service` and `Ingress`) running in the REANA
cluster. These objects might need to be deleted from time to time. Please note
that interactive session pod and service are linked to the Ingress object. If it
gets deleted other two will be deleted automatically.

To delete open interactive sessions use following commands:

.. code-block:: console

   # get all ingresses of open interactive sessions
   $ kubectl get ingresses | grep interactive
   interactive-jupyter-ad814137-baec-4ee5-b899-1d549e90b44a   *                 80      103m
   interactive-jupyter-e4c7aa38-370b-47b7-bf8c-44f5f0f44b44   *                 80      3h48m
   interactive-jupyter-ec5438b1-65a8-4bba-a52c-ff7970242e83   *                 80      3h16m
   interactive-jupyter-f401874d-e9a6-4b2b-9b9d-12b0f141a442   *                 80      103m
   interactive-jupyter-f9f56f92-a533-4bcc-aad9-581f5e31ff0f   *                 80      103m
   # lets delete all remaining objects of open interactive sessions
   $ kubectl delete $(kubectl get ingresses -o name | grep interactive)
   ingress.extensions "interactive-jupyter-ad814137-baec-4ee5-b899-1d549e90b44a" deleted
   ingress.extensions "interactive-jupyter-e4c7aa38-370b-47b7-bf8c-44f5f0f44b44" deleted
   ingress.extensions "interactive-jupyter-ec5438b1-65a8-4bba-a52c-ff7970242e83" deleted
   ingress.extensions "interactive-jupyter-f401874d-e9a6-4b2b-9b9d-12b0f141a442" deleted
   ingress.extensions "interactive-jupyter-f9f56f92-a533-4bcc-aad9-581f5e31ff0f" deleted
