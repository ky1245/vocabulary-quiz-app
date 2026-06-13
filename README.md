# Vocabulary Quiz App

An English–Korean vocabulary flashcard and quiz application built with Python.  
Add your own words, take round-based quizzes, review mistakes, and track your
progress across multiple rounds with a built-in bar chart.

---

## Features

| Feature | Description |
|---|---|
| **Word Manager** | Add, delete, or clear English–Korean vocabulary entries |
| **Persistent Storage** | Words and quiz history are saved to JSON files — data survives app restarts |
| **Round-Based Quiz** | Every word in the list appears exactly once per round (no repeats) |
| **Retry Wrong Words** | After a round, replay only the words you answered incorrectly |
| **Round History Chart** | Bar chart shows correct/wrong counts per round (1회차, 2회차, …) with score % |
| **Clear History** | Reset round history at any time |
| **Save Chart as PNG** | Export the statistics chart as `stats.png` |

---

## Tools & Libraries

| Library | Type | Purpose |
|---|---|---|
| `tkinter` | Built-in | Core GUI framework |
| `ttkbootstrap` | **External** | Modern themed widgets (`flatly` theme) |
| `matplotlib` | **External** | Round-by-round bar chart in the Statistics tab |
| `json` | Built-in | Persistent storage (`words.json`, `round_history.json`) |
| `random` | Built-in | Shuffle word order each round |
| `os` | Built-in | Check if data files exist on startup |

---

## Project Structure

```
vocabulary_quiz/
│
├── vocabulary_quiz_v2.py  # Main application source code
├── words.json             # Auto-generated: vocabulary data
├── round_history.json     # Auto-generated: quiz round results
├── stats.png              # Auto-generated when chart is saved
├── requirements.txt       # External library list
├── README.md              # Project documentation (this file)
├── short_report.pdf       # Project report
└── LICENSE                # MIT License
```

---

## ▶ How to Run

### 1. Clone or download the project
```bash
git clone [https://https://github.com/ky1245/vocabulary-quiz-app.git](https://github.com/ky1245/vocabulary-quiz-app.git)
cd vocabulary-quiz-app

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
python vocabulary_quiz_v2.py
```

> **Requires Python 3.8 or higher.**  
> On Windows, `tkinter` is included with the standard Python installer.  
> On Linux, install it with `sudo apt install python3-tk` if needed.

---

## How to Use

### Tab 1 — Word Manager
1. Type an English word and its Korean meaning.
2. Click **➕ Add Word** to save it.
3. Select a row and click **🗑 Delete Selected** to remove a word.
4. The list shows cumulative correct/wrong counts for each word.

### Tab 2 — Quiz
1. Click **▶ Start Round** — every word appears once in random order.
2. Type the Korean meaning and press **Enter** or click **Submit Answer**.
3. The result is shown immediately (green = correct, red = wrong).
4. Click **⏭ Next Word** to continue.
5. When the round ends, click **Retry Wrong** to practice only the words you missed.

### Tab 3 — Statistics
- A bar chart shows **correct (green)** and **wrong (red)** counts for each round.
- The X-axis shows **1회차, 2회차, 3회차 …** (Round 1, 2, 3 …).
- The score percentage is displayed above each round's bars.
- Click **💾 Save Chart (PNG)** to export the chart as `stats.png`.
- Click **🗑 Clear History** to reset the round records.

---

## Sample Test Cases

| # | Action | Input | Expected Output |
|---|---|---|---|
| 1 | Add valid word | `apple` / `사과` | Word appears in the list |
| 2 | Quiz – Correct answer | Question: `apple`, Answer: `사과` | Correct! Score increases |
| 3 | Quiz – Wrong answer | Question: `apple`, Answer: `바나나` | Wrong! Correct answer shown |
| 4 | Empty input | Both fields blank | Warning popup appears |
| 5 | Retry wrong words | Click 🔁 Retry Wrong after a round | Mini-round starts with missed words only |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

> MIT License: free to use, modify, and distribute with attribution.
