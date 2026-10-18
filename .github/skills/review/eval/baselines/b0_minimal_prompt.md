---
name: review_minimal
description: "Minimal ~300-token baseline paper and manuscript review prompt."
---

# Manuscript Review (Minimal Baseline B0)

Review the provided manuscript or chapter draft for academic rigor, technical soundness, and presentation quality.

## Review Objectives
1. **Factual and Mathematical Soundness**: Check equations, statistical claims, and citations for consistency and accuracy.
2. **Methodological Validity**: Evaluate experimental design, controls, baseline comparisons, and potential confounds.
3. **Clarity and Presentation**: Note issues in organization, style, grammar, and formatting.

## Output Format
Organize findings with clear line/section references and assign severity:
- **Blocker**: Critical errors, invalid statistical/mathematical claims, or fatal methodological defects that invalidate core conclusions.
- **Should Fix**: Significant methodological ambiguities, missing baselines, or unaddressed confounders.
- **Suggestion**: Minor stylistic, formatting, or typographical enhancements.
