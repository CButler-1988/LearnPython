from random import choice

from learnpython.app import pages
from learnpython.forms import FLOW_CHOICES

from .common import TEST_COMMENTS, TEST_EMAIL, TEST_MESSAGE, TEST_NAME, \
    TEST_PHONE, TEST_SUBJECT, TestCase


class TestViewsWithFlaskTesting(TestCase):

    def check_form_errors(self, url, collection):
        for data in collection:
            error = data.get('error', 'This field is required.')
            response = self.client.post(self.contacts_url, data=data)

            self.assert200(response)
            self.assertIn(
                'Cannot submit form! Please, fix errors below:', response.data
            )
            self.assertIn(error, response.data)

    def check_form_success(self, url, collection, subject):
        status_url = self.url('status', _external=True)

        for data in collection:
            subject = data.get('subject', subject)

            with self.mail.record_messages() as outbox:
                response = self.client.post(url, data=data)
                self.assertStatus(response, 302)
                self.assertTrue(
                    response.headers['Location'].startswith(status_url)
                )

                args = [data.pop('name'), data.pop('email')]
                data.pop('subject', None)
                args.extend(data.values())

                self.assertEqual(len(outbox), 1)
                self.check_message(outbox[0], subject, *args)

    def check_page(self, name, url):
        page = pages.get(name)
        self.assertIsNotNone(page)

        response = self.client.get(url)
        self.assert200(response)
        self.assertIn(u'<h2>{0}</h2>'.format(page['title']), response.udata)

    def test_about(self):
        self.check_page('about', self.about_url)

    def test_contacts(self):
        self.check_page('contacts', self.contacts_url)

        collection = (
            {},
            {'name': '', 'email': TEST_EMAIL, 'message': TEST_MESSAGE},
            {'name': TEST_NAME, 'email': '', 'message': TEST_MESSAGE},
            {'name': TEST_NAME, 'email': TEST_EMAIL, 'message': ''},
            {'name': TEST_NAME, 'email': TEST_NAME, 'message': TEST_MESSAGE,
             'error': 'Invalid email address.'},
        )
        self.check_form_errors(self.contacts_url, collection)

        collection = (
            {'name': TEST_NAME, 'email': TEST_EMAIL, 'message': TEST_MESSAGE},
            {'name': TEST_NAME, 'email': TEST_EMAIL, 'subject': TEST_SUBJECT,
             'message': TEST_MESSAGE}
        )
        self.check_form_success(self.contacts_url, collection, 'Feedback')

    def test_flows(self):
        flows = filter(lambda item: item[0].startswith('flows/'),
                       pages._pages.items())
        response = self.client.get(self.flows_url)
        self.assert200(response)

        for fullname, flow in flows:
            name = fullname.replace('flows/', '')
            self.assertIn('id="{0}"'.format(name), response.data)

    def test_index(self):
        response = self.client.get('/')
        self.assertRedirects(response, self.index_url)
        self.assertStatus(response, 301)

        self.check_page('index', self.index_url)

        urls = (self.contacts_url, self.flows_url + '#medium',
                self.flows_url + '#normal', self.flows_url + '#advanced',
                self.subscribe_url, self.index_url)

        response = self.client.get(self.index_url)
        self.assert200(response)

        for url in urls:
            self.assertIn('href="{0}"'.format(url), response.data)

    def test_static(self):
        url = self.url('static', filename='css/screen.css')
        response = self.client.get(url)
        self.assert200(response)

        url = self.url('static', filename='does_not_exists.exe')
        response = self.client.get(url)
        self.assert404(response)

    def test_subscribe(self):
        self.check_page('subscribe', self.subscribe_url)

        flow = choice(FLOW_CHOICES)[0]
        collection = (
            {},
            {'name': '', 'email': TEST_EMAIL, 'flow': flow},
            {'name': TEST_NAME, 'email': '', 'flow': flow},
            {'name': '', 'email': TEST_EMAIL, 'flow': ''},
            {'name': TEST_NAME, 'email': TEST_NAME, 'flow': '',
             'error': 'Invalid email address.'}
        )
        self.check_form_errors(self.subscribe_url, collection)

        collection = (
            {'name': TEST_NAME, 'email': TEST_EMAIL, 'flow': flow},
            {'name': TEST_NAME, 'email': TEST_EMAIL, 'phone': TEST_PHONE,
             'flow': flow, 'comments': TEST_COMMENTS}
        )
        self.check_form_success(self.subscribe_url, collection, 'Subscribe')