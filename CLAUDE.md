# Rules for Claude

## Paid credits — always ask first

Before any generation that spends more than **10 credits** (Higgsfield, Canva, or any other paid tool), stop and ask the user for permission first. Run a cost preflight (e.g. `get_cost: true`), tell the user the exact cost and their remaining balance, and wait for an explicit "yes". No exceptions, even when the user asked for the output directly.
