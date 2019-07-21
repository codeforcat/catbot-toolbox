from typing import Union

import dialogflow_v2beta1 as dialogflow
from dialogflow_v2beta1.proto import intent_pb2
from dialogflow_v2.gapic import enums
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct


class IntentRepository:
    def __init__(self, project):
        self.project = project
        self.platform = enums.Intent.Message.Platform.LINE
        self.intents_client = dialogflow.IntentsClient()
        self.contexts_client = dialogflow.ContextsClient()

        payload = Struct()
        payload.update({
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
        })
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

    def build_training_phrases(self, texts: [str]):
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

    def build_messages(self, payloads: [Union[str, dict]]):
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

    def list_intent(self):
        parent = self.intents_client.project_agent_path(self.project)
        intents = [MessageToDict(intent) for intent in self.intents_client.list_intents(parent)]
        return intents

    def get(self, id, intent_view=enums.IntentView.INTENT_VIEW_FULL):
        name = self.intents_client.intent_path(self.project, id)
        response = self.intents_client.get_intent(name, intent_view=intent_view)
        return MessageToDict(response)

    def create(self, display_name, training_phrases, messages, more_question=False):
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

        parent = self.intents_client.project_agent_path(self.project)
        response = self.intents_client.create_intent(parent, intent)

        return MessageToDict(response)

    def delete(self, id):
        name = self.intents_client.intent_path(self.project, id)
        self.intents_client.delete_intent(name)
