import pylons
import paste.fixture

import pylons.config as config

import ckan.logic as logic
import ckan.model as model
import ckan.tests as tests
import ckan.plugins as plugins
import ckan.lib.helpers as h
import ckanext.ngsipreview.plugin as previewplugin
import ckan.lib.create_test_data as create_test_data
import ckan.config.middleware as middleware


class TestNGSIPreview(tests.WsgiAppCase):

    @classmethod
    def setup_class(cls):
        wsgiapp = middleware.make_app(config['global_conf'], **config)
        plugins.load('ngsipreview')
        cls.app = paste.fixture.TestApp(wsgiapp)

        cls.p = previewplugin.NGSIPreview()
        #cls.p.proxy_is_enabled = False

        # create test resource
        create_test_data.CreateTestData.create()

        context = {
            'model': model,
            'session': model.Session,
            'user': model.User.get('testsysadmin').name
        }

        cls.package = model.Package.get('annakarenina')
        cls.resource = logic.get_action('resource_show')(
            context, {'id': cls.package.resources[1].id})
        cls.resource['url'] = pylons.config.get(
            'ckan.site_url', '//localhost:5000')
        logic.action.update.resource_update(context, cls.resource)

    @classmethod
    def teardown_class(cls):
        plugins.unload('ngsipreview')
        create_test_data.CreateTestData.delete()

    def test_js_included(self):
        res_id = self.resource['id']
        pack_id = self.package.name
        url = '/dataset/{0}/resource/{1}/preview'.format(pack_id, res_id)
        result = self.app.get(url, status='*')

        assert result.status == 200, result.status
        assert ((('preview_ngsi.js' in result.body)
                or ('preview_ngsi.min.js' in result.body))), result.body
        assert ((('highlight.pack.js' in result.body)
                or ('highlight.pack.js' in result.body))), result.body
        assert 'preload_resource' in result.body, result.body
        assert 'data-module="ngsipreview"' in result.body, result.body

    def test_css_included(self):
        res_id = self.resource['id']
        pack_id = self.package.name
        url = '/dataset/{0}/resource/{1}/preview'.format(pack_id, res_id)
        result = self.app.get(url, status='*')

        assert result.status == 200, result.status
        assert (('ngsi.css' in result.body)
                or ('ngsi.min.css' in result.body)), result.body
        assert (('github.css' in result.body)
                or ('github.min.css' in result.body)), result.body

    def test_iframe_is_shown(self):
        url = h.url_for(controller='package', action='resource_read',
                        id=self.package.name, resource_id=self.resource['id'])
        result = self.app.get(url)
        assert 'data-module="data-viewer"' in result.body
        assert '<iframe' in result.body
