from comps import (
    MegaServiceEndpoint,
    MicroService,
    ServiceRoleType,
    ServiceType,
    ServiceOrchestrator,
)
from pydantic import BaseModel  # Import Pydantic for data models
import os
import sys


# Define Pydantic models for request/response
class ChatCompletionRequest(BaseModel):
    """Request datatype for chat completion"""

    prompt: str


class ChatCompletionResponse(BaseModel):
    """Response datatype for chat completion"""

    response: str


class Chat:
    def __init__(self):
        print("init")
        self.megaservice = ServiceOrchestrator()
        self.endpoint = "/pepsi-amour"

    def add_remove_services(self):
        print("add_remove_services")
        # Implement your service addition/removal logic here

    def handle_request(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Handle incoming chat requests"""
        print(f"Received request: {request.prompt}")
        # Process the request and generate response
        response = f"Processed: {request.prompt}"
        return ChatCompletionResponse(response=response)

    def start(self):
        print("start")
        self.host = "localhost"
        self.port = 8080
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
        self.service.start()


if __name__ == "__main__":
    print("main")
    chat = Chat()
    chat.add_remove_services()
    chat.start()
    print("Chat service started")
