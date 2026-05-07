from pydantic import BaseModel


class WhatIfResponse(BaseModel):
    scenario: str
