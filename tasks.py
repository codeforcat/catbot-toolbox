import json
import re
import uuid

import dialogflow_v2beta1 as dialogflow
from dialogflow_v2beta1.proto.session_pb2 import TextInput, QueryInput
from dialogflow_v2beta1.types import intent_pb2
from dialogflow_v2.gapic import enums
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct
from invoke import task


@task
def list_intent(c, project='catbot-test', display_name_regex='\0'):
    """
    Intentの一覧を取得します。 `--display-name-regex` オプションで結果を絞り込むことができますが、
    裏では全件取得しているので、IntentのIDが判明している場合は `get-intent` taskの利用を推奨します。
    下記の実行例で `name` の `intents/` 以降がIntentのIDです。

    Examples:
        $ invoke list-intent --display-name-regex '^sample$' | jq
        {
          "name": "projects/catbot-test/agent/intents/1c5e9b44-1822-4b7a-9e97-f00e789c0ff3",
          "displayName": "sample",
        ...
    """
    display_name_pattern = re.compile(display_name_regex)
    intents_client = dialogflow.IntentsClient()
    parent = intents_client.project_agent_path(project)
    for element in intents_client.list_intents(parent):
        if display_name_pattern.search(element.display_name):
            print(json.dumps(MessageToDict(element), ensure_ascii=False))


@task
def get_intent(c, project='catbot-test', intent_id='', intent_view=enums.IntentView.INTENT_VIEW_FULL):
    """Intent IDを指定してIntentを一件取得します。
    IntentのIDがわかっている場合は、 `list-intent` ではなくこちらを利用してください。

    Examples:
        $ pipenv run inv get-intent --intent-id 1c5e9b44-1822-4b7a-9e97-f00e789c0ff3 | jq
        {
          "name": "projects/catbot-test/agent/intents/1c5e9b44-1822-4b7a-9e97-f00e789c0ff3",
          "displayName": "sample",
          ...
    """
    intents_client = dialogflow.IntentsClient()
    name = intents_client.intent_path(project, intent_id)
    response = intents_client.get_intent(name, intent_view=intent_view)
    print(json.dumps(MessageToDict(response), ensure_ascii=False))


@task
def create_sample_intent(c, project='catbot-test'):
    """サンプルのIntentを作成します。

    Examples:
        $ pipenv run inv create-sample-intent | jq
        {
          "name": "projects/catbot-test/agent/intents/08be25b6-a5c3-4bd5-9387-76ccf12e548a",
          "displayName": "sample",
          ...
    """
    intents_client = dialogflow.IntentsClient()
    contexts_client = dialogflow.ContextsClient()

    training_phrases_parts = ['サンプルインテントを呼んで下さい']
    training_phrases = []
    for training_phrases_part in training_phrases_parts:
        part = intent_pb2.Intent.TrainingPhrase.Part(text=training_phrases_part, user_defined=True)
        training_phrase = intent_pb2.Intent.TrainingPhrase(
            parts=[part],
            type=enums.Intent.TrainingPhrase.Type.EXAMPLE
        )
        training_phrases.append(training_phrase)

    message_texts = ['これはサンプルインテントです']
    text = intent_pb2.Intent.Message.Text(text=message_texts)
    message = intent_pb2.Intent.Message(
        text=text,
        platform=enums.Intent.Message.Platform.LINE
    )

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
    message2 = dialogflow.types.intent_pb2.Intent.Message(
        payload=payload,
        platform=enums.Intent.Message.Platform.LINE,
    )

    context = dialogflow.types.context_pb2.Context(
        name=contexts_client.context_path(project=project, session='-', context='more_question'),
        lifespan_count=5,
    )

    display_name = 'sample'
    intent = intent_pb2.Intent(
        display_name=display_name,
        output_contexts=[context],
        training_phrases=training_phrases,
        messages=[message, message2],
    )

    parent = intents_client.project_agent_path(project)
    response = intents_client.create_intent(parent, intent)

    print(json.dumps(MessageToDict(response), ensure_ascii=False))


@task
def delete_intent(c, project='catbot-test', intent_id=''):
    """Intent IDを指定してIntentを一件削除します。

    Examples:
        $ pipenv run inv delete-intent --intent-id 1c5e9b44-1822-4b7a-9e97-f00e789c0ff3
    """
    intents_client = dialogflow.IntentsClient()
    name = intents_client.intent_path(project, intent_id)
    intents_client.delete_intent(name)


@task
def detect_intent(c, project='catbot-test', text=''):
    """入力テキストにマッチするIntentを検出します。

    Examples:
        $ pipenv run inv detect-intent --text 'サンプルインテント'
    """
    sessions_client = dialogflow.SessionsClient()
    session = sessions_client.session_path(project, uuid.uuid4())
    text_input = TextInput(text=text, language_code='ja-JP')
    query_input = QueryInput(text=text_input)
    response = sessions_client.detect_intent(session=session, query_input=query_input)
    print(json.dumps(MessageToDict(response), ensure_ascii=False))
