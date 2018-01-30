"""
Copyright (c) 2017 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""
from __future__ import unicode_literals

import json
import logging

from osbs.utils import graceful_chain_get, get_time_from_rfc3339


logger = logging.getLogger(__name__)


class BuildConfigResponse(object):
    """ class which wraps json from http response from OpenShift """

    def __init__(self, build_config_json):
        """
        :param build_config_json: dict from JSON of OpenShift Build object
        """
        self.json = build_config_json

    @property
    def name(self):
        return graceful_chain_get(self.json, "metadata", "name")

    @property
    def labels(self):
        return graceful_chain_get(self.json, "metadata", "labels")

    @property
    def koji_task_id(self):
        return graceful_chain_get(self.labels, "koji-task-id")

    @property
    def git_branch(self):
        return graceful_chain_get(self.labels, "git-branch")

    @property
    def git_repo_name(self):
        return graceful_chain_get(self.labels, "git-repo-name")

    @property
    def triggers(self):
        return graceful_chain_get(self.json, "spec", "triggers")
