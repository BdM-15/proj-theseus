# Critique Prompt (post-generation self-review)

After producing an artifact, run this prompt against your own output before returning it.

```
You are a Source Selection Authority on a federal proposal evaluation. You have 5 seconds per slide and 30 seconds per page.

Review the attached artifact and answer:
1. What is the discriminator? State it in one sentence using the customer's language.
2. Which workspace entities (CLINs, requirements, factors) are cited? Are any invented?
3. Is the compliance trace (L → M → C) complete? List any gap.
4. What would a competitor say is weak? (black-hat read)
5. Production quality 1-5: typography, density, hierarchy, restraint.

Reject the artifact if any answer is "unclear", "I can't tell", or score <3.
```

Iterate until the critique passes.
