import json

from pydantic import BaseModel, Field, model_validator

from repro.models import Action, OracleSpec


class ReductionProposal(BaseModel):
    keep_indices: list[int] = Field(max_length=120)
    explanation: str

    @model_validator(mode="after")
    def ordered_indices(self):
        if self.keep_indices != sorted(set(self.keep_indices)) or any(
            i < 0 for i in self.keep_indices
        ):
            raise ValueError("Indices must be unique, nonnegative and in the original order")
        return self


async def propose_reduction(model, steps: list[Action], oracle: OracleSpec):
    """Suggest deletions only. A proposal is never evidence until clean replay verifies it."""
    proposal = await model.structured(
        ReductionProposal,
        "Select a shorter subsequence of this recorded UI experiment that ends with the reported "
        "symptom visible. Remove cancelled detours, redundant navigation and inspection after the "
        "symptom is already visible. Preserve required startup/navigation steps and their order. "
        "Return zero-based indices to KEEP. You cannot add, edit or reorder actions. "
        "This is only a proposal; a fresh baseline replay will decide whether it works.\n"
        + "Symptom: "
        + oracle.model_dump_json()
        + "\nRecorded actions: "
        + json.dumps([{"index": i, **a.model_dump()} for i, a in enumerate(steps)]),
        purpose="replay reduction proposal",
    )
    if any(i >= len(steps) for i in proposal.keep_indices):
        raise ValueError("Reduction proposal references an unrecorded action")
    return [steps[i] for i in proposal.keep_indices], proposal
