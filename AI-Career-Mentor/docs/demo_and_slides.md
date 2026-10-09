# AI Career & Project Mentor - Presentation & Demo

## 🎤 2-Minute Demo Script

**Speaker:** 
"Hello everyone, today I want to show you the AI Career & Project Mentor. Have you ever felt lost trying to pick a project that perfectly aligns with your skills, year of study, and available time? We solve exactly that."

*(Opens the Streamlit App - Tab 1)*
"Here, a 2nd-year IT student enters their profile. They know basic Python and HTML, have 10 hours a week, and are interested in AI. Let's click 'Generate'."

*(App loads and switches to Tab 2)*
"Under the hood, our ML engine uses Sentence-Transformers to match them to a 'Machine Learning Stock Predictor' project. Since they lack Pandas and Scikit-Learn, the engine calculates a realistic difficulty of 75% and estimates a duration of 12 weeks. 
But we don’t stop there. Our Gemini-powered LLM layer gives them a personalized reason for this project, along with a week-by-week roadmap, the exact tools they need, and beginner YouTube videos for the missing skills."

*(Switches to Tab 4 - Chatbot)*
"Now, what if they get stuck or fall behind? Our AI Twin records their context into a ChromaDB vector store. If they ask the chatbot a question, it replies strictly in the context of their specific stock predictor project. Furthermore, if they check off tasks slower than the roadmap dictates, the AI twin automatically notices they are falling behind and proposes an adjusted schedule. Lastly, background jobs send email reminders so they never miss a milestone."

"This is the future of personalized education. Thank you!"

---

## 📊 Presentation Slide Outlines (6 Slides)

### Slide 1: Title Slide
- **Title:** AI Career & Project Mentor for Students
- **Subtitle:** Personalized learning roadmaps via ML & LLM Hybrid AI.
- **Visuals:** Clean logo, a flowchart connecting a student profile to a finished project.

### Slide 2: The Problem
- **Headline:** Students Are Overwhelmed by Choices
- **Points:** 
  - Don't know which skills to learn.
  - Pick projects that are too hard or irrelevant.
  - Lack structure, planning, and mentorship.
  - Struggle with time management.

### Slide 3: The Solution
- **Headline:** A Personalized, Data-Driven Mentor
- **Points:**
  - Evaluates current skills vs. project requirements.
  - Generates a customized week-by-week roadmap.
  - Recommends free tools and YouTube tutorials.
  - Tracks progress and sends email reminders.

### Slide 4: System Architecture (Hybrid Design)
- **Headline:** How It Works
- **Visual Diagram representation:**
  - *Input Form* (Streamlit)
  - *FastAPI Backend*
  - *ML Engine:* (Sentence-Transformers) for project matching and difficulty heuristics.
  - *LLM Layer:* (Gemini API) for qualitative reasoning, tool recommendations, and career vision via Structured Outputs.
  - *RAG & Scheduler:* ChromaDB for memory, APScheduler for tasks.

### Slide 5: The AI Twin Concept
- **Headline:** Your Persistent Mentor
- **Points:**
  - System remembers student profile and project context.
  - **Dynamic Pacing:** Senses if tasks are marked complete. If falling behind, the chatbot adjusts its tone and deadlines.
  - **Context-Aware:** Answers doubts specifically about *their* project, not general knowledge.

### Slide 6: Future Scope & Conclusion
- **Headline:** What's Next?
- **Points:**
  - Scrape GitHub to continuously auto-update the projects repository.
  - Train an XGBoost model on actual student completion rates for precise difficulty predictions.
  - Integrate with GitHub to auto-verify task completion based on commits.
- **Call to Action:** Scan QR code for the Live Demo.
