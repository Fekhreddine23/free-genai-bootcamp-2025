from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo
)
from comps.cores.mega.constants import ServiceType, ServiceRoleType
from comps import MicroService, ServiceOrchestrator
import os
from comps.cores.mega.utils import handle_message
from fastapi import HTTPException
from starlette.responses import StreamingResponse, Response

import json  # Assurez-vous que json est importé

# Configuration des variables d'environnement
EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 9000)


class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        print("coucou")
        os.environ["TELEMETRY_ENDPOINT"] = ""
        self.host = host
        self.port = port
        self.endpoint = "/v1/example-service"
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        """
        Configure les services distants nécessaires pour le méga-service.
        """
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(llm)

    def start(self):
        """
        Configure et démarre le service principal.
        """
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )

        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        print(f"Service configured with endpoint: {self.endpoint}")
        self.service.start()

    async def handle_request(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Gère les requêtes entrantes et retourne une réponse.
        """
        print("handle_request called")  # Log pour confirmer l'appel
        try:
            # Préparer la requête pour Ollama
            ollama_request = {
                "model": request.model or "llama3.2:1b",  # Modèle par défaut
                "messages": request.messages,
                "stream": False  # Désactiver le streaming pour l'instant
            }

            print("\n\n\n 1. Ollama request:")
            print(ollama_request)

            # Planifier la requête via le méga-service
            result = await self.megaservice.schedule(ollama_request)
            print("\n\n\n 2. Ollama response:")
            print(result)

            # Vérifier si le résultat est valide
            if isinstance(result, tuple) and len(result) > 0:
                llm_response = result[0].get("llm/MicroService")
                print("\n\n\n 3. LLM response:")
                print(llm_response)

                if llm_response and hasattr(llm_response, "body_iterator"):
                    # Traiter la réponse de type StreamingResponse
                    response_body = b""
                    async for chunk in llm_response.body_iterator:
                        print("Received chunk:", chunk)
                        response_body += chunk
                    print("response body:", response_body)

                    try:
                        # Décoder le contenu brut
                        content = response_body.decode('utf-8')
                        print("Decoded content:", content)

                        # Tenter de parser le contenu en JSON
                        content_json = json.loads(content)
                        print("Parsed JSON content:", content_json)

                        # Extraire la réponse si disponible
                        content = content_json.get("choices", [{}])[0].get("message", {}).get("content", "No content found")
                    except json.JSONDecodeError:
                        print("Response is not valid JSON, using raw content.")
                        content = response_body.decode('utf-8')
                    except Exception as e:
                        print(f"Error processing response: {e}")
                        content = "Error processing response"
                else:
                    content = "Invalid response format"
            else:
                content = "No valid response received from megaservice"

            # Créer la réponse
            response = ChatCompletionResponse(
                model=request.model or "example-model",
                choices=[
                    ChatCompletionResponseChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=content
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=UsageInfo(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0
                )
            )
            print("Final response:", response)
            return response

        except Exception as e:
            # Gérer les erreurs
            print(f"Error in handle_request: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


# Instanciation de la classe et démarrage du service
if __name__ == "__main__":
    example = ExampleService()
    example.add_remote_service()
    example.start()
    print("app.py executed successfully!")


