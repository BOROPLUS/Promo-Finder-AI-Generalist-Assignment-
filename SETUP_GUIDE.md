# Setup guide: where every file goes

## 1. Final folder layout
```
promo-finder/                  <- your existing folder
├── parse.py
├── prompt_utils.py
├── llm.py
├── find.py
├── validate.py
├── judge.py
├── rank.py
├── run_all.py
├── test_validate.py
├── requirements.txt
├── README.md
├── .gitignore
├── mistakes_log.md            (keep yours, add lines as you go)
├── step1_check.py             (optional, keep or delete)
├── episodes/                  <- your 50 .txt files stay here
└── outputs/                   <- created results go here
```

## 2. Put the files in place
1. Download `promo-finder.zip` and extract it to your Desktop.
2. Open the extracted `promo-finder` folder, select everything inside it, and copy.
3. Paste into your real folder: `C:\Users\hp\Desktop\Projects\KUKU Assignment\promo-finder`.
4. When Windows asks about files with the same name, choose **Replace the files in the destination**. This replaces your old `llm.py`, `find.py`, `prompt_utils.py` and `parse.py` with versions that work together.
5. Do **not** touch your `episodes` folder. The zip has an empty one; if Windows asks, choose **Skip** for folders.

## 3. Run, in this order (PowerShell)
Use one PowerShell window for all of it.

1. Go to the folder:
```
cd "C:\Users\hp\Desktop\Projects\KUKU Assignment\promo-finder"
```
2. Install the libraries (only needed once):
```
& "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" -m pip install -r requirements.txt
```
3. Set your NEW API key (create a new one in AI Studio, delete the old one):
```
$env:LLM_API_KEY="your-new-key"
```
4. Test the rules (no AI). Expect `All tests passed.`:
```
& "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" test_validate.py
```
5. Test the AI connection. Expect a 3-word greeting:
```
& "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" llm.py
```
6. Test one episode end to end:
```
& "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" run_all.py --episodes 42
```
Open `outputs\ranking.md` and `outputs\run_log.txt`. Read the promos against the script.
7. Try 3 episodes, then the full run (about 20 to 40 minutes, my estimate):
```
& "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" run_all.py --limit 3
& "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" run_all.py
```
If it stops on a rate-limit error, wait a few minutes and run the same command again. Finished episodes are cached and are not redone.

## 4. After the full run
- Your raw outputs are in `outputs\` (`ranking.md`, `all_candidates.json`, `rejected.json`, `run_log.txt`). Do not edit them.
- Do Step 7 of the plan: grade 10 picks by reading the script, and list the common failures.
- Use `run_log.txt` for the cost and scale numbers in your doc.
- Keep `mistakes_log.md` for the "where the AI got it wrong" part.

## 5. If something fails
- `model not found`: change `MODEL_NAME` at the top of `llm.py`.
- `ModuleNotFoundError`: you ran the wrong Python. Use the full-path command above.
- Anything else: paste the full error here.
