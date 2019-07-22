import re
from typing import Union, Optional, List, Any

import dialogflow_v2beta1 as dialogflow
from dialogflow_v2beta1.proto import intent_pb2
from dialogflow_v2.gapic import enums
from google.api_core.page_iterator import GRPCIterator
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct


class IntentRepository:
    MORE_QUESTION_PAYLOAD = {
        'line': {
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
        },
    }

    def __init__(self, project: str):
        self.project = project
        self.platform = enums.Intent.Message.Platform.LINE
        self.intents_client = dialogflow.IntentsClient()
        self.contexts_client = dialogflow.ContextsClient()

        payload = Struct()
        payload.update(self.MORE_QUESTION_PAYLOAD)
        self.more_question_message = dialogflow.types.intent_pb2.Intent.Message(
            payload=payload,
            platform=self.platform,
        )

        self.more_question_context = dialogflow.types.context_pb2.Context(
            name=self.contexts_client.context_path(
                project=self.project,
                session='-',
                context='more_question',
            ),
            lifespan_count=5,
        )

    @staticmethod
    def parse_intent_name(name: str) -> (Optional[str], Optional[str]):
        matches = re.match('projects/(?P<project>[^/]+)/agent/intents/(?P<intent>[^/]+)', name)
        if matches:
            return matches['project'], matches['intent']
        else:
            return None, None

    def build_training_phrases(self, texts: [str]) -> [intent_pb2.Intent.TrainingPhrase]:
        training_phrases = []
        for text in texts:
            part = intent_pb2.Intent.TrainingPhrase.Part(
                text=text,
                user_defined=True,
            )
            training_phrase = intent_pb2.Intent.TrainingPhrase(
                parts=[part],
                type=enums.Intent.TrainingPhrase.Type.EXAMPLE,
            )
            training_phrases.append(training_phrase)

        return training_phrases

    def build_messages(self, payloads: [Union[str, dict]]) -> [intent_pb2.Intent.Message]:
        messages = []
        for payload in payloads:
            if isinstance(payload, str):
                message = intent_pb2.Intent.Message(
                    text=intent_pb2.Intent.Message.Text(text=[payload]),
                    platform=self.platform,
                )
            elif isinstance(payload, list):
                message = intent_pb2.Intent.Message(
                    text=intent_pb2.Intent.Message.Text(text=payload),
                    platform=self.platform,
                )
            elif isinstance(payload, dict):
                payload_struct = Struct()
                payload_struct.update(payload)
                message = intent_pb2.Intent.Message(
                    payload=payload,
                    platform=self.platform,
                )
            else:
                raise AttributeError(f'Invalid payload "{payload}"')

            messages.append(message)

        return messages

    def build_intent(
        self,
        display_name: str,
        training_phrases: [str],
        messages: [Union[str, dict]],
        more_question=False
    ) -> intent_pb2.Intent:
        _training_phrases = self.build_training_phrases(training_phrases)
        _messages = self.build_messages(messages)

        if more_question:
            intent = intent_pb2.Intent(
                display_name=display_name,
                output_contexts=[self.more_question_context],
                training_phrases=_training_phrases,
                messages=[*_messages, self.more_question_message],
            )
        else:
            intent = intent_pb2.Intent(
                display_name=display_name,
                training_phrases=_training_phrases,
                messages=_messages,
            )

        return intent

    def list(
        self,
        as_dict=True,
        intent_view=enums.IntentView.INTENT_VIEW_FULL,
    ) -> Union[List[dict], GRPCIterator]:
        parent = self.intents_client.project_agent_path(self.project)
        intents = self.intents_client.list_intents(parent, intent_view=intent_view)
        if as_dict:
            intents = [MessageToDict(intent, preserving_proto_field_name=True) for intent in intents]

        return intents

    def find_by_display_name(
        self,
        display_name: str,
        intent_list: Optional[List[dict]]=None,
    ) -> Optional[dict]:
        if intent_list:
            for intent in intent_list:
                if intent['display_name'] == display_name:
                    return intent
        else:
            for page in self.list(as_dict=False).pages:
                for intent in page:
                    if intent.display_name == display_name:
                        return MessageToDict(intent, preserving_proto_field_name=True)

        return None

    def get(self, id: str, intent_view=enums.IntentView.INTENT_VIEW_FULL) -> dict:
        name = self.intents_client.intent_path(self.project, id)
        response = self.intents_client.get_intent(name, intent_view=intent_view)
        return MessageToDict(response, preserving_proto_field_name=True)

    def create(
        self,
        display_name: str,
        training_phrases: [str],
        messages: [Union[str, dict]],
        more_question=False,
        intent_view=enums.IntentView.INTENT_VIEW_FULL,
    ) -> dict:
        intent = self.build_intent(display_name, training_phrases, messages, more_question)
        parent = self.intents_client.project_agent_path(self.project)
        response = self.intents_client.create_intent(parent, intent, intent_view=intent_view)
        return MessageToDict(response, preserving_proto_field_name=True)

    def update(
        self,
        id: str,
        display_name: str,
        training_phrases: [str],
        messages: [Union[str, dict]],
        more_question=False,
        intent_view=enums.IntentView.INTENT_VIEW_FULL,
    ) -> dict:
        intent = self.build_intent(display_name, training_phrases, messages, more_question)
        intent.name = self.intents_client.intent_path(self.project, id)
        response = self.intents_client.update_intent(intent, language_code='', intent_view=intent_view)
        return MessageToDict(response, preserving_proto_field_name=True)

    def upsert(
        self,
        display_name: str,
        training_phrases: [str],
        messages: [Union[str, dict]],
        more_question=False,
        intent_view=enums.IntentView.INTENT_VIEW_FULL,
        intent_list: [dict]=None,
    ) -> dict:
        """`Intentのupsertを行う。
        `project` と `display_name` が一致するIntentがあればupdate、なければcreateを実行します。
        `intent_list` 引数にIntentの一覧を渡すことで、毎回Intentを走査するのを防ぐことができます。
        """
        current_intent = self.find_by_display_name(display_name, intent_list)
        if current_intent:
            project, id = self.parse_intent_name(current_intent['name'])
        else:
            project, id = None, None

        if not project or project != self.project:
            intent = self.create(display_name, training_phrases, messages, more_question)
        else:
            intent = self.update(id, display_name, training_phrases, messages, more_question, intent_view)

        return intent

    def delete(self, id: str):
        name = self.intents_client.intent_path(self.project, id)
        self.intents_client.delete_intent(name)