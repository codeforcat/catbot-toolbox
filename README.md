catbot-toolbox
==============


Links
-----

- [Python Client Library  |  Dialogflow Documentation  |  Google Cloud](https://cloud.google.com/dialogflow/docs/reference/libraries/python)
- [GitHub - googleapis/dialogflow-python-client-v2](https://github.com/googleapis/dialogflow-python-client-v2)
- [Dialogflow: Python Client — dialogflow 0.1.0 documentation](https://dialogflow-python-client-v2.readthedocs.io/en/latest/)


Requirements
------------

- [Pipenv: 人間のためのPython開発ワークフロー](https://pipenv-ja.readthedocs.io/ja/translate-ja/)
- [gcloud コマンドライン ツールの概要  |  Cloud SDK のドキュメント  |  Google Cloud](https://cloud.google.com/sdk/gcloud/)


Setup
-----

パッケージ依存関係インストール

```
$ pipenv install --dev
```

gcloud でのプロジェクト設定


```
gcloud config configurations create catbot-test

gcloud auth login
gcloud config set project catbot-test
gcloud config set compute/region asia-northeast1
gcloud config set compute/zone asia-northeast1-a
```


GCPプロジェクトの秘密鍵設定
---------------------------

1. [Setting up authentication](https://dialogflow.com/docs/reference/v2-auth-setup) を参考にGCPプロジェクトのサービスアカウントで秘密鍵を作成し、 keysディレクトリ以下に配置する。
2. `.env.example` ファイルを `.env` ファイルにコピーし、 `GOOGLE_APPLICATION_CREDENTIALS` を変更する。


サービスアカウントの設定
------------------------

intentの取得などでパーミッションエラーが出た場合、GCPのコンソールでサービスアカウントに `Dialogflow API 管理者` の役割を付与する必要がある。


invoke tasks
------------

各種タスクを `pipenv run inv[oke]` で利用できます。タスクの一覧を表示するには

```
$ pipenv run inv --list
```

を実行して下さい。各タスクの詳細なヘルプを参照するには

```
$ pipenv run inv task-name --help
```

を実行して下さい。


Tips 
----

### Training Phraseが取れなかったら

下記のように `get_intent` に `intent_view` を渡す必要がある。

```
import dialogflow_v2beta1 as dialogflow
from dialogflow_v2.gapic import enums

client = dialogflow.IntentsClient()
name = client.intent_path(project, intent_id)
response = client.get_intent(name, intent_view=enums.IntentView.INTENT_VIEW_FULL)
print(json.dumps(MessageToDict(element), ensure_ascii=False))
```

See [Training Dialogflow agent via API V2 - Stack Overflow](https://stackoverflow.com/questions/50149514/training-dialogflow-agent-via-api-v2)
