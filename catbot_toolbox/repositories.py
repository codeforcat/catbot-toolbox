import re
from typing import Any, Dict, List, Optional, Tuple, Union

import dialogflow_v2beta1 as dialogflow
import packaging.version
import yaml
from dialogflow_v2.gapic import enums
from dialogflow_v2beta1.proto.context_pb2 import Context
from dialogflow_v2beta1.proto.intent_pb2 import Intent
from google.api_core.page_iterator import GRPCIterator
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct

from . import __version__, FormatVersionError


class IntentRepository:
    PLATFORMS = [
        'PLATFORM_UNSPECIFIED',
        'FACEBOOK',
        'SLACK',
        'TELEGRAM',
        'KIK',
        'SKYPE',
        'LINE',
        'VIBER',
        'ACTIONS_ON_GOOGLE',
    ]

    MORE_QUESTION_PAYLOAD = {
        "type": "template",
        "altText": "もっと質問あるにゃ？",
        'template': {
            "type": "confirm",
            "text": "もっと質問あるにゃ？",
            "actions": [
                {
                    "type": "message",
                    "label": "はい",
                    "text": "はい",
                },
                {
                    "type": "message",
                    "label": "いいえ",
                    "text": "いいえ",
                },
            ],
        },
    }

    def __init__(self, project: str, platform: int = enums.Intent.Message.Platform.LINE):
        self.project = project
        self.platform = platform
        self.intents_client = dialogflow.IntentsClient()
        self.contexts_client = dialogflow.ContextsClient()

        payload = Struct()
        payload.update({self.PLATFORMS[self.platform].lower(): self.MORE_QUESTION_PAYLOAD})
        self.more_question_message = Intent.Message(
            payload=payload,
            platform=self.platform,
        )

        self.more_question_context = Context(
            name=self.contexts_client.context_path(
                project=self.project,
                session='-',
                context='more_question',
            ),
            lifespan_count=1,
        )

    @staticmethod
    def parse_intent_name(name: str) -> Tuple[Optional[str], Optional[str]]:
        matches = re.match('projects/(?P<project>[^/]+)/agent/intents/(?P<intent>[^/]+)', name)
        if matches:
            return matches['project'], matches['intent']
        else:
            return None, None

    def build_training_phrases(self, training_phrases: List[str]) -> List[Intent.TrainingPhrase]:
        _training_phrases = []
        for training_phrase in training_phrases:
            if isinstance(training_phrase, str):
                parts = [Intent.TrainingPhrase.Part(text=training_phrase, user_defined=True)]
            elif isinstance(training_phrase, dict) and 'parts' in training_phrase:
                parts = [
                    Intent.TrainingPhrase.Part(**part, user_defined=True)
                    for part in training_phrase['parts']
                ]
            elif isinstance(training_phrase, dict) and 'number' in training_phrase:
                parts = [
                    Intent.TrainingPhrase.Part(
                        text=str(training_phrase['number']),
                        entity_type='@sys.number',
                        alias='number',
                        user_defined=True,
                    )
                ]
            else:
                continue

            training_phrase = Intent.TrainingPhrase(
                parts=parts,
                type=enums.Intent.TrainingPhrase.Type.EXAMPLE,
            )
            _training_phrases.append(training_phrase)

        return _training_phrases

    def build_input_context_names(self, context_names: List[str]) -> List[Intent.TrainingPhrase]:
        _context_names = []
        for context_name in context_names:
            _context_name = self.contexts_client.context_path(
                project=self.project,
                session='-',
                context=context_name,
            )
            _context_names.append(_context_name)

        return _context_names

    def build_output_contexts(self, contexts: List[dict]) -> List[Intent.TrainingPhrase]:
        _contexts = []
        for context in contexts:
            _context = Context(
                name=self.contexts_client.context_path(
                    project=self.project,
                    session='-',
                    context=context['name'],
                ),
                lifespan_count=context['lifespan_count'] if 'lifespan_count' in context else 0
            )
            _contexts.append(_context)

        return _contexts

    def build_parameters(self, parameters: List[dict]) -> List[Intent.TrainingPhrase]:
        _parameters = []
        for parameter in parameters:
            if isinstance(parameter, str) and parameter == 'number':
                _parameters.append(Intent.Parameter(
                    display_name='number',
                    entity_type_display_name='@sys.number',
                    value='$number',
                ))
            else:
                _parameters.append(Intent.Parameter(**parameter))

        return _parameters

    def build_messages(self, payloads: List[Union[str, dict]]) -> List[Intent.Message]:
        messages = []
        for payload in payloads:
            if isinstance(payload, str):
                message = Intent.Message(
                    text=Intent.Message.Text(text=[payload.strip()]),
                    platform=self.platform,
                )
            elif isinstance(payload, list):
                message = Intent.Message(
                    text=Intent.Message.Text(text=[text.strip() for text in payload]),
                    platform=self.platform,
                )
            elif isinstance(payload, dict):
                payload_struct = Struct()
                if 'payload' in payload:
                    payload_struct.update({self.PLATFORMS[self.platform].lower(): payload['payload']})
                elif 'choice_buttons' in payload:
                    _payload = self.build_choice_buttons(payload['choice_buttons'])
                    payload_struct.update({self.PLATFORMS[self.platform].lower(): _payload})
                else:
                    payload_struct.update(payload)

                message = Intent.Message(
                    payload=payload_struct,
                    platform=self.platform,
                )
            else:
                raise AttributeError(f'Invalid payload "{payload}"')

            messages.append(message)

        return messages

    def build_choice_buttons(self, payload: dict) -> dict:
        _payload = {
            'type': 'template',
            'altText': payload['text'],
            'template': {
                'type': 'buttons',
                'text': payload['text'],
                'actions': [
                    {'type': 'message', 'label': l, 'text': i + 1} for i, l in enumerate(payload['buttons'])
                ]
            }
        }
        return _payload

    def build_intent(
        self,
        display_name: str,
        training_phrases: Optional[List[str]] = None,
        input_context_names: Optional[List[str]] = None,
        output_contexts: Optional[List[dict]] = None,
        parameters: Optional[List[dict]] = None,
        messages: Optional[List[Union[str, dict]]] = None,
        events: Optional[List[str]] = None,
        webhook_state: Optional[str] = None,
        is_fallback: Optional[bool] = None,
        more_question: bool = False,
    ) -> Intent:
        _training_phrases = self.build_training_phrases(training_phrases if training_phrases else [])
        _input_context_names = self.build_input_context_names(input_context_names if input_context_names else [])
        _output_contexts = self.build_output_contexts(output_contexts if output_contexts else [])
        _parameters = self.build_parameters(parameters if parameters else [])
        _messages = self.build_messages(messages if messages else [])
        _events = events if events is not None else [display_name]

        params: Dict[str, Any] = {
            'display_name': display_name,
            'training_phrases': _training_phrases,
            'input_context_names': _input_context_names,
            'output_contexts': _output_contexts,
            'parameters': _parameters,
            'messages': _messages,
            'events': _events,
            'webhook_state': webhook_state,
            'is_fallback': is_fallback,
        }
        if more_question:
            params['output_contexts'].append(self.more_question_context)
            params['messages'].append(self.more_question_message)

        intent = Intent(**params)

        return intent

    def list(self, intent_view: int = enums.IntentView.INTENT_VIEW_FULL) -> GRPCIterator:
        parent = self.intents_client.project_agent_path(self.project)
        intents = self.intents_client.list_intents(parent, intent_view=intent_view)
        return intents

    def list_all(self, intent_view: int = enums.IntentView.INTENT_VIEW_FULL) -> List[dict]:
        intents = [MessageToDict(intent, preserving_proto_field_name=True) for intent in self.list(intent_view)]
        return intents

    def find_by_display_name(
        self,
        display_name: str,
        intent_list: Optional[List[dict]] = None,
    ) -> Optional[dict]:
        if intent_list:
            for intent_dict in intent_list:
                if intent_dict['display_name'] == display_name:
                    return intent_dict
        else:
            for page in self.list().pages:
                for intent in page:
                    if intent.display_name == display_name:
                        return MessageToDict(intent, preserving_proto_field_name=True)

        return None

    def get(self, id: str, intent_view: int = enums.IntentView.INTENT_VIEW_FULL) -> dict:
        name = self.intents_client.intent_path(self.project, id)
        response = self.intents_client.get_intent(name, intent_view=intent_view)
        return MessageToDict(response, preserving_proto_field_name=True)

    def create(
        self,
        display_name: str,
        training_phrases: Optional[List[str]] = None,
        input_context_names: Optional[List[str]] = None,
        output_contexts: Optional[List[dict]] = None,
        parameters: Optional[List[dict]] = None,
        messages: Optional[List[Union[str, dict]]] = None,
        events: Optional[List[str]] = None,
        webhook_state: Optional[str] = None,
        is_fallback: Optional[bool] = None,
        more_question: bool = False,
        intent_view: int = enums.IntentView.INTENT_VIEW_FULL,
    ) -> dict:
        intent = self.build_intent(
            display_name,
            training_phrases,
            input_context_names,
            output_contexts,
            parameters,
            messages,
            events,
            webhook_state,
            is_fallback,
            more_question,
        )
        parent = self.intents_client.project_agent_path(self.project)
        response = self.intents_client.create_intent(parent, intent, intent_view=intent_view)
        return MessageToDict(response, preserving_proto_field_name=True)

    def update(
        self,
        id: str,
        display_name: str,
        training_phrases: Optional[List[str]] = None,
        input_context_names: Optional[List[str]] = None,
        output_contexts: Optional[List[dict]] = None,
        parameters: Optional[List[dict]] = None,
        messages: Optional[List[Union[str, dict]]] = None,
        events: Optional[List[str]] = None,
        webhook_state: Optional[str] = None,
        is_fallback: Optional[bool] = None,
        more_question: bool = False,
        intent_view: int = enums.IntentView.INTENT_VIEW_FULL,
    ) -> dict:
        intent = self.build_intent(
            display_name,
            training_phrases,
            input_context_names,
            output_contexts,
            parameters,
            messages,
            events,
            webhook_state,
            is_fallback,
            more_question,
        )
        intent.name = self.intents_client.intent_path(self.project, id)
        response = self.intents_client.update_intent(intent, language_code='', intent_view=intent_view)
        return MessageToDict(response, preserving_proto_field_name=True)

    def upsert(
        self,
        display_name: str,
        training_phrases: Optional[List[str]] = None,
        input_context_names: Optional[List[str]] = None,
        output_contexts: Optional[List[dict]] = None,
        parameters: Optional[List[dict]] = None,
        messages: Optional[List[Union[str, dict]]] = None,
        events: Optional[List[str]] = None,
        webhook_state: Optional[str] = None,
        is_fallback: Optional[bool] = None,
        more_question: bool = False,
        intent_view: int = enums.IntentView.INTENT_VIEW_FULL,
        intent_list: Optional[List[dict]] = None,
    ) -> dict:
        """
        Intentのupsertを行う。

        `project` と `display_name` が一致するIntentがあればupdate、なければcreateを実行します。
        `intent_list` 引数にIntentの一覧を渡すことで、毎回Intentを走査するのを防ぐことができます。
        """
        current_intent = self.find_by_display_name(display_name, intent_list)
        project, intent_id = self.parse_intent_name(current_intent['name'] if current_intent else '')

        params = {
            'display_name': display_name,
            'training_phrases': training_phrases,
            'input_context_names': input_context_names,
            'output_contexts': output_contexts,
            'parameters': parameters,
            'messages': messages,
            'events': events,
            'webhook_state': webhook_state,
            'is_fallback': is_fallback,
            'more_question': more_question,
            'intent_view': intent_view,
        }
        if intent_id:
            intent = self.update(intent_id, **params)  # type: ignore
        else:
            intent = self.create(**params)  # type: ignore

        return intent

    def load(self, file: str) -> dict:
        with open(file) as f:
            data = yaml.full_load(f)
            version = data.get('version', __version__)
            intents = data['intents']

        if packaging.version.parse(version) > packaging.version.parse(__version__):
            raise FormatVersionError(f'Invalid data format version {version}')

        intent_list = self.list_all()
        result: dict = {'intents': []}
        intents = self.resolve_all(intents, intent_list=intent_list)
        for intent_params in intents:
            intent = self.upsert(intent_list=intent_list, **intent_params)
            result['intents'].append(intent)

        return result

    def delete(self, id: str) -> None:
        name = self.intents_client.intent_path(self.project, id)
        self.intents_client.delete_intent(name)

    def resolve_all(self, intents: List[dict], intent_list: Optional[List[dict]] = None) -> List:
        """インテントのリストに対して%pathなどのカスタムフィールドを解決します。"""
        if intent_list is None:
            intent_list = self.list_all()
        return [self.resolve(i, intents + intent_list) for i in intents]

    def resolve(self, branch: Union[List, dict, str], intent_list: List[dict]) -> Union[List, dict, str]:
        """インテントに対してphrase_fromなどのカスタムフィールドを解決します。"""
        if isinstance(branch, str) and branch.startswith('%'):
            return self.resolve_path(branch.lstrip('%'), intent_list)
        elif isinstance(branch, list):
            return [self.resolve(sub, intent_list) for sub in branch]
        elif isinstance(branch, dict):
            return {k: self.resolve(sub, intent_list) for k, sub in branch.items()}
        else:
            return branch

    def resolve_path(self, path: str, intent_list: List[dict]) -> Any:
        keys = path.split('.')
        display_name = keys.pop(0)
        matches = filter(lambda i: 'display_name' in i and i['display_name'] == display_name, intent_list)

        def traverse(branch: Any, _keys: List) -> Any:
            if not _keys:
                return branch
            try:
                if isinstance(branch, dict):
                    return traverse(branch[_keys[0]], _keys[1:])
                elif isinstance(branch, list):
                    return traverse(branch[int(_keys[0])], _keys[1:])
                else:
                    return None
            except (KeyError, IndexError, ValueError):
                return None

        for intent in matches:
            value = traverse(intent, keys)
            if value is not None:
                return value

        return None
