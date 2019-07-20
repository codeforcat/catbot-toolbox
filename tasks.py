import os
import re
import uuid

import dialogflow_v2
from invoke import task

import dialogflow_v2beta1


@task
def list_intent(c, project='catbot-test', display_name_regex='\0'):
    display_name_pattern = re.compile(display_name_regex)
    client = dialogflow_v2beta1.IntentsClient()
    parent = client.project_agent_path(project)
    for element in client.list_intents(parent):
        if display_name_pattern.search(element.display_name):
            print(element)


@task
def get_intent(c, project='catbot-test', intent_id=''):
    client = dialogflow_v2beta1.IntentsClient()
    name = client.intent_path(project, intent_id)
    response = client.get_intent(name)
    print(response)


@task
def detect_intent(c, project='catbot-test', text=''):
    session_client = dialogflow_v2beta1.SessionsClient()
    session = session_client.session_path(project, uuid.uuid4())
    text_input = dialogflow_v2beta1.types.TextInput(text=text)
    query_input = dialogflow_v2beta1.types.QueryInput(text=text_input)
    response = session_client.detect_intent(session=session, query_input=query_input)
    print(response)
