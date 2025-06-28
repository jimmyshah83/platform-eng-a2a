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

from platform_eng_a2a_demo.tools.azure_mcp_agent import AzureMCPTool


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AzureMCPAgentExecutor(AgentExecutor):
    """Azure MCP AgentExecutor Example."""

    def __init__(self):
        self.agent = AzureMCPTool()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        task = context.current_task
        if not task:
            if not context.message:
                raise ServerError(error=InvalidParamsError())
            task = new_task(context.message)
            event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        try:
            async for item in self.agent.stream(query, task.contextId):
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]

                if not is_task_complete and not require_user_input:
                    updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            item["content"],
                            task.contextId,
                            task.id,
                        ),
                    )
                elif require_user_input:
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
                    updater.add_artifact(
                        [Part(root=TextPart(text=item["content"]))],
                        name="azure_mcp_result",
                    )
                    updater.complete()
                    break

        except Exception as e:
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