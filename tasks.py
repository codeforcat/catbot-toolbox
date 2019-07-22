import json
import os
import re
import sys
import uuid

import dialogflow_v2beta1 as dialogflow
import yaml
from dialogflow_v2beta1.proto.session_pb2 import TextInput, QueryInput
from dialogflow_v2.gapic import enums
from google.protobuf.json_format import MessageToDict
from invoke import task

from catbot_toolbox.repositories import IntentRepository


@task
def list_intent(c, project='catbot-test', display_name_regex='.*'):
    """Intentの一覧を取得します。
    `--display-name-regex` オプションで結果を絞り込むことができますが、
    裏では全件取得しているので、IntentのIDが判明している場合は `get-intent` taskの利用を推奨します。
    下記の実行例で `name` の `intents/` 以降がIntentのIDです。

    Examples:
        $ invoke list-intent --display-name-regex '^sample$' | jq
        {
          "name": "projects/catbot-test/agent/intents/1c5e9b44-1822-4b7a-9e97-f00e789c0ff3",
          "displayName": "sample",
        ...
    """
    repos = IntentRepository(project)
    display_name_pattern = re.compile(display_name_regex)
    for intent in repos.list():
        if display_name_pattern.search(intent['display_name']):
            print(json.dumps(intent, ensure_ascii=False))


@task
def get_intent(c, intent_id, project='catbot-test', intent_view=enums.IntentView.INTENT_VIEW_FULL):
    """Intent IDを指定してIntentを一件取得します。
    IntentのIDがわかっている場合は、 `list-intent` ではなくこちらを利用してください。

    Examples:
        $ pipenv run inv get-intent --intent-id 1c5e9b44-1822-4b7a-9e97-f00e789c0ff3 | jq
        {
          "name": "projects/catbot-test/agent/intents/1c5e9b44-1822-4b7a-9e97-f00e789c0ff3",
          "displayName": "sample",
          ...
    """
    repos = IntentRepository(project)
    intent = repos.get(intent_id)
    print(json.dumps(intent, ensure_ascii=False))


@task
def create_sample_intent(c):
    """サンプルのIntentを作成します。

    Examples:
        $ pipenv run inv create-sample-intent | jq
        {
          "name": "projects/catbot-test/agent/intents/08be25b6-a5c3-4bd5-9387-76ccf12e548a",
          "displayName": "sample",
          ...
    """
    with open(os.path.join(os.path.dirname(__file__), 'examples', 'create_sample.yml')) as f:
        data = yaml.full_load(f)
        project = data['project']
        intents = data['intents']

    repos = IntentRepository(project)
    for display_name, intent_dict in intents.items():
        intent = repos.create(display_name=display_name, **intent_dict)
        print(json.dumps(intent, ensure_ascii=False))


@task
def update_sample_intent(c):
    """サンプルのIntentを更新します。

    Examples:
        $ pipenv run inv update-sample-intent | jq
        {
          "name": "projects/catbot-test/agent/intents/08be25b6-a5c3-4bd5-9387-76ccf12e548a",
          "displayName": "sample",
          ...
    """
    with open(os.path.join(os.path.dirname(__file__), 'examples', 'update_sample.yml')) as f:
        data = yaml.full_load(f)
        project = data['project']
        intents = data['intents']

    repos = IntentRepository(project)
    for display_name, intent_dict in intents.items():
        intent = repos.update(display_name=display_name, **intent_dict)
        print(json.dumps(intent, ensure_ascii=False))


@task
def update_sample_intent(c):
    """サンプルのIntentを更新します。

    Examples:
        $ pipenv run inv update-sample-intent | jq
        {
          "name": "projects/catbot-test/agent/intents/08be25b6-a5c3-4bd5-9387-76ccf12e548a",
          "displayName": "sample",
          ...
    """
    with open(os.path.join(os.path.dirname(__file__), 'examples', 'update_sample.yml')) as f:
        data = yaml.full_load(f)
        project = data['project']
        intents = data['intents']

    repos = IntentRepository(project)
    for display_name, intent_dict in intents.items():
        intent = repos.update(display_name=display_name, **intent_dict)
        print(json.dumps(intent, ensure_ascii=False))


@task
def upsert_sample_intent(c):
    """サンプルのIntentを更新もしくは作成します。

    Examples:
        $ pipenv run inv upsert-sample-intent | jq
        {
          "name": "projects/catbot-test/agent/intents/08be25b6-a5c3-4bd5-9387-76ccf12e548a",
          "displayName": "sample",
          ...
    """
    with open(os.path.join(os.path.dirname(__file__), 'examples', 'create_sample.yml')) as f:
        data = yaml.full_load(f)
        project = data['project']
        intents = data['intents']

    repos = IntentRepository(project)
    intent_list = repos.list()
    for display_name, intent_dict in intents.items():
        intent = repos.upsert(display_name=display_name, intent_list=intent_list, **intent_dict)
        print(json.dumps(intent, ensure_ascii=False))


@task
def delete_intent(c, intent_id, project='catbot-test'):
    """Intent IDを指定してIntentを一件削除します。

    Examples:
        $ pipenv run inv delete-intent --intent-id 1c5e9b44-1822-4b7a-9e97-f00e789c0ff3
    """
    repos = IntentRepository(project)
    repos.delete(intent_id)


@task
def detect_intent(c, text, project='catbot-test'):
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


@task
def yaml2json(c, file):
    """YAML形式のファイルを読み込み、JSON形式で出力します。

    Examples:
        $ pipenv run inv yaml2json -f sample.yml | jq
    """
    with open(file) as f:
        print(json.dumps(yaml.full_load(f), ensure_ascii=False))


@task
def json2yaml(c, file):
    """JSON形式のファイルを読み込み、YAML形式で出力します。

    Examples:
        $ pipenv run inv json2yaml -f sample.json
    """
    with open(file) as f:
        yaml.dump(json.load(f), sys.stdout, allow_unicode=True)
