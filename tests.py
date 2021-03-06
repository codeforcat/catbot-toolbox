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
        self.assert_display_name(intent, params)
        self.assert_training_phrases(intent, params)
        self.assert_input_context_names(intent, params)
        self.assert_output_contexts(intent, params)
        self.assert_parameters(intent, params)
        self.assert_messages(intent, params)
        self.assert_events(intent, params)
        self.assert_webhook_state(intent, params)
        self.assert_more_question(intent, params)

    def assert_display_name(self, intent, params):
        self.assertEqual(params['display_name'], intent['display_name'])

    def assert_training_phrases(self, intent, params):
        if 'training_phrases' not in params:
            return

        for i, training_phrase in enumerate(params['training_phrases']):
            if isinstance(training_phrase, str):
                self.assertEqual(training_phrase, intent['training_phrases'][i]['parts'][0]['text'])
            elif isinstance(training_phrase, dict) and 'parts' in training_phrase:
                for j, part in enumerate(training_phrase['parts']):
                    self.assertEqual({**part, 'user_defined': True}, intent['training_phrases'][i]['parts'][j])
            else:
                continue

    def assert_input_context_names(self, intent, params):
        if 'input_context_names' not in params:
            return

        for i, context_name in enumerate(params['input_context_names']):
            self.assertEqual(context_name, os.path.basename(intent['input_context_names'][i]))

    def assert_output_contexts(self, intent, params):
        if 'output_contexts' not in params:
            return

        for i, context in enumerate(params['output_contexts']):
            self.assertEqual(context['name'], os.path.basename(intent['output_contexts'][i]['name']))
            if 'lifespan_count' in context:
                self.assertEqual(
                    context['lifespan_count'],
                    intent['output_contexts'][i]['lifespan_count'],
                )

    def assert_parameters(self, intent, params):
        if 'parameters' not in params:
            return

        for i, parameter in enumerate(params['parameters']):
            if isinstance(parameter, str) and 'number' in parameter:
                continue
            _parameter = {k: v for k, v in intent['parameters'][i].items() if k not in ['name']}
            self.assertTrue(parameter, _parameter)

    def assert_messages(self, intent, params):
        if 'messages' not in params:
            return

        for i, message in enumerate(params['messages']):
            if isinstance(message, str):
                self.assertEqual(message, intent['messages'][i]['text']['text'][0])
            elif isinstance(message, dict):
                if 'payload' in message:
                    self.assertEqual(message['payload'], intent['messages'][i]['payload']['line'])
                elif 'choice_buttons' in message:
                    pass
                else:
                    self.assertEqual(message, intent['messages'][i]['payload'])

    def assert_events(self, intent, params):
        if 'events' in params:
            self.assertEqual(params['events'], intent['events'])
        else:
            self.assertEqual([params['display_name']], intent['events'])

    def assert_webhook_state(self, intent, params):
        if 'webhook_state' not in params:
            return

        self.assertEqual(params['webhook_state'], intent['webhook_state'])

    def assert_more_question(self, intent, params):
        if not params.get('more_question', False):
            return

        self.assertEqual(
            {'line': IntentRepository.MORE_QUESTION_PAYLOAD},
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
        file = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample.yml')

        with open(file) as f:
            data = yaml.full_load(f)

        repos = IntentRepository(self.project)
        result = None
        try:
            result = repos.load(file)
            # expectationとしてresolve_allを通した後のintentsを取得する
            intents = repos.resolve_all(data['intents'], [])
            for i, intent_params in enumerate(intents):
                self.assert_intent(result['intents'][i], intent_params)
        finally:
            if result:
                for intent in result['intents']:
                    project, id = repos.parse_intent_name(intent['name'])
                    repos.delete(id)

    def test_resolve_all(self):
        file = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample.yml')

        with open(file) as f:
            data = yaml.full_load(f)
            intents = data['intents']

        repos = IntentRepository(self.project)
        result = repos.resolve_all(intents, [])
        self.assertEqual(
            intents[2]['training_phrases'][0],
            result[1]['messages'][0]['payload']['template']['columns'][0]['actions'][0]['text'],
        )


if __name__ == '__main__':
    unittest.main()
