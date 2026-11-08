# Promo Finder

Reads microdrama screenplays and finds the best 20-60 second promo clips (hook at the start, cliffhanger at the end, clear on its own).

## How it works
1. `parse.py` reads each screenplay into blocks with exact timestamps. `prompt_utils.py` gives each block an ID (B001, B002 ...).
2. `find.py`: the AI picks 3 candidate promos per episode and answers with block IDs, never timestamps.
3. `validate.py`: plain rules turn IDs into exact times and reject bad picks (wrong length, wrong order, no hook in first 3 s, ends on a camera-only description).
4. `judge.py`: a second AI call scores each pick (hook, cliffhanger, standalone) seeing only the clip.
5. `rank.py`: weighted score, near-duplicates removed, all episodes ranked. `run_all.py` runs everything.

## Run it
1. Put the screenplay `.txt` files in `episodes/` (not included, they are private).
2. `pip install -r requirements.txt`
3. Set your API key (never put it in a file):
   - PowerShell: `$env:LLM_API_KEY="your-key"`
   - Mac/Linux: `export LLM_API_KEY="your-key"`
4. `python test_validate.py` checks the rules (no AI needed).
5. `python run_all.py --episodes 42` tests one episode. `python run_all.py` runs all of them.
   Finished episodes are cached in `outputs/cache/`, so a re-run continues where it stopped. Use `--fresh` to redo everything.

## Swap the model
Edit the three settings at the top of `llm.py`: `PROVIDER` ("gemini" or "groq"), `MODEL_NAME`, `SLEEP_BETWEEN_CALLS`. Nothing else changes.

## Outputs (in `outputs/`)
`ranking.md` (top promos), `all_candidates.json` (every valid scored pick), `rejected.json` (rejected picks with reasons), `run_log.txt` (model, calls, tokens, time, rejection counts).

## Known limits
- Works from the script text only, not the video, so it cannot judge acting or visuals.
- Only joins moments inside one episode, not across episodes.
- The AI scores are opinions; a human editor should approve the final picks.
