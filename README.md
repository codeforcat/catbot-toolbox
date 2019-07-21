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


サンプルコードの実行
--------------------

[クイックスタート](https://cloud.google.com/dialogflow/docs/quickstart-api#detect-intent-text-python) のサンプルコードの実行

```
$ pipenv run python examples/detect_intent_texts.py --project-id catbot-test --language-code ja-JP "ほげほげ"
Loading .env environment variables…
Session path: projects/catbot-test/agent/sessions/167b667b-946a-4740-a369-86180e75e0b4

====================
Query text: ほげほげ
Detected intent: Default Fallback Intent (confidence: 1.0)

Fulfillment text: ごめんね。ちょっとわからなかったにゃ。
```
