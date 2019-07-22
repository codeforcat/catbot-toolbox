import unittest
import uuid

from catbot_toolbox.repositories import IntentRepository


class IntentRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.project = 'catbot-test'
        self.create_params = {
            'display_name': f'test_{uuid.uuid4()}',
            'training_phrases': ['これはcreateのテストですか'],
            'messages': ['これはcreateのテストです'],
        }
        self.update_params = {
            'display_name': f'test_{uuid.uuid4()}',
            'training_phrases': ['これはupdateのテストですか'],
            'messages': ['これはupdateのテストです'],
        }

    def assert_intent(self, intent, params):
        self.assertEqual(params['display_name'], intent['display_name'])
        self.assertEqual(
            params['training_phrases'][0],
            intent['training_phrases'][0]['parts'][0]['text'],
        )
        self.assertEqual(
            params['messages'][0],
            intent['messages'][0]['text']['text'][0],
        )
        if params.get('more_question', False):
            self.assertEqual(
                IntentRepository.MORE_QUESTION_PAYLOAD,
                intent['messages'][1]['payload'],
            )

    def test_create_and_update_intent(self):
        repos = IntentRepository(self.project)
        id = ''
        try:
            created_intent = repos.create(**self.create_params)
            project, id = repos.parse_intent_name(created_intent['name'])

            updated_intent = repos.update(id=id, **self.update_params)

            self.assertEqual(self.project, project)
            self.assert_intent(created_intent, self.create_params)
            self.assert_intent(updated_intent, self.update_params)
        finally:
            if id:
                repos.delete(id)

    def test_upsert_intent(self):
        repos = IntentRepository(self.project)
        id = ''
        try:
            created_intent = repos.upsert(**self.create_params)
            updated_intent = repos.upsert(**self.update_params)
            project, id = repos.parse_intent_name(created_intent['name'])

            self.assert_intent(created_intent, self.create_params)
            self.assert_intent(updated_intent, self.update_params)
        finally:
            if id:
                repos.delete(id)

    def test_create_which_has_more_question(self):
        repos = IntentRepository(self.project)
        create_params = {**self.create_params, 'more_question': True}
        id = ''
        try:
            created_intent = repos.create(**create_params)
            project, id = repos.parse_intent_name(created_intent['name'])

            self.assert_intent(created_intent, create_params)
        finally:
            if id:
                repos.delete(id)
