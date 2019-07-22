import os
import unittest
import uuid

import yaml

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
        created_id = ''
        try:
            created_intent = repos.create(**self.create_params)
            created_project, created_id = repos.parse_intent_name(created_intent['name'])

            updated_intent = repos.update(id=created_id, **self.update_params)
            updated_project, updated_id = repos.parse_intent_name(updated_intent['name'])

            self.assertEqual(self.project, created_project)
            self.assertEqual(self.project, updated_project)
            self.assertEqual(created_id, updated_id)
            self.assert_intent(created_intent, self.create_params)
            self.assert_intent(updated_intent, self.update_params)
        finally:
            if created_id:
                repos.delete(created_id)

    def test_upsert_intent(self):
        repos = IntentRepository(self.project)
        created_id = ''
        try:
            created_intent = repos.upsert(**self.create_params)
            created_project, created_id = repos.parse_intent_name(created_intent['name'])

            update_params = {**self.update_params, 'display_name': self.create_params['display_name']}
            updated_intent = repos.upsert(**update_params)
            updated_project, updated_id = repos.parse_intent_name(updated_intent['name'])

            self.assertEqual(self.project, created_project)
            self.assertEqual(self.project, updated_project)
            self.assertEqual(created_id, updated_id)
            self.assert_intent(created_intent, self.create_params)
            self.assert_intent(updated_intent, update_params)
        finally:
            if created_id:
                repos.delete(created_id)

    def test_create_which_has_more_question(self):
        repos = IntentRepository(self.project)
        create_params = {**self.create_params, 'more_question': True}
        id = ''
        try:
            intent = repos.create(**create_params)
            project, id = repos.parse_intent_name(intent['name'])

            self.assertEqual(self.project, project)
            self.assert_intent(intent, create_params)
        finally:
            if id:
                repos.delete(id)

    def test_load(self):
        file = os.path.join(os.path.dirname(__file__), 'examples', 'sample.yml')

        with open(file) as f:
            data = yaml.full_load(f)

        repos = IntentRepository(self.project)
        result = None
        try:
            result = repos.load(file)
            self.assertEqual(data['project'], result['project'])
            for i, intent_params in enumerate(data['intents']):
                self.assert_intent(result['intents'][i], intent_params)
        finally:
            if result:
                for intent in result['intents']:
                    project, id = repos.parse_intent_name(intent['name'])
                    repos.delete(id)


if __name__ == '__main__':
    unittest.main()
