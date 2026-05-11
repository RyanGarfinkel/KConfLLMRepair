from pydantic import BaseModel, Field, field_validator

class AgentResponse(BaseModel):

    define: list[str] = Field(description='List of configuration option names to define for KLocalizer. Option name only.')
    undefine: list[str] = Field(description='List of configuration option names to undefine for KLocalizer. Option name only.')
    reasoning: str = Field(description='Reasoning behind what options to define and undefine.')

    @field_validator('define', 'undefine')
    @classmethod
    def validate_option_names(cls, v: list[str]) -> list[str]:
        
        result = []

        for name in v:
            name = name.strip()
            if not name:
                continue
            if not name.startswith('CONFIG_'):
                name = f'CONFIG_{name}'
            if not name.isupper():
                name = name.upper()
            if '=' in name:
                name = name.split('=')[0].strip()
            result.append(name)
        
        return result
