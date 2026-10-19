# chughy-skills

Agent skills for shipping Apple apps safely: small, tested checks an AI coding agent (Claude Code, Codex, Gemini/Antigravity, Pi, or any agent that reads `SKILL.md` files) runs before you do something you can't take back.

## Skills

| Skill | What it does |
|---|---|
| [`hidden-feature-gate`](skills/hidden-feature-gate/SKILL.md) | Blocks an App Store upload while release source or the built binary still contains hidden, dormant or undocumented switches (App Review guideline 2.5.19, whose penalty includes developer-account termination). It scans Swift source outside `#if DEBUG` and every Mach-O file in the `.app`/`.xcarchive`. |

## Install

```sh
# any agent that supports the skills format (global)
npx skills add anupamchugh/chughy-skills -g

# or copy one skill by hand
git clone https://github.com/anupamchugh/chughy-skills
cp -R chughy-skills/skills/hidden-feature-gate ~/.claude/skills/   # or ~/.agents/skills/
```

## Use

In your agent: "run the hidden-feature gate before we upload", or run it yourself:

```sh
python3 skills/hidden-feature-gate/scripts/gate.py --source Sources
python3 skills/hidden-feature-gate/scripts/gate.py --binary build/App.xcarchive
```

Exit codes: 0 pass, 1 hits found (blocks the upload), 2 usage error. Python 3 standard library only, plus `strings` from the Xcode command-line tools.

## Test

```sh
python3 -m unittest discover -s skills/hidden-feature-gate/tests -v
```

## Limits

This is a heuristic scanner, not a guarantee of approval. It reads Swift source and binary strings; it doesn't know your App Store metadata, and it reports false positives (a game role called "Demon", a visible Face ID "Unlock" button). Explain each remaining hit in writing; don't rename switches to slip past it. App Review makes the final call.

## License

MIT
