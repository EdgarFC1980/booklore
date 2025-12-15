from pydantic import BaseModel, Field

class PlanAction(BaseModel):
    book_id: str
    add_tags: list[str] = Field(default_factory=list)

class Plan(BaseModel):
    intent: str
    actions: list[PlanAction]
    notes: str | None = None

def naive_plan_from_user_request(user_text: str, book_ids: list[str]) -> Plan:
    return Plan(
        intent="tag_books",
        actions=[
            PlanAction(book_id=b, add_tags=["pendiente_clasificar"])
            for b in book_ids
        ],
        notes=f"plan generado desde: {user_text}",
    )
