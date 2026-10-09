# 🎓 Student Skill & Project Recommendation System

A production-ready Machine Learning system that recommends tailored academic/capstone projects, required learning skills, and developer tools to students based on their **academic year**, **department**, **current skills**, **primary interest**, and **available weekly hours**.

---

## 📌 Project Overview & Objectives

In higher education, students often struggle to identify suitable projects that match their current technical abilities and career ambitions. This project builds a transparent, leak-free machine learning classification pipeline to predict `Recommended_Project` from student profile characteristics, accompanied by mapped learning paths (`Recommended_Skills`, `Recommended_Tools`, and contextual `Recommendation_Reason`).

### Input Features:
- `Year`: Academic year (`1st Year`, `2nd Year`, `3rd Year`, `4th Year`)
- `Department`: Student's engineering / science department (`CSE`, `IT`, `ECE`, `EEE`, `Mechanical`, `Civil`, `Biotechnology`, `Microbiology`, `BCA`, `BSc`)
- `Current_Skills`: Comma-separated text representing skills already acquired (e.g., `"Python, pandas"`, `"HTML, CSS"`, `"C Basics, electronics"`)
- `Interest`: Student's domain interest (e.g., `"Data Science"`, `"AI"`, `"IoT"`, `"Web Development"`)
- `Available_Hours_Per_Week`: Available study/development time per week (integer / float)

### Outputs:
- **Recommended Project**: Predicted suitable project title (49 target classes)
- **Recommended Skills**: Key skills needed to complete the project
- **Recommended Tools**: Recommended software tools, libraries, or frameworks
- **Recommendation Rationale**: Explanation adapted to student background and weekly bandwidth

---

## 📂 Project Structure

```text
student_recommendation_ml/
├── data/
│   ├── student_recommendation_10000_no_difficulty.csv  # Raw dataset (10,000 records)
│   └── cleaned_dataset.csv                             # Cleaned dataset without whitespace/anomalies
├── models/
│   ├── student_project_model.pkl                       # Serialized champion pipeline + metadata
│   └── student_hours_regression_model.pkl              # Experimental regression model (Task 4)
├── reports/
│   ├── evaluation_results.json                         # Comprehensive JSON evaluation report
│   └── classification_report.txt                       # Per-class precision, recall, and F1 scores
├── src/
│   ├── load_data.py                                    # Data ingestion and schema validation
│   ├── prepare_data.py                                 # Cleaning, encoding, and train/test splitting
│   ├── train_model.py                                  # Classifier training, CV, and regression test
│   ├── evaluate_model.py                               # Performance metrics, reports & overfitting check
│   └── predict.py                                      # Inference engine and CLI recommendation tool
├── app.py                                              # Interactive Streamlit Web Application
├── requirements.txt                                    # Project dependencies
└── README.md                                           # Complete project documentation
```

---

## 🔍 Dataset Analysis & Findings

1. **Volume & Integrity**: 10,000 student records across 10 departments and 49 target project classes. No missing values or corrupt rows.
2. **Output Isolation**: Output columns (`Recommended_Skills`, `Recommended_Tools`, `Recommendation_Reason`) and identifier (`Student_ID`) were strictly isolated from model inputs to prevent data leakage.
3. **Synthetic Rule Graph**: Analysis revealed that the dataset was generated using deterministic associative rules: exactly 98 distinct `(Interest, Current_Skills)` combinations exist, and each maps deterministically to a specific project.
4. **Deterministic Mapping of Associated Outputs**: For each `Recommended_Project`, `Recommended_Skills` and `Recommended_Tools` are 1-to-1 mappings.

---

## ⚙️ Data Preprocessing & Pipeline Architecture

To prevent data leakage, all preprocessing transformations are encapsulated within a scikit-learn `ColumnTransformer` and fit exclusively on the training split:
- **Categorical Columns (`Year`, `Department`, `Interest`)**: Encoded using `OneHotEncoder(handle_unknown='ignore')`.
- **Free-Text Skills (`Current_Skills`)**: Vectorized using `TfidfVectorizer(token_pattern=r'(?u)\b[\w-]+\b', ngram_range=(1, 2))`.
- **Numerical Features (`Available_Hours_Per_Week`)**: Scaled using `StandardScaler()`.

Data is partitioned into **80% training (8,000 samples)** and **20% testing (2,000 samples)** using stratified splitting on the target project class.

---

## 📊 Model Evaluation & Benchmarks

Two candidate classification architectures were evaluated using 5-fold stratified cross-validation on the training set:

| Model Architecture | 5-Fold CV Accuracy | Train Accuracy | Test Accuracy | Macro Precision | Macro Recall | Macro F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Multinomial Logistic Regression** *(Champion)* | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |
| **Random Forest Classifier (100 Trees)** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

### Overfitting & Generalization Diagnosis:
- **Training Accuracy**: 1.0000 (8,000 samples)
- **Test Accuracy**: 1.0000 (2,000 samples)
- **Generalization Gap**: `0.0000`
- Both models perfectly reproduce the underlying rule graph without memorizing training noise.
- **Champion Selection**: `LogisticRegression` was selected for production deployment because it delivers identical accuracy with a substantially smaller memory footprint (5.4 KB vs 12+ MB for tree ensembles) and faster inference latency (< 5ms).

> ⚠️ **Synthetic Dataset Reality Check**:
> While the model achieves 1.0000 accuracy on this synthetic benchmark, **this does not establish 100% accuracy in real-world environments**. Real-world student data features typos, ambiguous skill phrases, conflicting interests, and subjective choices.

---

## 🔬 Task 4: Available Hours Regression Experiment

A dedicated regression study evaluated whether student background (`Year`, `Department`, `Current_Skills`, `Interest`) could predict `Available_Hours_Per_Week`:

- **Ridge Regression Test $R^2$**: `0.0561`
- **Random Forest Regressor Test $R^2$**: `0.0038`
- **Ridge Test RMSE**: `5.35` hours (vs. Dataset Standard Deviation: `5.46` hours)
- **Ridge Test MAE**: `4.43` hours

### Senior ML Engineer Conclusion:
The near-zero $R^2$ demonstrates that **student background contains virtually zero predictive signal regarding weekly available study hours**. Available hours were assigned quasi-randomly in the synthetic generation process.
Deploying an ML model to predict hours would be unscientific and produce misleading predictions. Therefore, available study hours is correctly treated as an **independent user input**, while the regression findings are documented in `reports/evaluation_results.json`.

---

## 🚀 Quickstart & How to Run

### 1. Environment Setup

```bash
# Navigate to the project directory
cd student_recommendation_ml

# Create and activate a Python virtual environment (Python 3.10+ recommended)
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Inspect Dataset
```bash
python src/load_data.py
```

### 3. Clean and Prepare Data
```bash
python src/prepare_data.py
```

### 4. Train the ML Model
```bash
python src/train_model.py
```

### 5. Evaluate the Saved Model
```bash
python src/evaluate_model.py
```

### 6. Run CLI Prediction with Sample Student Profile
```bash
python src/predict.py --year "3rd Year" --dept "CSE" --skills "Python, pandas" --interest "Data Science" --hours 15
```

### 7. Launch the Streamlit Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🌐 Deployment to Streamlit Community Cloud

To deploy this app publicly:

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "feat: complete student project recommendation ML system"
   git remote add origin https://github.com/<your-username>/student-recommendation-ml.git
   git push -u origin main
   ```
2. **Deploy on Streamlit Community Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io).
   - Sign in with your GitHub account.
   - Click **"New app"**.
   - Select your repository: `<your-username>/student-recommendation-ml`.
   - Set the Main file path to: `app.py` (or `student_recommendation_ml/app.py` if rooted in a subfolder).
   - Click **"Deploy!"**.
3. **Verification**:
   - Streamlit will automatically install dependencies from `requirements.txt` and launch the app with model caching.

---

## 📄 License
This project is open-source and available under the Apache 2.0 License.
