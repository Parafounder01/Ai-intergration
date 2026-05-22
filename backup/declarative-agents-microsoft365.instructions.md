# Write effective instructions for declarative agents

> **Source:** Microsoft Learn — Official guidance for Microsoft 365 Copilot declarative agents
> **URL:** https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions
> **Retrieved:** 2026-05-22

Declarative agents are customized versions of Microsoft 365 Copilot that help you create personalized experiences by declaring specific instructions, actions, and knowledge. To write effective instructions for your declarative agent, consider the following questions:

- What goal must your agent accomplish?
- What workflows do you envision your end users going through?
  - Is there business logic you want to incorporate?
  - Is there a desired end user experience you want to incorporate?
- For each workflow, can you provide step-by-step instructions for the agent?

---

## Instruction components

A well-structured set of instructions ensures that the agent understands its role, the tasks it should perform, and how to interact with users. The main components of declarative agent instructions are:

- **Purpose**
- **General guidelines**, including general directions, tone, and restrictions
- **Skills**

When relevant, also include:

- Step-by-step instructions
- Error handling and limitations
- Feedback and iteration
- Interaction examples
- Nonstandard terms
- Follow-up and closing

> **IMPORTANT:** Don't store or offload declarative agent instructions in SharePoint documents (or any other knowledge source) to work around the 8,000-character instruction limit. Knowledge source content is not trusted maker-authored instruction content and is subject to cross-prompt injection attacks (XPIA) classifiers.

---

## Best practices

### Use clear actionable language
- Focus on what Copilot **should do**, not what to avoid.
- Use precise verbs: "ask", "search", "send", "check", "use".
- Supplement with examples. Define nonstandard terms.

### Build step-by-step workflows with transitions
Each step should include:
- **Goal**: The purpose of the step.
- **Action**: What the agent should do and which tools to use.
- **Transition**: Clear criteria for moving to the next step or ending.

### Use strict structure
- **Sections** group related tasks (no sequence implied).
- **Bullets** for parallel, independent tasks.
- **Steps** for required sequential actions only.

### Make tasks atomic
Break multiaction instructions into clearly separated units.

### Always specify tone, verbosity, and output format
If you don't specify, the model infers — leading to inconsistency.

### Structure instructions in Markdown
- `#`, `##`, `###` for headers
- `-` for unordered lists, `1.` for ordered
- Backticks for tool/system names (`` `Jira` ``)
- `**bold**` for critical instructions

### Provide domain vocabulary
Define specialized terms, formulas, acronyms, and dataset-specific language.

### Explicitly reference capabilities, knowledge, and actions
Clearly call out action names, capabilities, or knowledge sources at each step.

### Provide examples
Complex scenarios work best with few-shot prompting (multiple examples).

### Control reasoning through phrasing

| Mode | Phrasing |
|------|----------|
| Deep | "analyze", "evaluate", "justify", "think step by step", "reflect" |
| Moderate | "concise but structured explanation, 3 key drivers, final recommendation" |
| Fast/Minimal | "Short answer only. No reasoning or explanation." |

### Avoid common failures
- **Overeager tool use**: "Only call tool if inputs are available; otherwise ask user."
- **Repetitive phrasing**: Encourage varied responses; use multiple examples.
- **Verbose explanations**: Add constraints and concise examples.

### Add a final self-evaluation step
Before finalizing, confirm completeness and alignment with instructions.

### Apply a stabilizing header when needed
If drift occurs, add:
> Always interpret instructions literally. Never infer intent or fill in missing steps. Follow step order exactly.

### Iterate on instructions
Create -> Publish -> Test -> Iterate

---

## Example: IT support agent instructions

```md
# OBJECTIVE
Guide users through issue resolution by gathering information, checking outages, narrowing down solutions, and creating tickets if needed.

# RESPONSE RULES
- Ask one clarifying question at a time, only when needed.
- Present information as concise bullet points or tables.
- Always confirm before moving to the next step or ending.

# WORKFLOW

## Step 1: Gather Basic Details
- **Goal:** Identify the user's issue.
- **Action:** Proceed if clear; otherwise ask one clarifying question.
- **Transition:** Once clear, proceed to Step 2.

## Step 2: Check for Ongoing Outages
- **Goal:** Rule out known outages.
- **Action:** Query `ServiceNow` for current outages.
- **Transition:** If outage found with unrelated issue -> Step 3. Otherwise end.

## Step 3: Narrow Down Resolution
- **Goal:** Find best-fit solutions.
- **Action:** Search `ServiceNow KB` for related articles.
- **Iterative narrowing:** Ask clarifying questions until best solution found.

## Step 4: Create Support Ticket
- **Goal:** Log unresolved issues.
- **Action:** Map category from `sys_choice` SharePoint file. Fetch user UPN. Fill ticket.
```

---

## Design patterns

### Pattern 1: Deterministic workflows
Remove ambiguity with atomic steps, explicit formulas, and required validation.

### Pattern 2: Parallel vs. sequential structure
Separate parallel and sequential logic explicitly.

### Pattern 3: Explicit decision rules
Add if/then rules to prevent unintended interpretation:
```
If performance is stable, write summary.
If performance declines, write risks section.
```

### Pattern 4: Output contract
Specify: Goal, Format, Detail level, Tone, Include/Exclude, Example shape.

### Pattern 5: Clean Markdown structure
Consistent headers, lists, and formatting.

### Pattern 6: Self-evaluation gate
Add "Final Check" step to verify completeness before responding.

### Pattern 7: Steering reasoning
Use deep reasoning cues or fast/minimal cues explicitly.

### Pattern 8: Literal-execution header (stability)
```
Always interpret instructions literally.
Never infer intent or fill in missing steps.
Never add context, recommendations, or assumptions.
Follow step order exactly with no optimization.
```

### Pattern 9: Evaluate and migrate existing instructions
Structured audit: Step order, Tool use, Grounding, Missing-data handling, Verbosity, Contradictions, Vague verbs, Safety.

---

## Related
- Declarative agent manifest schema (v1.3+)
- Agent Builder in Microsoft 365 Copilot
- Microsoft 365 Agents Toolkit
