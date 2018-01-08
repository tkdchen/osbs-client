"""
Copyright (c) 2017 Red Hat, Inc
All rights reserved.

This software may be modified and distributed under the terms
of the BSD license. See the LICENSE file for details.
"""

from __future__ import unicode_literals

from copy import deepcopy
import pytest

from osbs.build.plugins_renderer import PluginsRenderer
from osbs.build.spec import BuildSpec
from osbs.constants import SECRETS_PATH
from osbs.exceptions import OsbsValidationException
from tests.constants import TEST_GIT_BRANCH, TEST_GIT_REF, TEST_GIT_URI


class TestPluginsRenderer(object):

    def test_render(self):
        spec = self._make_build_spec()
        plugins_config_template = {}
        expected_plugins_config = {}

        renderer = PluginsRenderer(spec, plugins_config_template)
        assert renderer.render() == expected_plugins_config

    @pytest.mark.parametrize(('params', 'expected'), (
        ({}, {}),

        (
            {'yum_repourls': ['http://example.com/yum1.repo', 'http://example.com/yum2.repo']},
            {'repos': ['http://example.com/yum1.repo', 'http://example.com/yum2.repo']}
        ),

        ({'platforms': ['x86_64', 'ppc64le']}, {'architectures': ['x86_64', 'ppc64le']}),

        ({'filesystem_koji_task_id': 12345678}, {'from_task_id': 12345678}),
    ))
    def test_render_add_filesystem(self, params, expected):
        params.setdefault('kojihub', 'http://hub/')
        expected.setdefault('koji_hub', 'http://hub/')

        spec = self._make_build_spec(params)

        plugins_config_template = {'prebuild_plugins': [{'name': 'add_filesystem', 'args': {}}]}

        expected_plugins_config = {
            'prebuild_plugins': [{'name': 'add_filesystem', 'args': expected}
            ]}

        renderer = PluginsRenderer(spec, plugins_config_template)
        assert renderer.render() == expected_plugins_config

    def test_render_add_filesystem_koji_hub_required(self):
        spec = self._make_build_spec()
        plugins_config_template = {'prebuild_plugins': [{'name': 'add_filesystem', 'args': {}}]}
        renderer = PluginsRenderer(spec, plugins_config_template)

        with pytest.raises(OsbsValidationException):
            renderer.render()

    @pytest.mark.parametrize(('template', 'params', 'expected'), (
        ({}, {}, {}),

        (
            {'labels': {'static': 'spam'}},
            {
                'vendor': 'Foo Vendor',
                'authoritative_registry': 'registry.example.com',
                'distribution_scope': 'private',
                'release': '33',
            },
            {
                'labels': {
                    'vendor': 'Foo Vendor',
                    'authoritative-source-url': 'registry.example.com',
                    'distribution-scope': 'private',
                    'release': '33',
                    'static': 'spam',
                }
            }
        ),
        (
            {},
            {
                'info_url_format': 'http://example.com/info/#/{name}/{version}/{release}',
            },
            {
                'info_url_format': 'http://example.com/info/#/{name}/{version}/{release}',
            }
        ),
        (
            {},
            {
                'equal_labels': [['name1', 'name2', 'name3'], ['release1', 'release2']],
            },
            {
                'equal_labels': [['name1', 'name2', 'name3'], ['release1', 'release2']],
            }
        ),
    ))
    def test_render_add_labels_in_dockerfile(self, template, params, expected):
        expected.setdefault('labels', {})

        spec = self._make_build_spec(params)

        plugins_config_template = {'prebuild_plugins': [
            {'name': 'add_labels_in_dockerfile', 'args': template}
        ]}

        expected_plugins_config = {
            'prebuild_plugins': [{'name': 'add_labels_in_dockerfile', 'args': expected}
        ]}

        renderer = PluginsRenderer(spec, plugins_config_template)
        assert renderer.render() == expected_plugins_config

    @pytest.mark.parametrize(('params', 'expected'), (
        ({}, {}),

        (
            {'yum_repourls': ['http://example.com/yum1.repo', 'http://example.com/yum2.repo']},
            {'repourls': ['http://example.com/yum1.repo', 'http://example.com/yum2.repo']},
        ),

        (
            {
                'yum_repourls': ['http://example.com/yum1.repo'],
                'proxy': 'http://proxy.example.com',
            },
            {
                'repourls': ['http://example.com/yum1.repo'],
                'inject_proxy': 'http://proxy.example.com',
            },
        )
    ))
    def test_render_add_yum_repo_by_url(self, params, expected):
        expected.setdefault('repourls', [])

        spec = self._make_build_spec(params)

        plugins_config_template = {'prebuild_plugins': [
            {'name': 'add_yum_repo_by_url', 'args': {}}
        ]}

        expected_plugins_config = {
            'prebuild_plugins': [{'name': 'add_yum_repo_by_url', 'args': expected}
        ]}

        renderer = PluginsRenderer(spec, plugins_config_template)
        assert renderer.render() == expected_plugins_config

    @pytest.mark.parametrize(('params', 'expected'), (
        ({}, None),
        ({'release': '33'}, None),

        (
            {'kojihub': 'http://hub/'},
            {'hub': 'http://hub/'},
        ),

        (
            {'kojihub': 'http://hub/', 'flatpak': True},
            {'hub': 'http://hub/', 'append': True},
        ),
    ))
    def test_render_bump_release(self, params, expected):
        spec = self._make_build_spec(params)

        plugins_config_template = {'prebuild_plugins': [
            {'name': 'bump_release', 'args': {}}
        ]}

        if expected is None:
            expected_plugins_config = {'prebuild_plugins': []}
        else:
            expected_plugins_config = {
                'prebuild_plugins': [{'name': 'bump_release', 'args': expected}
            ]}

        renderer = PluginsRenderer(spec, plugins_config_template)
        assert renderer.render() == expected_plugins_config

    @pytest.mark.parametrize(('params', 'expected'), (
        ({}, {}),

        (
            {'use_auth': True},
            {'use_auth': True},
        ),

        (
            {'use_auth': False},
            {'use_auth': False},
        ),

        # (
        #     {'kojihub': 'http://hub/', 'flatpak': True},
        #     {'hub': 'http://hub/', 'append': True},
        # ),
    ))
    def test_check_and_set_rebuild(self, params, expected):
        params.setdefault('builder_openshift_url', 'https://openshift/')
        expected.setdefault('url', 'https://openshift/')
        spec = self._make_build_spec(params)

        plugins_config_template = {'prebuild_plugins': [
            {'name': 'check_and_set_rebuild', 'args': {}}
        ]}

        expected_plugins_config = {
            'prebuild_plugins': [{'name': 'check_and_set_rebuild', 'args': expected}
        ]}

        renderer = PluginsRenderer(spec, plugins_config_template)
        assert renderer.render() == expected_plugins_config

    @pytest.mark.parametrize(('template', 'params', 'expected'), (
        (
            # template
            {'{{REGISTRY_URI}}': {}},

            # params
            {
                'registry_uris': ['https://example.one.com'],
                'registry_secrets': ['secret-one'],
            },

            # expected
            {
                'example.one.com': {
                    'secret': SECRETS_PATH + '/secret-one',
                    'version': 'v1',
                }
            }
        ),

        (
            # template
            {'{{REGISTRY_URI}}': {}},

            # params
            {
                'registry_uris': ['https://example.one.com'],
            },

            # expected
            {
                'example.one.com': {
                    'version': 'v1',
                }
            }
        ),

        (
            # template
            {'{{REGISTRY_URI}}': {}},

            # params
            {
                'registry_uris': ['https://example.one.com', 'https://example.two.com/v2'],
                'registry_secrets': ['secret-one', 'secret-two'],
            },

            # expected
            {
                'example.one.com': {
                    'secret': SECRETS_PATH + '/secret-one',
                    'version': 'v1',
                },
                'example.two.com': {
                    'secret': SECRETS_PATH + '/secret-two',
                    'version': 'v2',
                },
            }
        ),

        (
            # template
            {
                'example.static.com': {
                    'secret': SECRETS_PATH + '/secret-static',
                    'version': 'v2',
                }
            },

            # params
            {
                # Only used if placeholder is in template.
                'registry_uris': ['https://example.ignored.com'],
                'registry_secrets': ['secret-ignored'],
            },

            # expected
            {
                'example.static.com': {
                    'secret': SECRETS_PATH + '/secret-static',
                    'version': 'v2',
                }
            }
        ),

    ))
    def test_render_tag_and_push_registries_all(self, template, params, expected):
        spec = self._make_build_spec(params)

        plugins_config_template = {
            'postbuild_plugins': [
                {'name': 'tag_and_push', 'args': {'registries': template}}
            ]
        }

        expected_plugins_config = {
            'postbuild_plugins': [
                {'name': 'tag_and_push', 'args': {'registries': expected}}
            ]
        }

        renderer = PluginsRenderer(spec, plugins_config_template)
        assert renderer.render() == expected_plugins_config

    def _make_build_spec(self, additional_params=None):
        params = {
            'git_uri': TEST_GIT_URI,
            'git_ref': TEST_GIT_REF,
            'git_branch': TEST_GIT_BRANCH,
            'user': 'john-foo',
            'base_image': 'fedora:latest',
            'name_label': 'fedora/resultingimage',
        }

        if additional_params:
            params.update(additional_params)

        spec = BuildSpec()
        spec.set_params(**params)
        return spec

