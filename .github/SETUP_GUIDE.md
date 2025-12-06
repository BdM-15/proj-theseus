# VS Code Copilot Customization Setup Guide

**Your VS Code Version**: 1.106.3 ✅ (Custom agents supported!)

---

## 1. Enable Prompt Files

**In VS Code**:

1. Open Settings (`Ctrl+,`)
2. Search for `chat.promptFiles`
3. Check the box to enable it

**Or use Command Palette**:

- Press `Ctrl+Shift+P`
- Type: `Preferences: Open User Settings (JSON)`
- Add: `"chat.promptFiles": true`

---

## 2. Verify Agents Appear

1. Open GitHub Copilot Chat (`Ctrl+Alt+I`)
2. Click the **agent selector** dropdown (top of chat)
3. You should see:
   - `@plan` - Planning agent
   - `@implement` - Implementation agent
   - `@validate` - Validation agent

**If you don't see them**:

- Reload VS Code: `Ctrl+Shift+P` → `Developer: Reload Window`

---

## 3. Use Prompt Files with `/` Commands

In Copilot Chat, type `/` and you'll see:

- `/plan-feature` - Plan from GitHub issue
- `/add-entity-type` - Add new entity type workflow
- `/add-inference-algorithm` - Add relationship inference
- `/debug-processing` - Troubleshoot RFP processing

**Example**:

```
/plan-feature 17
```

This will automatically:

1. Fetch Issue #17 from GitHub
2. Research the codebase
3. Generate implementation plan
4. Suggest branch: `028-parallel-chunk-extraction`

---

## 4. Use Custom Agents

**Method 1: Agent Selector**

1. Click agent dropdown in chat
2. Select `@plan`
3. Type: `Create plan for Issue #17`

**Method 2: Direct Reference**

```
@plan Create implementation plan for Issue #17 (parallel chunk extraction)
```

**Method 3: Agent Handoffs** (POWERFUL!)

1. Use `@plan` to create plan
2. Click **"Start Implementation"** button at bottom of response
3. Automatically switches to `@implement` agent with context!
4. After implementation, click **"Start Validation"** button
5. Switches to `@validate` agent

This creates a guided workflow: Plan → Implement → Validate

---

## 5. Real Workflow Example

### Using Prompt Files (Easiest):

```
Step 1: /plan-feature 17
[Agent generates plan + suggests branch 028-parallel-chunk-extraction]

Step 2: Create branch manually
git checkout -b 028-parallel-chunk-extraction

Step 3: @implement
[Paste the plan, agent writes tests + implements]

Step 4: @validate
[Agent runs tests, checks errors, validates]
```

### Using Agent Handoffs (Smoothest):

```
Step 1: @plan
"Create implementation plan for Issue #17"
[Click "Start Implementation" button]

Step 2: (Automatically switches to @implement)
[Click "Start Validation" button]

Step 3: (Automatically switches to @validate)
[Manual validation complete]
```

---

## 6. What Each Agent Does

### `@plan` Agent

- **Tools**: `fetch`, `githubRepo`, `search`, `usages` (READ-ONLY)
- **Purpose**: Research and plan, no code edits
- **Handoff**: "Start Implementation" → `@implement`

### `@implement` Agent

- **Tools**: ALL tools (full editing)
- **Purpose**: TDD implementation (tests first)
- **Handoff**: "Start Validation" → `@validate`

### `@validate` Agent

- **Tools**: `runTests`, `get_errors`, READ-ONLY tools
- **Purpose**: Run tests, check quality, verify Neo4j
- **Handoff**: "Commit Changes" → Git commit message ready

---

## 7. Troubleshooting

### "Agent not found"

- Reload VS Code: `Ctrl+Shift+P` → `Developer: Reload Window`
- Check files exist in `.github/agents/*.agent.md`

### "Prompt file not found"

- Enable setting: `chat.promptFiles: true`
- Check files exist in `.github/prompts/*.prompt.md`
- Reload VS Code

### "/ commands don't show"

- Type `/` in chat input (may need to wait 2-3 seconds)
- Enable `chat.promptFiles` setting
- Ensure prompt files have `.prompt.md` extension

---

## 8. Next Steps

Once setup complete:

1. **Test the workflow**: `/plan-feature 17`
2. **Try agent handoffs**: Use the buttons!
3. **Customize agents**: Edit `.github/agents/*.agent.md` files
4. **Add more prompts**: Create new `.prompt.md` files

---

**Last Updated**: December 6, 2025  
**Your VS Code**: 1.106.3 (supports all features)
