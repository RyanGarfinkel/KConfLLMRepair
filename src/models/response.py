from pydantic import BaseModel, Field

class AgentResponse(BaseModel):

    define: list[str] = Field(description='List of configuration option names to define for KLocalizer.')
    undefine: list[str] = Field(description='List of configuration option names to undefine for KLocalizer.')
    reasoning: str = Field(description='Reasoning behind what options to define and undefine.')
