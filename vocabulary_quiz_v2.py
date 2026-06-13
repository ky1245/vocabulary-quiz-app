"""
Vocabulary Quiz App
====================
A simple English-Korean vocabulary flashcard and quiz application
built with Python, Tkinter (ttkbootstrap), and JSON storage.

Features:
- Add / delete / clear vocabulary words
- Round-based quiz: every registered word is shown exactly once per round
- Per-word correct/wrong statistics saved to JSON
- Bar chart visualization of quiz results (matplotlib)

Author: Student Project
Course: Introduction to Open Source Software
"""

import json
import random
import os
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# ── File paths ─────────────────────────────────────────────────────────────────
DATA_FILE   = "words.json"        # word list  { "apple": {"meaning": "사과", "correct": 3, "wrong": 1} }
HISTORY_FILE = "round_history.json"  # round history [ {"round": 1, "correct": 4, "wrong": 1, "pct": 80}, ... ]


def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history: list) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ── Persistence helpers ────────────────────────────────────────────────────────
def load_words() -> dict:
    """Load vocabulary from JSON file. Returns empty dict if file doesn't exist."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Migrate old flat format  {"apple": "사과"}  →  new format
        migrated = {}
        for word, val in data.items():
            if isinstance(val, dict):
                migrated[word] = val
            else:
                migrated[word] = {"meaning": val, "correct": 0, "wrong": 0}
        return migrated
    return {}


def save_words(words: dict) -> None:
    """Save vocabulary dictionary to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)


# ── Main Application ───────────────────────────────────────────────────────────
class VocabularyApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.title("📚 Vocabulary Quiz App")
        self.geometry("680x580")
        self.resizable(False, False)

        self.words: dict = load_words()            # { word: {meaning, correct, wrong} }
        self.round_history: list = load_history()  # list of per-round result dicts

        # ── Quiz round state ──
        self.quiz_queue:    list = []   # words remaining this round
        self.current_word:  str  = ""
        self.round_correct: int  = 0
        self.round_wrong:   int  = 0
        self.wrong_words:   list = []   # words answered incorrectly this round
        self.is_retry_mode: bool = False  # True when replaying wrong words only

        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.notebook = ttk.Notebook(self, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.tab_manage = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_manage, text="  📖 Word Manager  ")
        self._build_manage_tab()

        self.tab_quiz = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_quiz, text="  🎯 Quiz  ")
        self._build_quiz_tab()

        self.tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stats, text="  📊 Statistics  ")
        self._build_stats_tab()

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 1 – Word Manager
    # ══════════════════════════════════════════════════════════════════════════
    def _build_manage_tab(self):
        frame = self.tab_manage

        input_frame = ttk.Labelframe(frame, text=" Add New Word ", bootstyle="primary", padding=12)
        input_frame.pack(fill=X, padx=15, pady=(15, 8))

        ttk.Label(input_frame, text="English Word:",   font=("Helvetica", 11)).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.entry_word = ttk.Entry(input_frame, width=30, font=("Helvetica", 11))
        self.entry_word.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Korean Meaning:", font=("Helvetica", 11)).grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.entry_meaning = ttk.Entry(input_frame, width=30, font=("Helvetica", 11))
        self.entry_meaning.grid(row=1, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="➕ Add Word",        bootstyle="success",         command=self.add_word,    width=14).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 Delete Selected", bootstyle="danger",          command=self.delete_word, width=16).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Clear All",       bootstyle="warning-outline", command=self.clear_all,   width=12).pack(side=LEFT, padx=5)

        self.list_frame = ttk.Labelframe(frame, text=f" Word List ({len(self.words)} words) ",
                                         bootstyle="info", padding=10)
        self.list_frame.pack(fill=BOTH, expand=True, padx=15, pady=8)

        cols = ("English", "Korean Meaning", "Correct", "Wrong")
        self.tree = ttk.Treeview(self.list_frame, columns=cols, show="headings",
                                 bootstyle="info", height=10)
        self.tree.heading("English",        text="English Word")
        self.tree.heading("Korean Meaning", text="Korean Meaning (뜻)")
        self.tree.heading("Correct",        text="✅ Correct")
        self.tree.heading("Wrong",          text="❌ Wrong")
        self.tree.column("English",        width=180, anchor=CENTER)
        self.tree.column("Korean Meaning", width=220, anchor=CENTER)
        self.tree.column("Correct",        width=80,  anchor=CENTER)
        self.tree.column("Wrong",          width=80,  anchor=CENTER)

        sb = ttk.Scrollbar(self.list_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        self._refresh_list()

    def add_word(self):
        word    = self.entry_word.get().strip().lower()
        meaning = self.entry_meaning.get().strip()
        if not word or not meaning:
            messagebox.showwarning("Input Error", "Please fill in both fields!")
            return
        if word in self.words:
            messagebox.showinfo("Duplicate", f"'{word}' already exists.")
            return
        self.words[word] = {"meaning": meaning, "correct": 0, "wrong": 0}
        save_words(self.words)
        self.entry_word.delete(0, END)
        self.entry_meaning.delete(0, END)
        self._refresh_list()
        messagebox.showinfo("Success", f"✅ '{word}' has been added!")

    def delete_word(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a word to delete.")
            return
        word = self.tree.item(selected[0])["values"][0].lower()
        if messagebox.askyesno("Confirm Delete", f"Delete '{word}'?"):
            del self.words[word]
            save_words(self.words)
            self._refresh_list()

    def clear_all(self):
        if not self.words:
            messagebox.showinfo("Empty", "The word list is already empty.")
            return
        if messagebox.askyesno("Confirm", "Clear ALL words? This cannot be undone."):
            self.words = {}
            save_words(self.words)
            self._refresh_list()

    def _refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for word, info in sorted(self.words.items()):
            self.tree.insert("", END, values=(
                word, info["meaning"], info["correct"], info["wrong"]
            ))
        self.list_frame.config(text=f" Word List ({len(self.words)} words) ")

    # ══════════════════════════════════════════════════════════════════════════
    # Tab 2 – Quiz  (round-based: every word shown exactly once per round)
    # ══════════════════════════════════════════════════════════════════════════
    def _build_quiz_tab(self):
        frame = self.tab_quiz

        # ── Top info bar ──
        top = ttk.Frame(frame)
        top.pack(fill=X, padx=15, pady=(15, 5))

        self.lbl_progress = ttk.Label(top, text="Round not started",
                                      font=("Helvetica", 11), bootstyle="secondary")
        self.lbl_progress.pack(side=LEFT)

        self.lbl_score = ttk.Label(top, text="Score: 0 / 0  (0%)",
                                   font=("Helvetica", 12, "bold"), bootstyle="info")
        self.lbl_score.pack(side=RIGHT)

        # ── Card ──
        card = ttk.Labelframe(frame, text=" Quiz Card ", bootstyle="primary", padding=20)
        card.pack(fill=BOTH, expand=True, padx=15, pady=8)

        self.lbl_question = ttk.Label(card,
                                      text="Press 'Start Round' to begin!",
                                      font=("Helvetica", 18, "bold"),
                                      anchor=CENTER, wraplength=580)
        self.lbl_question.pack(pady=(20, 10))

        ttk.Label(card, text="Type the Korean meaning:", font=("Helvetica", 11)).pack()

        self.entry_answer = ttk.Entry(card, width=30, font=("Helvetica", 13), justify=CENTER)
        self.entry_answer.pack(pady=10)
        self.entry_answer.bind("<Return>", lambda e: self.check_answer())

        self.lbl_result = ttk.Label(card, text="", font=("Helvetica", 14, "bold"))
        self.lbl_result.pack(pady=8)

        # ── Buttons ──
        btn_frame = ttk.Frame(card)
        btn_frame.pack(pady=10)

        self.btn_start = ttk.Button(btn_frame, text="▶ Start Round",
                                    bootstyle="success", command=self.start_round, width=14)
        self.btn_start.pack(side=LEFT, padx=6)

        self.btn_check = ttk.Button(btn_frame, text="✅ Submit Answer",
                                    bootstyle="primary", command=self.check_answer, width=16,
                                    state=DISABLED)
        self.btn_check.pack(side=LEFT, padx=6)

        self.btn_next = ttk.Button(btn_frame, text="⏭ Next Word",
                                   bootstyle="info-outline", command=self.next_question, width=13,
                                   state=DISABLED)
        self.btn_next.pack(side=LEFT, padx=6)

        self.btn_retry = ttk.Button(btn_frame, text="🔁 Retry Wrong",
                                    bootstyle="warning", command=self.retry_wrong_words, width=14,
                                    state=DISABLED)
        self.btn_retry.pack(side=LEFT, padx=6)

    # ── Round logic ────────────────────────────────────────────────────────────
    def start_round(self):
        """Shuffle all words into a queue and begin the round."""
        if len(self.words) < 1:
            messagebox.showwarning("No Words", "Please add words in the Word Manager tab first!")
            return

        self.quiz_queue    = random.sample(list(self.words.keys()), len(self.words))
        self.round_correct = 0
        self.round_wrong   = 0
        self.wrong_words   = []
        self.is_retry_mode = False
        self.lbl_result.config(text="")
        self.btn_check.config(state=NORMAL)
        self.btn_next.config(state=DISABLED)
        self.btn_retry.config(state=DISABLED)
        self._next_from_queue()

    def _next_from_queue(self):
        """Pop the next word from the queue and display it."""
        if not self.quiz_queue:
            self._finish_round()
            return

        self.current_word = self.quiz_queue.pop(0)
        remaining = len(self.quiz_queue) + 1          # including current
        total     = len(self.words)
        done      = total - remaining

        self.lbl_question.config(text=self.current_word)
        self.lbl_result.config(text="")
        self.lbl_progress.config(text=f"Word {done + 1} / {total}")
        self.entry_answer.delete(0, END)
        self.entry_answer.focus()
        self.btn_check.config(state=NORMAL)
        self.btn_next.config(state=DISABLED)

    def next_question(self):
        """Called after the user has already answered — advance to next word."""
        self._next_from_queue()

    def check_answer(self):
        """Evaluate the typed answer, update stats."""
        if not self.current_word:
            messagebox.showinfo("No Question", "Press 'Start Round' first!")
            return

        user_answer = self.entry_answer.get().strip()
        if not user_answer:
            messagebox.showwarning("Empty Answer", "Please type an answer!")
            return

        correct_answer = self.words[self.current_word]["meaning"]

        if user_answer == correct_answer:
            self.words[self.current_word]["correct"] += 1
            self.round_correct += 1
            self.lbl_result.config(text=f"✅  Correct!  ({correct_answer})", bootstyle="success")
        else:
            self.words[self.current_word]["wrong"] += 1
            self.round_wrong += 1
            self.wrong_words.append(self.current_word)
            self.lbl_result.config(text=f"❌  Wrong!  Answer: {correct_answer}", bootstyle="danger")

        save_words(self.words)
        self._refresh_list()

        total    = self.round_correct + self.round_wrong
        pct      = int(self.round_correct / total * 100)
        self.lbl_score.config(text=f"Score: {self.round_correct} / {total}  ({pct}%)")

        self.current_word = ""          # prevent double-submit
        self.btn_check.config(state=DISABLED)

        # If words remain show Next button, else auto-finish after short delay
        if self.quiz_queue:
            self.btn_next.config(state=NORMAL)
        else:
            self.after(800, self._finish_round)

    def _finish_round(self):
        """Round complete — save history, show summary, switch to Statistics tab."""
        total = self.round_correct + self.round_wrong
        if total == 0:
            return

        self.current_word = ""
        self.btn_check.config(state=DISABLED)
        self.btn_next.config(state=DISABLED)

        # Save round result to history (only for full rounds, not retry sessions)
        if not self.is_retry_mode:
            pct = int(self.round_correct / total * 100)
            round_num = len(self.round_history) + 1
            self.round_history.append({
                "round":   round_num,
                "correct": self.round_correct,
                "wrong":   self.round_wrong,
                "pct":     pct
            })
            save_history(self.round_history)

        pct = int(self.round_correct / total * 100)
        mode_label = "오답 복습" if self.is_retry_mode else f"Round {len(self.round_history)}"
        summary = (
            f"🎉  {mode_label} Complete!\n\n"
            f"Correct : {self.round_correct}\n"
            f"Wrong   : {self.round_wrong}\n"
            f"Score   : {pct}%"
        )
        self.lbl_question.config(text=summary)
        self.lbl_result.config(text="")
        self.lbl_progress.config(text="Round finished — see Statistics tab!")

        # Enable retry button only if there are wrong words
        if self.wrong_words:
            self.btn_retry.config(state=NORMAL)
        else:
            self.btn_retry.config(state=DISABLED)

        # Refresh chart and jump to Stats tab
        self._refresh_chart()
        self.notebook.select(self.tab_stats)

    def retry_wrong_words(self):
        """Start a new mini-round with only the words answered incorrectly."""
        if not self.wrong_words:
            messagebox.showinfo("No Wrong Words", "No wrong words to retry!")
            return
        self.quiz_queue    = random.sample(self.wrong_words, len(self.wrong_words))
        self.wrong_words   = []
        self.round_correct = 0
        self.round_wrong   = 0
        self.is_retry_mode = True
        self.lbl_result.config(text="")
        self.btn_check.config(state=NORMAL)
        self.btn_next.config(state=DISABLED)
        self.btn_retry.config(state=DISABLED)
        self.notebook.select(self.tab_quiz)
        self._next_from_queue()

    # ══════════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════════
    def _build_stats_tab(self):
        frame = self.tab_stats

        top = ttk.Frame(frame)
        top.pack(fill=X, padx=15, pady=(12, 4))
        ttk.Label(top, text="Round-by-Round Performance",
                  font=("Helvetica", 13, "bold"), bootstyle="primary").pack(side=LEFT)
        ttk.Button(top, text="🗑 Clear History", bootstyle="danger-outline",
                   command=self.clear_history, width=14).pack(side=RIGHT)
        ttk.Button(top, text="💾 Save Chart (PNG)", bootstyle="info-outline",
                   command=self.save_chart, width=18).pack(side=RIGHT, padx=6)
        ttk.Button(top, text="🔄 Refresh", bootstyle="secondary-outline",
                   command=self._refresh_chart, width=10).pack(side=RIGHT, padx=6)

        # Matplotlib canvas placeholder
        self.chart_frame = ttk.Frame(frame)
        self.chart_frame.pack(fill=BOTH, expand=True, padx=10, pady=6)

        self.fig, self.ax = plt.subplots(figsize=(6.5, 3.8), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=True)

        self._refresh_chart()

    def _refresh_chart(self):
        """Redraw the bar chart showing round-by-round correct/wrong rates."""
        self.ax.clear()

        if not self.round_history:
            self.ax.text(0.5, 0.5, "No round data yet.\nComplete a quiz round first!",
                         ha="center", va="center", fontsize=13,
                         transform=self.ax.transAxes, color="#888888")
            self.ax.set_axis_off()
            self.canvas.draw()
            return

        labels  = [f"{h['round']}" for h in self.round_history]
        correct = [h["correct"] for h in self.round_history]
        wrong   = [h["wrong"]   for h in self.round_history]
        pcts    = [h["pct"]     for h in self.round_history]

        x     = list(range(len(labels)))
        width = 0.35

        bars1 = self.ax.bar([i - width / 2 for i in x], correct, width,
                            label="correct", color="#4CAF50", zorder=3)
        bars2 = self.ax.bar([i + width / 2 for i in x], wrong,   width,
                            label="wrong", color="#F44336", zorder=3)

        # Annotate each group with the score percentage
        for i, pct in enumerate(pcts):
            self.ax.text(i, max(correct[i], wrong[i]) + 0.15,
                         f"{pct}%", ha="center", va="bottom",
                         fontsize=9, fontweight="bold", color="#333333")

        self.ax.set_xticks(x)
        self.ax.set_xticklabels(labels, fontsize=10)
        self.ax.set_ylabel("Count", fontsize=10)
        self.ax.set_title("Round-by-Round Results",
                          fontsize=12, fontweight="bold")
        self.ax.legend(fontsize=9)
        self.ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        self.ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
        self.ax.bar_label(bars1, padding=2, fontsize=8)
        self.ax.bar_label(bars2, padding=2, fontsize=8)
        self.fig.tight_layout()
        self.canvas.draw()

    def clear_history(self):
        """Delete all round history."""
        if not self.round_history:
            messagebox.showinfo("Empty", "No history to clear.")
            return
        if messagebox.askyesno("Confirm", "Clear all round history? This cannot be undone."):
            self.round_history = []
            save_history(self.round_history)
            self._refresh_chart()

    def save_chart(self):
        """Save the current chart to stats.png."""
        quizzed = {w: i for w, i in self.words.items() if i["correct"] + i["wrong"] > 0}
        if not quizzed:
            messagebox.showinfo("No Data", "Take a quiz first, then save the chart.")
            return
        self.fig.savefig("stats.png", dpi=150, bbox_inches="tight")
        messagebox.showinfo("Saved", "Chart saved as  stats.png  in the project folder.")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = VocabularyApp()
    app.mainloop()
