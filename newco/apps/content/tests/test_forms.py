import json
from django.conf import settings
from django.utils import unittest
from django.test.client import RequestFactory, Client
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, AnonymousUser
from ..models import Item
from ..forms import ItemForm, DictionaryField
from ..views import ContentCreateView, ContentDeleteView, ContentDetailView


class SimpleTest(unittest.TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()
        self.request = self.factory.get('/')
        self.request.user = AnonymousUser()
        self.views = [ContentCreateView, ContentDeleteView, ContentDetailView]

    def test_redirect_anon(self):
        '''
        Content: AnonymousUser is redirected
        '''
        for view in self.views:
            response = view().dispatch(self.request)
            self.assertEqual(response.status_code, 302)
            assert settings.LOGIN_URL in response._headers['location'][1]

    def test_non_staff_fordidden(self):
        '''
        Content: non staff user is fordidden
        '''
        request = self.request
        request.user = User()
        for view in self.views:
            self.assertRaises(PermissionDenied, view().dispatch, request)

    def test_dictionary_field(self):
        '''
        Content: test dictionary field
        '''
        form = ItemForm(request=self.request, initial=Item.initial)
        field = form.declared_fields['data']
        widget = field.widget
        context = {}
        self.assertEqual(widget.render('data', context),
                         widget.base_template.format(''))
        data = {"VENEZUELA": "CARACAS", "CANADA": "TORONTO"}
        self.assertEqual(field.clean(json.dumps(data)), json.loads(json.dumps(data)))
