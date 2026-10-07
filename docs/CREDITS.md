# Credits

job-apply-kit builds on two upstream open-source projects. Both are MIT-licensed; the kit itself is
MIT-licensed (see `LICENSE`).

## humanizer

`skills/humanizer/` is adapted from [blader/humanizer](https://github.com/blader/humanizer) (v2.5.1)
by Siqi Chen ([@blader](https://github.com/blader)). The 29 anti-AI-writing patterns, the personality
and voice-calibration guidance, and the worked example are preserved from the source; only the tool
references were made tool-neutral and the frontmatter was adapted for this kit. Original license
preserved in `skills/humanizer/LICENSE`.

## resume-kit (deep-tailoring track)

`skills/resume-kit/` and the six skills that depend on it (`make-resume`, `make-cover-letter`, `critique`,
`edit-resume`, `setup-extract`, `setup-build-kb`) descend from a resume-tailoring skill set by Varun
Ramesh, combining the character-budget / char-count-gate system, the critique framework, and the
knowledge-base build pipeline (`/setup-extract` -> `/setup-build-kb` -> `/make-resume`). The content
was reworked to remove personal data, point at this kit's config and `OPERATIONS.md`, and merge in
recovery/safety logic from an earlier fork of the same skill set.

## Everything else

The browser-automation skills (`bdjobs-full-run`, `linkedin-full-run`, `linkedin-job-search`,
`check-linkedin-saved`, `check-facebook-saved`, `check-discord-jobs`, `check-image-batch`), `job-apply-core`, and
`create-template` are original to this kit.
