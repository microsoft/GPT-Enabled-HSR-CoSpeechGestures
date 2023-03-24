from azure.core.credentials import AzureKeyCredential
from azure.ai.language.conversations import ConversationAnalysisClient


class luis:
    def __init__(self,credential):
        self.clu_endpoint = credential["intent_recognizer"]["AZURE_CONVERSATIONS_ENDPOINT"]
        self.clu_key = credential["intent_recognizer"]["AZURE_CONVERSATIONS_KEY"]
        self.project_name = credential["intent_recognizer"]["AZURE_CONVERSATIONS_WORKFLOW_PROJECT_NAME"]
        self.deployment_name = credential["intent_recognizer"]["AZURE_CONVERSATIONS_WORKFLOW_DEPLOYMENT_NAME"]
    def analyze_input(self, query):
        self.client = ConversationAnalysisClient(self.clu_endpoint, AzureKeyCredential(self.clu_key))
        with self.client:
            #query = "Send an email to Carol about the tomorrow's demo"
            result = self.client.analyze_conversation(
                task={
                    "kind": "Conversation",
                    "analysisInput": {
                        "conversationItem": {
                            "participantId": "1",
                            "id": "1",
                            "modality": "text",
                            "language": "en",
                            "text": query
                        },
                        "isLoggingEnabled": False
                    },
                    "parameters": {
                        "projectName": self.project_name,
                        "deploymentName": self.deployment_name,
                        "verbose": True
                    }
                }
            )
        return result['result']['prediction']['topIntent']