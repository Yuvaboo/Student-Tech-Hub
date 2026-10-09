import streamlit as st
import requests
import json
import pandas as pd

# Assume Backend is running on port 8000
API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Career & Project Mentor", layout="wide")

st.title("🎓 AI Career & Project Mentor for Students")
st.markdown("Discover the best projects and skills tailored to your profile, powered by ML and LLMs.")

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'ml_results' not in st.session_state:
    st.session_state.ml_results = None
if 'llm_results' not in st.session_state:
    st.session_state.llm_results = None
if 'youtube_links' not in st.session_state:
    st.session_state.youtube_links = None

tabs = st.tabs(["Profile Input", "Dashboard & Roadmap", "Career Path", "AI Twin & Chatbot"])

with tabs[0]:
    st.header("Step 1: Build Your Profile")
    with st.form("profile_form"):
        email = st.text_input("Email (for reminders)")
        col1, col2 = st.columns(2)
        year = col1.number_input("Year of Study", min_value=1, max_value=5, value=2)
        department = col2.selectbox("Department", ["CSE", "IT", "ECE", "EEE", "Mech", "Civil", "Other"])
        
        current_skills = st.text_input("Current Skills (comma separated)", "Python, HTML")
        interests = st.text_input("Interests/Domains (comma separated)", "AI/ML, Web Development")
        weekly_hours = st.slider("Available Time (hours/week)", 1, 40, 10)
        
        submit = st.form_submit_button("Generate Personalized Plan")
        
    if submit:
        if not email:
            st.error("Please provide an email.")
        else:
            with st.spinner("Analyzing profile with ML and Gemini LLM..."):
                payload = {
                    "email": email,
                    "year": year,
                    "department": department,
                    "current_skills": [s.strip() for s in current_skills.split(",")],
                    "interests": [s.strip() for s in interests.split(",")],
                    "weekly_hours": weekly_hours
                }
                try:
                    res = requests.post(f"{API_URL}/recommend", json=payload)
                    res.raise_for_status()
                    data = res.json()
                    st.session_state.user_id = data['user_id']
                    st.session_state.ml_results = data['ml_results']
                    st.session_state.llm_results = data['llm_results']
                    st.session_state.youtube_links = data['youtube']
                    st.success("Plan generated successfully! Move to the next tabs.")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")

with tabs[1]:
    if st.session_state.ml_results:
        st.header("🏆 Recommended Project")
        ml = st.session_state.ml_results
        llm = st.session_state.llm_results
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Project Difficulty", f"{ml['difficulty_percentage']}%")
        col2.metric("Estimated Duration", ml['duration'])
        col3.metric("Missing Skills", ml['missing_skills_count'])
        
        st.subheader(ml['recommended_project']['title'])
        st.write(f"**Domain:** {ml['recommended_project']['domain']}")
        st.write(f"**Description:** {ml['recommended_project']['description']}")
        
        st.info(f"**Why this project?** {llm['reason']}")
        
        st.subheader("📚 Skill Gap & Resources")
        st.write(f"You need to learn: **{', '.join(ml['recommended_skills'])}**")
        
        if st.session_state.youtube_links:
            for skill, videos in st.session_state.youtube_links.items():
                with st.expander(f"YouTube Tutorials for {skill}"):
                    for v in videos:
                        st.markdown(f"- [{v['title']}]({v['url']})")
                        
        st.subheader("🗓️ Week-by-Week Roadmap & Reminders")
        roadmap = llm.get('week_by_week_roadmap', [])
        for task in roadmap:
            st.markdown(f"**Week {task['week']}:** {task['task']} _({task['hours_required']} hrs)_")
            st.caption(f"Milestone: {task['milestone']}")
        
        st.subheader("🛠️ Tools Required")
        tools_df = pd.DataFrame(llm.get('tools', []))
        if not tools_df.empty:
            st.table(tools_df)
    else:
        st.warning("Please fill out your profile first.")

with tabs[2]:
    if st.session_state.llm_results:
        st.header("🚀 Futuristic Career View")
        roles = st.session_state.llm_results.get('career_roles', [])
        for r in roles:
            with st.container():
                st.subheader(r['role'])
                st.write(f"**Required Skills:** {', '.join(r['required_skills'])}")
                st.write(f"**5-Year Outlook:** {r['outlook_5_years']}")
                st.divider()
    else:
        st.warning("Please fill out your profile first.")

with tabs[3]:
    if st.session_state.user_id:
        st.header("🤖 AI Twin & Chatbot")
        
        # Progress View
        st.subheader("Your Progress")
        try:
            prog_res = requests.get(f"{API_URL}/progress/{st.session_state.user_id}")
            if prog_res.status_code == 200:
                tasks = prog_res.json()
                total = len(tasks)
                completed = sum(1 for t in tasks if t['is_completed'])
                prog = int((completed/total)*100) if total > 0 else 0
                st.progress(prog / 100.0, text=f"{prog}% Completed ({completed}/{total} Tasks)")
                
                # Checkboxes to mark complete
                for t in tasks:
                    checked = st.checkbox(f"Week {t['week']}: {t['task_desc']}", value=t['is_completed'], key=f"task_{t['id']}")
                    if checked and not t['is_completed']:
                        requests.post(f"{API_URL}/task/complete", json={"task_id": t['id']})
                        st.rerun()
        except:
            st.write("Could not load progress.")

        st.divider()
        st.subheader("Chat with your Project Mentor")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask a doubt about your project or roadmap..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        chat_res = requests.post(f"{API_URL}/chat", json={"user_id": st.session_state.user_id, "message": prompt})
                        reply = chat_res.json().get("reply", "Error generating response.")
                    except:
                        reply = "Backend error."
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
    else:
        st.warning("Please fill out your profile first.")
