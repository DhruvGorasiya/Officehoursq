# Sprint 2 Retrospective

**Sprint Duration:** Mar 3 - Mar 13, 2026
**Sprint Goal:** Complete all user-facing features, implement real-time updates, add API documentation, and deploy the application to production.
**Sprint Outcome:** Goal met. All planned user stories completed and application deployed.

---

## What Went Well

**The PRD paid off during implementation.** Because the PRD was detailed and LLM-consumable, Cursor could reference it directly when building features. The data models, API specs, and edge cases were all explicit, which meant less back-and-forth during coding. Having the mockup JSX as a visual source of truth alongside the PRD eliminated ambiguity about how things should look versus how they should behave.

**FastAPI's built-in OpenAPI made API docs effortless.** Instead of writing separate documentation, we annotated route decorators and Pydantic models with descriptions, and FastAPI generated the entire Swagger UI automatically. The key lesson was being specific in our instructions to Cursor: the first attempt produced standalone markdown files instead of code annotations. Rewriting the task PRD with exact file paths and a clear "do NOT create markdown files" instruction fixed this immediately.

**Supabase Realtime worked well for the queue.** Subscribing to Postgres changes on the questions table meant that queue position updates, claim notifications, and status changes all propagated to clients without any custom WebSocket server. Scoping subscriptions to session channels kept the payloads focused.

**Deployment was straightforward once configured correctly.** Vercel auto-detected Next.js and Render handled FastAPI without issues. The main deployment work was environment variables and CORS configuration.

---

## What Didn't Go Well

**Vercel deployment 404 issue.** The first Vercel deploy showed a 404 even though the build succeeded. The root cause was the Framework being set to "Other" instead of "Next.js" in Vercel's Production Overrides. This setting was locked and couldn't be edited after creation, so we had to delete the project and recreate it. This cost about 30 minutes of debugging.

**AI-assisted docs generation required iteration.** When we first asked Cursor to generate API documentation, it created standalone markdown files instead of modifying the actual FastAPI source code. The initial PRD was too abstract. We had to rewrite it with specific file paths, exact code snippets for every route decorator, and explicit instructions about what NOT to do. The lesson: the quality of AI-generated output is directly proportional to the specificity of your instructions.

**Render free tier cold starts.** The backend takes 30-60 seconds to wake up after inactivity. This creates a poor first impression when someone visits the app after it's been idle. We documented this in the README but it's still a known limitation.

**Testing was deferred too late.** We focused on features and deployment first, which left testing and CI/CD for the final stretch. Starting tests earlier would have caught edge cases sooner and made the CI pipeline setup smoother.

---

## What We'd Change

**Write tests alongside features, not after.** Every user story should include test files as part of its acceptance criteria. This would have distributed the testing workload across the sprint instead of concentrating it at the end.

**Create a deployment checklist earlier.** We hit several small issues during deployment (CORS, environment variables, Vercel framework override) that could have been anticipated with a pre-deployment checklist. For Sprint 3 or future projects, we'd document deployment requirements before the deploy step.

**Be more specific with AI instructions from the start.** The pattern we discovered, writing task-specific PRDs with exact file paths and explicit "do not" rules, should be the default approach when delegating to AI tools. Abstract instructions produce abstract results.

**Budget time for CI/CD in the sprint plan.** CI/CD was listed as a Sprint 2 item but didn't have a dedicated user story with acceptance criteria. Treating infrastructure as a first-class user story would ensure it gets proper attention.

---

## Sprint Velocity

| Metric | Value |
|---|---|
| Stories planned | 8 |
| Stories completed | 8 |
| Deployment issues encountered | 2 (Vercel 404, Render cold starts) |
| Deployment issues resolved | 2 |
| AI tool iterations needed for docs | 2 (abstract PRD failed, specific PRD succeeded) |

---

## Key Learnings

1. **PRD conciseness matters for LLM consumption.** Verbose, traditional PRDs don't work well as AI context. Lean, explicit documents with clear data models and edge cases produce better AI-assisted code.

2. **System prompts and PRDs serve different purposes.** A `.cursorrules` file should focus on coding behavior and workflow rules. Product details belong in the PRD as a referenced document, not embedded in the system prompt.

3. **Specificity beats abstraction for AI delegation.** Instead of "generate API docs," say "modify these exact files, add these exact parameters to these exact decorators, do NOT create any new files." The more specific the instruction, the better the output.

4. **Deploy early, even if incomplete.** Getting the deployment infrastructure working early reveals configuration issues that are easier to fix when you're not also racing to finish features.
