import json
import re
import sys
import uuid

import dialogflow_v2beta1 as dialogflow
import yaml
from dialogflow_v2.gapic import enums
from dialogflow_v2beta1.proto.session_pb2 import QueryInput, TextInput
from google.protobuf.json_format import MessageToDict
from invoke import task

from catbot_toolbox.repositories import IntentRepository


@task
def list_intents(c, project='catbot-test', display_name_regex='.*'):
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
    for intent in repos.list_all():
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
def delete_intents(c, intent_id='', display_name_regex='', project='catbot-test'):
    """Intent IDを指定してIntentを一件削除します。

    Examples:
        $ pipenv run inv delete-intents --intent-id 1c5e9b44-1822-4b7a-9e97-f00e789c0ff3
        $ pipenv run inv delete-intents --display-name-regex '^test_'
    """
    if intent_id:
        repos = IntentRepository(project)
        repos.delete(intent_id)
    elif display_name_regex:
        repos = IntentRepository(project)
        display_name_pattern = re.compile(display_name_regex)
        for intent in repos.list_all():
            if display_name_pattern.search(intent['display_name']):
                _, _id = repos.parse_intent_name(intent['name'])
                repos.delete(_id)


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
def load_intents(c, file, project='catbot-test'):
    """YAMLファイルからIntentをロードします。

    Examples:
        $ pipenv run inv load-intents --file fixtures/sample.yml
    """
    repos = IntentRepository(project)
    response = repos.load(file)
    print(json.dumps(response, ensure_ascii=False))


@task
def yaml2json(c, file):
    """YAML形式のファイルを読み込み、JSON形式で出力します。

    Examples:
        $ pipenv run inv yaml2json -f fixtures/sample.yml | jq
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


@task
def coverage_report(c):
    """コンソールへカバレッジレポートを出力します。"""
    c.run('coverage report -m')


@task
def coverage_html(c):
    """HTML形式のカバレッジレポートを出力します。"""
    c.run('coverage html')


@task
def unittest(c):
    """ユニットテストを実施します。"""
    c.run('coverage run --source="." tests.py')


@task(pre=[unittest, coverage_report, coverage_html])
def test(c):
    """テストに関するタスクを実施します。"""
    pass


@task
def isort(c):
    """import文の最適化を実施します。"""
    c.run('isort -rc .')


@task(pre=[isort])
def flake8(c):
    """コードフォーマットチェックを実施します。"""
    c.run('flake8')


@task
def mypy(c):
    """型アノテーションのチェックを実施します。"""
    c.run('mypy .')


@task(pre=[isort, flake8, mypy])
def lint(c):
    """コードフォーマッティングに関するタスクを実行します。"""
    pass


@task
def radon_cc(c):
    """循環的複雑度(Cyclomatic Complexity)を算出します。"""
    c.run('radon cc -s -a -e tasks.py -i fixtures .')


@task
def radon_mi(c):
    """保守性指数(Maintainability Index)を算出します。"""
    c.run('radon mi -s -e tasks.py -i fixtures .')


@task
def xenon(c):
    """コード複雑度の検査をします。"""
    c.run('xenon --max-absolute B --max-modules A --max-average A .')


@task(pre=[radon_cc, radon_mi])
def metrics(c):
    """コードメトリクスに関するタスクを実行します。"""
    pass


@task(pre=[lint, metrics, test])
def ci(c):
    """CI関連タスクを実行します。"""
    pass
