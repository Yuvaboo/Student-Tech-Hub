# Student Skill & Project Recommendation System
## Built from scratch with scikit-learn + Streamlit

---

## 🗂 Project Structure

```
student_ml_from_scratch/
├── data/
│   ├── student_recommendation_10000_no_difficulty.csv   ← raw dataset
│   └── cleaned_dataset.csv                              ← created by load_data.py
├── models/
│   ├── student_project_model.pkl                        ← saved trained model
│   └── _test_split.pkl                                  ← saved test split
├── reports/
│   ├── evaluation_results.json                          ← all metrics
│   ├── classification_report.txt                        ← per-class metrics
│   └── regression_report.txt                            ← optional regression
├── src/
│   ├── load_data.py       ← Step 2: Load & inspect
│   ├── prepare_data.py    ← Step 3: Feature definitions & pipeline builder
│   ├── train_model.py     ← Step 4: Train & save model
│   ├── evaluate_model.py  ← Step 5 + 6: Evaluate classification & regression
│   └── predict.py         ← Step 7: Predict from a student profile
├── app.py                 ← Step 8: Streamlit web app
├── requirements.txt
└── README.md
```

---

## ✅ How to Run (Beginner-Friendly)

Open your terminal (Command Prompt or PowerShell), **navigate to the project folder**, and run the steps below **in order**.

### Step 0 — Navigate to the project folder

```powershell
cd "c:\Users\yuvas\New folder\New folder\student_ml_from_scratch"
```

### Step 1 — Install required packages (only once)

```powershell
pip install -r requirements.txt
```

> **Note:** On this workstation, a preconfigured virtual environment is located at `C:\Users\yuvas\New folder\.venv`. You can activate it with:
> ```powershell
> ..\..\.venv\Scripts\Activate.ps1
> ```
> Or invoke Python directly with: `..\..\.venv\Scripts\python.exe <script>`

---

### Step 2 — Load and inspect the dataset

```powershell
python src/load_data.py
```

**What it does:**
- Checks that the CSV file exists.
- Prints the number of rows, columns, dtypes, missing values, and class distribution.
- Saves a cleaned copy to `data/cleaned_dataset.csv`.

---

### Step 3 — Inspect data preparation (optional check)

```powershell
python src/prepare_data.py
```

**What it does:**
- Confirms all required feature columns are present.
- Reports whether stratification is safe during training.

---

### Step 4 — Train the model

```powershell
python src/train_model.py
```

**What it does:**
- Splits data 80/20 (train/test).
- Trains **Logistic Regression** and **Random Forest**.
- Picks the better model.
- Saves it to `models/student_project_model.pkl`.

---

### Step 5 — Evaluate the model

```powershell
python src/evaluate_model.py
```

**What it does:**
- Loads the saved model (no retraining).
- Computes Training Accuracy, Test Accuracy, Precision, Recall, F1-score.
- Prints the Confusion Matrix and Classification Report.
- Also runs an optional regression experiment on `Available_Hours_Per_Week`.
- Saves all results to `reports/`.

---

### Step 6 — Test a prediction

```powershell
python src/predict.py
```

**What it does:**
- Loads the saved model once.
- Runs 4 example predictions and prints the recommended project for each.

---

### Step 7 — Launch the Streamlit web app

```powershell
streamlit run app.py
```

**What it does:**
- Opens a browser tab with a student form.
- Fill in your details and click **Get My Recommendation**.
- Displays the recommended project + model metrics + limitations.

---

## 📌 Important Notes

| Topic | Detail |
|---|---|
| **Dataset** | Synthetically generated — 10,000 student records |
| **Target** | `Recommended_Project` (multi-class classification) |
| **Features** | Year, Department, Current_Skills (TF-IDF), Interest, Available_Hours_Per_Week |
| **Model** | Best of Logistic Regression vs Random Forest |
| **Accuracy caveat** | High accuracy = good fit to *synthetic* data, not real-world quality |
| **Regression** | Predicts `Available_Hours_Per_Week`; kept separate; low R² expected |

---

## ⚠️ Limitations

- The model was trained on **synthetic (fake) data**. It cannot reliably recommend projects for real students.
- Real-world use would require real survey or academic records.
- This project is educational — it demonstrates the complete ML pipeline.

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `FileNotFoundError: cleaned_dataset.csv` | Run `python src/load_data.py` first |
| `FileNotFoundError: student_project_model.pkl` | Run `python src/train_model.py` first |
| Streamlit shows "model not found" | Train the model first, then relaunch |
| `streamlit: command not found` | Run `pip install streamlit` |
