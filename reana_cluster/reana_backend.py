# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Abstract Base Class representing REANA cluster backend."""

from abc import ABCMeta, abstractmethod, abstractproperty


# An implementation of abstract class method that python 2 lacks.
# From: https://stackoverflow.com/a/11218474
class abstractclassmethod(classmethod):
    """."""

    __isabstractmethod__ = True

    def __init__(self, callable):
        """."""
        callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable)


class ReanaBackendABC(object):
    """."""

    __metaclass__ = ABCMeta
    __cluster_type = None

    @abstractproperty
    def cluster_type(self):
        """."""
        raise NotImplementedError()

    @abstractclassmethod
    def generate_configuration(cls, cluster_spec):
        """."""
        raise NotImplementedError()

    @abstractmethod
    def get_component(self, component_name):
        """."""
        raise NotImplementedError()

    @abstractmethod
    def down(self):
        """."""
        raise NotImplementedError()

    @abstractmethod
    def init(self):
        """."""
        raise NotImplementedError()

    @abstractmethod
    def restart(self):
        """."""
        raise NotImplementedError()

    @abstractmethod
    def verify_backend(self):
        """."""
        raise NotImplementedError()

    @abstractmethod
    def verify_components(self):
        """."""
        raise NotImplementedError()
