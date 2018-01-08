"""
Copyright (c) 2017 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""
from __future__ import absolute_import, unicode_literals


from copy import deepcopy
from osbs.build.manipulate import DockJsonManipulator
from osbs.constants import SECRETS_PATH
from osbs.exceptions import OsbsValidationException
from six.moves import zip_longest

import logging
import os


logger = logging.getLogger(__name__)


class PluginsRenderer(object):
    """Render atomic-reactor plugins configuration

    This class is used to render the desired plugins configuration
    to be used by atomic-reactor.
    """

    def __init__(self, build_spec, plugins_config_template, customization_config_template=None):
        self.spec = build_spec
        self._plugins_config = deepcopy(plugins_config_template)
        self._customization_config = deepcopy(customization_config_template)

        self.dj = DockJsonManipulator(None, self._plugins_config)

    def render(self):
        # TODO: adjust_*
        # TODO: apply_customizations
        self.render_prebuild_plugins()
        self.render_buildstep_plugins()
        self.render_postbuild_plugins()
        self.render_prepublish_plugins()
        self.render_exit_plugins()

        return self._plugins_config

    def render_prebuild_plugins(self):
        # pre_add_dockerfile.py - Not rendered
        # pre_add_filesystem.py
        self.render_add_filesystem()
        # pre_add_help.py - Not rendered
        # pre_add_labels_in_df.py
        self.render_add_labels_in_dockerfile()
        # pre_add_yum_repo_by_url.py
        self.render_add_yum_repo_by_url()
        # pre_add_yum_repo.py - Not rendered
        # pre_assert_labels.py - Not rendered
        # pre_bump_release.py
        self.render_bump_release()
        # pre_change_from_in_df.py - Not rendered
        # pre_check_and_set_rebuild.py
        self.render_check_and_set_rebuild()
        # pre_distribution_scope.py
        # pre_fetch_maven_artifacts.py
        # pre_flatpak_create_dockerfile.py
        # pre_inject_parent_image.py
        # pre_inject_yum_repo.py
        # pre_koji_parent.py
        # pre_koji.py
        # pre_pull_base_image.py
        # pre_pyrpkg_fetch_artefacts.py
        # pre_reactor_config.py
        # pre_resolve_composes.py
        # pre_resolve_module_compose.py
        # pre_stop_autorebuild_if_disabled.py

    def render_add_filesystem(self):
        phase = 'prebuild_plugins'
        plugin = 'add_filesystem'

        if self.dj.dock_json_has_plugin_conf(phase, plugin):
            if not self.spec.kojihub.value:
                raise OsbsValidationException(
                    'Custom base image builds require kojihub to be defined')
            self.dj.dock_json_set_arg(phase, plugin, 'koji_hub',
                                      self.spec.kojihub.value)
            if self.spec.yum_repourls.value:
                self.dj.dock_json_set_arg(phase, plugin, 'repos',
                                          self.spec.yum_repourls.value)
            if self.spec.platforms.value:
                self.dj.dock_json_set_arg(phase, plugin, 'architectures',
                                          self.spec.platforms.value)

            if self.spec.filesystem_koji_task_id.value:
                self.dj.dock_json_set_arg(phase, plugin, 'from_task_id',
                                          self.spec.filesystem_koji_task_id.value)

    def render_add_labels_in_dockerfile(self):
        phase = 'prebuild_plugins'
        plugin = 'add_labels_in_dockerfile'
        if not self.dj.dock_json_has_plugin_conf(phase, plugin):
            return

        implicit_labels = {}
        label_spec = {
            'vendor': self.spec.vendor,
            'authoritative-source-url': self.spec.authoritative_registry,
            'distribution-scope': self.spec.distribution_scope,
            'release': self.spec.release,
        }

        for label, spec in label_spec.items():
            if spec.value is not None:
                implicit_labels[label] = spec.value

        self.dj.dock_json_merge_arg(phase, plugin, 'labels', implicit_labels)

        if self.spec.info_url_format.value:
            self.dj.dock_json_set_arg(phase, plugin, 'info_url_format',
                                      self.spec.info_url_format.value)

        if self.spec.equal_labels.value:
            self.dj.dock_json_set_arg(phase, plugin, 'equal_labels',
                                      self.spec.equal_labels.value)

    def render_add_yum_repo_by_url(self):
        if (self.spec.yum_repourls.value is not None and
                self.dj.dock_json_has_plugin_conf('prebuild_plugins',
                                                  "add_yum_repo_by_url")):
            self.dj.dock_json_set_arg('prebuild_plugins',
                                      "add_yum_repo_by_url", "repourls",
                                      self.spec.yum_repourls.value)
            if self.spec.proxy.value:
                self.dj.dock_json_set_arg('prebuild_plugins',
                                          "add_yum_repo_by_url", "inject_proxy",
                                          self.spec.proxy.value)

    def render_bump_release(self):
        """
        If the bump_release plugin is present, configure it
        """
        phase = 'prebuild_plugins'
        plugin = 'bump_release'
        if not self.dj.dock_json_has_plugin_conf(phase, plugin):
            return

        if self.spec.release.value:
            logger.info('removing %s from request as release already specified',
                        plugin)
            self.dj.remove_plugin(phase, plugin)
            return

        hub = self.spec.kojihub.value
        if not hub:
            logger.info('removing %s from request as koji hub not specified',
                        plugin)
            self.dj.remove_plugin(phase, plugin)
            return

        self.dj.dock_json_set_arg(phase, plugin, 'hub', hub)

        # For flatpak, we want a name-version-release of
        # <name>-<stream>-<module_build_version>.<n>, where the .<n> makes
        # sure that the build is unique in Koji
        if self.spec.flatpak.value:
            self.dj.dock_json_set_arg(phase, plugin, 'append', True)

    def render_check_and_set_rebuild(self):
        if self.dj.dock_json_has_plugin_conf('prebuild_plugins',
                                             'check_and_set_rebuild'):
            self.dj.dock_json_set_arg('prebuild_plugins',
                                      'check_and_set_rebuild', 'url',
                                      self.spec.builder_openshift_url.value)

            use_auth = self.spec.use_auth.value
            if use_auth is not None:
                self.dj.dock_json_set_arg('prebuild_plugins',
                                          'check_and_set_rebuild',
                                          'use_auth', use_auth)

    def render_buildstep_plugins(self):
        pass

    def render_postbuild_plugins(self):
        self.render_tag_and_push_registries()

    def render_tag_and_push_registries(self):
        if self.dj.dock_json_has_plugin_conf('postbuild_plugins',
                                             'tag_and_push'):
            push_conf = self.dj.dock_json_get_plugin_conf('postbuild_plugins',
                                                          'tag_and_push')
            args = push_conf.setdefault('args', {})
            registries = args.setdefault('registries', {})
            placeholder = '{{REGISTRY_URI}}'

            if placeholder in registries:
                for registry, secret in zip_longest(self.spec.registry_uris.value,
                                                    self.spec.registry_secrets.value):
                    if not registry.uri:
                        continue

                    regdict = registries[placeholder].copy()
                    regdict['version'] = registry.version
                    if secret:
                        regdict['secret'] = os.path.join(SECRETS_PATH, secret)

                    registries[registry.docker_uri] = regdict

                del registries[placeholder]

    def render_prepublish_plugins(self):
        pass

    def render_exit_plugins(self):
        pass

