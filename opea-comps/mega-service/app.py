from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from comps.cores.mega.constants import ServiceType
from comps import MicroService, ServiceOrchestrator
from comps.cores.proto.docarray import LLMParams
import os
import random
import time
import json
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import FastAPI, HTTPException, Request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import logging
import uvicorn
import aiohttp

# Configuration des variables d'environnement
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "localhost")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", "11434")
LLM_SERVICE_ENDPOINT = os.getenv("LLM_SERVICE_ENDPOINT", "/api/generate")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "gemma:2b")
JAEGER_ENDPOINT = os.getenv("JAEGER_ENDPOINT", "172.19.0.3:4317")

# Configuration du logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level, logging.INFO)
logging.basicConfig(level=numeric_level)
logger = logging.getLogger(__name__)
logger.setLevel(numeric_level)


class ExampleService:
    def __init__(self, host="0.0.0.0", port=8001):
        logger.info("Initializing ExampleService...")
        self.host = host
        self.port = port
        self.endpoint = "/chat"
        self.megaservice = ServiceOrchestrator()

        os.environ["LOGFLAG"] = "true"
        self.setup_tracing(jaeger_endpoint=JAEGER_ENDPOINT)
        self.tracer = trace.get_tracer(__name__)

    async def check_ollama_connection(self):
        """Vérifie la connexion à Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}/api/tags"
                logger.info(f"Testing Ollama connection to: {url}")
                async with session.get(url) as response:
                    if response.status == 200:
                        models = await response.json()
                        logger.info(f"Available models: {models}")
                        return True
                    return False
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False

    def setup_tracing(self, jaeger_endpoint="jaeger:4317"):
        """Configure le tracing OpenTelemetry avec exportateur OTLP."""
        if not isinstance(trace.get_tracer_provider(), TracerProvider):
            trace.set_tracer_provider(TracerProvider())
            logger.info("Created new TracerProvider")

        otlp_exporter = OTLPSpanExporter(
            endpoint=jaeger_endpoint,
            insecure=True,
        )
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        logger.info(f"OTLP exporter configured for Jaeger at {jaeger_endpoint}")

    def add_remote_service(self):
        """Configure les services distants nécessaires."""
        with self.tracer.start_as_current_span("add_remote_service"):
            llm = MicroService(
                name="llm",
                host=LLM_SERVICE_HOST_IP,
                port=LLM_SERVICE_PORT,
                endpoint=LLM_SERVICE_ENDPOINT,
                use_remote_service=True,
                service_type=ServiceType.LLM,
            )
        logger.info(f"Added LLM service")
        self.megaservice.add(llm)

    async def handle_request_internal(self, request: Request) -> ChatCompletionResponse:
        """Gère les requêtes entrantes en utilisant l'orchestrateur."""
        with self.tracer.start_as_current_span("handle_request"):
            data = await request.json()
            stream_opt = data.get("stream", False)
            chat_request = ChatCompletionRequest.model_validate(data)
            logger.info(f"Received request for model: {chat_request.model}")

        # Configuration des paramètres LLM
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens or 1024,
            top_k=chat_request.top_k or 10,
            top_p=chat_request.top_p or 0.95,
            temperature=chat_request.temperature or 0.01,
            frequency_penalty=chat_request.frequency_penalty or 0.0,
            presence_penalty=chat_request.presence_penalty or 0.0,
            repetition_penalty=chat_request.repetition_penalty or 1.03,
            stream=stream_opt,
            model=chat_request.model,
            chat_template=chat_request.chat_template or None,
        )

        # Convertir les messages en prompt pour Ollama - Gestion des deux formats
        prompt_parts = []
        for msg in chat_request.messages:
            # Si c'est un objet Pydantic
            if hasattr(msg, "role") and hasattr(msg, "content"):
                prompt_parts.append(f"{msg.role}: {msg.content}")
            # Si c'est un dictionnaire
            elif isinstance(msg, dict) and "role" in msg and "content" in msg:
                prompt_parts.append(f"{msg['role']}: {msg['content']}")
            else:
                logger.warning(f"Message format inconnu ignoré: {type(msg)} - {msg}")

        prompt = "\n".join(prompt_parts)
        initial_inputs = {"prompt": prompt}

        logger.debug(
            "Request payload:\n%s",
            json.dumps(
                initial_inputs,
                indent=2,
                default=lambda o: o.dict() if hasattr(o, "dict") else str(o),
            ),
        )

        # Appel à l'orchestrateur
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs=initial_inputs, llm_parameters=parameters
        )

        logger.debug(
            "Service results:\n%s",
            json.dumps({k: type(v).__name__ for k, v in result_dict.items()}, indent=2),
        )

        # Détection des réponses streaming
        for node, response in result_dict.items():
            if isinstance(response, StreamingResponse):
                logger.info("Returning streaming response from node: %s", node)
                return response

        # Extraction du dernier nœud du graphe
        leaves = runtime_graph.all_leaves()
        if not leaves:
            logger.error("No leaves found in execution graph")
            raise HTTPException(500, "Service execution error")

        last_node = leaves[-1]
        logger.debug("Last execution node: %s", last_node)

        # Vérification de la présence des résultats
        if last_node not in result_dict:
            logger.error("Missing results for node: %s", last_node)
            raise HTTPException(500, "Missing service results")

        service_result = result_dict[last_node]
        logger.debug(f"Raw Ollama response: {service_result}")

        # Vérifier les erreurs de chargement du modèle
        if (
            isinstance(service_result, dict)
            and service_result.get("done_reason") == "load"
        ):
            logger.error(f"Model failed to load: {service_result}")
            raise HTTPException(500, "Model loading failed")

        # Gestion des erreurs
        if isinstance(service_result, dict) and "error" in service_result:
            error = service_result["error"]
            logger.error("Service error: %s", error)
            raise HTTPException(
                status_code=(
                    400 if error.get("type") == "invalid_request_error" else 500
                ),
                detail=error.get("message", "Unknown error"),
            )

        # Traitement des réponses Ollama
        if isinstance(service_result, dict):
            # Format Ollama
            message_content = service_result.get("response", "")

            # Extraction des informations d'usage
            usage_info = {
                "prompt_tokens": service_result.get("prompt_eval_count", 0),
                "completion_tokens": service_result.get("eval_count", 0),
                "total_tokens": service_result.get("prompt_eval_count", 0)
                + service_result.get("eval_count", 0),
            }
        else:
            # Format de secours
            message_content = str(service_result)
            usage_info = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        # Construction de la réponse
        usage = UsageInfo(
            prompt_tokens=usage_info["prompt_tokens"],
            completion_tokens=usage_info["completion_tokens"],
            total_tokens=usage_info["total_tokens"],
        )

        return ChatCompletionResponse(
            id=f"chatcmpl-{random.randint(1000, 9999)}",
            model=chat_request.model or LLM_MODEL_ID,
            object="chat.completion",
            created=int(time.time()),
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=message_content),
                    finish_reason="stop",
                )
            ],
            usage=usage,
        )

    def start(self):
        """Configure et démarre le service principal."""
        app = FastAPI()
        FastAPIInstrumentor.instrument_app(app)

        @app.get("/health")
        async def health_check():
            return {"status": "ok", "service": "mega-service"}

        @app.post("/chat")
        async def endpoint_handler(request: Request):
            return await self.handle_request_internal(request)

        logger.info(f"Service running on http://{self.host}:{self.port}{self.endpoint}")

        # Vérification asynchrone de la connexion Ollama
        import asyncio

        if not asyncio.run(self.check_ollama_connection()):
            logger.error(
                "Ollama connection check failed! Service may not work properly"
            )

        uvicorn.run(app, host=self.host, port=self.port)


if __name__ == "__main__":
    logger.info("Starting ExampleService...")
    example = ExampleService(port=8001)
    example.add_remote_service()

    try:
        example.start()
    except Exception as e:
        logger.error(f"Service failed: {str(e)}")
        raise
