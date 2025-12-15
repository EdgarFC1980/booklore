from .booklore_client import BookloreClient
from .planner import Plan

class Executor:
    def __init__(self, booklore: BookloreClient) -> None:
        self.booklore = booklore

    async def apply(self, plan: Plan) -> dict:
        results = []
        for action in plan.actions:
            res = await self.booklore.set_book_tags(
                action.book_id, action.add_tags
            )
            results.append({"book_id": action.book_id, "result": res})
        return {"applied": len(results), "results": results}
