from pydantic import BaseModel, Field, field_validator
import re

OPTION_PATTERN = r'CONFIG_[A-Z0-9_]+'

class AgentResponse(BaseModel):

    define: list[str] = Field(description='List of configuration option names to define for KLocalizer. Option name only.')
    undefine: list[str] = Field(description='List of configuration option names to undefine for KLocalizer. Option name only.')
    reasoning: str = Field(description='Reasoning behind what options to define and undefine.')

    @field_validator('define', 'undefine')
    @classmethod
    def validate_option_names(cls, v: list[str]) -> list[str]:
        
        result = []

        for name in v:
            name = ''.join(c for c in name.strip() if c.isascii()).upper()
        
            if not name.startswith('CONFIG_'):
                name = f'CONFIG_{name}'

            matches = re.findall(OPTION_PATTERN, name)
            if not matches:
                continue

            name_lower = name.lower()
            if 'undefine' in name_lower:
                index = name_lower.find('undefine')
                result.extend(re.findall(OPTION_PATTERN, name[:index]))
            elif 'define' in name_lower:
                index = name_lower.find('define')
                result.extend(re.findall(OPTION_PATTERN, name[:index]))
            else:
                result.extend(matches)
        
        return result
