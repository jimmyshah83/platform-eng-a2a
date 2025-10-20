"""Azure MCP demo agent executor module.

This module contains the AzureMCPAgentExecutor class that handles
Azure MCP requests and manages task execution flow.
"""
import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

from .azure_agent import AzureMCPAgent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureMCPAgentExecutor(AgentExecutor):
    """Azure MCP AgentExecutor Example."""

    def __init__(self):
        print("[AzureMCPAgentExecutor] Initializing executor...")
        self.agent = AzureMCPAgent()
        print("[AzureMCPAgentExecutor] Executor initialized\n")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        print(f"\n{'='*60}")
        print("[AzureMCPAgentExecutor] Execute called")
        print(f"{'='*60}")
        
        error = self._validate_request(context)
        if error:
            print("[AzureMCPAgentExecutor] Request validation failed")
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        print(f"[AzureMCPAgentExecutor] User query: '{query}'")
        
        task = context.current_task
        if not task:
            if not context.message:
                print("[AzureMCPAgentExecutor] No message in context")
                raise ServerError(error=InvalidParamsError())
            print("[AzureMCPAgentExecutor] Creating new task...")
            task = new_task(context.message)
            event_queue.enqueue_event(task)
        
        print(f"[AzureMCPAgentExecutor] Task ID: {task.id}")
        print(f"[AzureMCPAgentExecutor] Context ID: {task.contextId}")
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        try:
            print("[AzureMCPAgentExecutor] Starting agent stream...")
            async for item in self.agent.stream(query, task.contextId):
                print(f"[AzureMCPAgentExecutor] Agent Response Item: {item}")
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]

                if not is_task_complete and not require_user_input:
                    print(f"[AzureMCPAgentExecutor] Task working: {item['content']}")
                    updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            item["content"],
                            task.contextId,
                            task.id,
                        ),
                    )
                elif require_user_input:
                    print(f"[AzureMCPAgentExecutor] Input required: {item['content']}")
                    updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            item["content"],
                            task.contextId,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                else:
                    print(f"[AzureMCPAgentExecutor] Task completed: {item['content']}")
                    updater.add_artifact(
                        [Part(root=TextPart(text=item["content"]))],
                        name="azure_mcp_result",
                    )
                    updater.complete()
                    break

            print(f"[AzureMCPAgentExecutor] Execution completed successfully")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"[AzureMCPAgentExecutor] ERROR: {e}")
            logger.error("An error occurred while streaming the response: %s", e)
            raise ServerError(error=InternalError()) from e

    def _validate_request(self, context: RequestContext) -> bool:  # pylint: disable=unused-argument
        """Validate the request context.
        
        Args:
            context: The request context to validate
            
        Returns:
            bool: False indicating no validation errors
        """
        return False

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel the current task execution.
        
        Args:
            context: The request context
            event_queue: The event queue for task updates
            
        Returns:
            Task | None: Returns None as cancellation is not supported
            
        Raises:
            ServerError: Always raises UnsupportedOperationError
        """
        raise ServerError(error=UnsupportedOperationError()) 