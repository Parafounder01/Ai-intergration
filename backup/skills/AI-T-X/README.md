# ✏️ AI-T-X — English Corrector with Tamil Support

**Developed by:** anantha

A simple, no-nonsense English corrector for **slow learners** who need **Tamil translations**. Fixes grammar, prepositions, and punctuation — without long explanations or practice questions.

---

## 📋 What It Does

| Input | Output |
|-------|--------|
| Your sentence / paragraph in broken English | ✅ **Corrected English** — natural, daily-use rewrite |
| | ✅ **Corrections Table** — shows exactly what changed + Tamil meaning |

---

## 🧠 How to Use

### In OpenCode (when loaded as a skill)

```
@AI-T-X He go to office in every day.
```

Or use the `skill` tool:

```
@skill AI-T-X

My text
He go to office in every day.
```

### Flow

1. You paste your text below **My text**
2. If unclear → I ask **1 short question** to clarify
3. I output **only** the 2 sections below:

#### 1) Corrected English (Natural)

> He goes to the office every day.

#### 2) Corrections Table

| Wrong | Correct | Polite/Formal | Simple Meaning | Tamil Meaning |
|-------|---------|---------------|----------------|---------------|
| go | goes | - | changes for he/she/it | போகிறான் |
| in every day | every day | daily | removes wrong "in" | ஒவ்வொரு நாளும் |
| office | the office | - | a specific office | அலுவலகம் |

---

## 🎯 What Gets Corrected

| Focus Area | Examples |
|------------|----------|
| **Prepositions** | `in / on / at / to / for / with / from / about / by` |
| **Verb tense** | `go → goes`, `eated → ate` |
| **Subject-verb agreement** | `he go → he goes`, `they goes → they go` |
| **Word order** | `I like very much it → I like it very much` |
| **Punctuation / Capitalization** | missing `?` `.` `,` or capital letters |
| **Missing / extra words** | missing `the`, extra `in` |

---

## 🚫 What It Does NOT Do

- ❌ No long grammar explanations
- ❌ No practice questions
- ❌ No encouragement or "Good job!"
- ❌ No extra notes or tips
- ❌ No text outside the 2 output sections

---

## 📁 File Structure

```
backup/skills/AI-T-X/
├── SKILL.md      # OpenCode skill definition (2.9 KB)
└── README.md      # This file — usage & explanation
```

---

## ⚙️ Installation

The skill is auto-discovered by OpenCode from:

```
~/.config/opencode/skills/AI-T-X/SKILL.md
```

Or clone this repo and copy:

```powershell
Copy-Item -Recurse backup/skills/AI-T-X "$env:USERPROFILE\.config\opencode\skills\"
```

---

## 📝 License

MIT — free to use, modify, and share.
