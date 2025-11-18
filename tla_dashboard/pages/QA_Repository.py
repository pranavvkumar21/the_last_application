"""
Q&A Repository Page - Manage and analyze form questions and answers
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.styles import apply_custom_css
from utils.db_helper import get_question_analytics, get_db_manager
from config import COLORS, CHART_HEIGHT

# Page config
st.set_page_config(page_title="Q&A Repository", page_icon="📋", layout="wide")
apply_custom_css()

# Header
st.title("📋 Q&A Repository")
st.markdown("### Manage questions and answers from job applications")
st.markdown("---")

try:
    db = get_db_manager()
    
    # Q&A Statistics
    with db.get_connection() as conn:
        qa_stats = conn.execute("""
            SELECT 
                COUNT(DISTINCT fq.question_id) as total_questions,
                COUNT(DISTINCT fr.response_id) as total_responses,
                COUNT(DISTINCT fr.application_id) as applications_with_qa
            FROM form_questions fq
            LEFT JOIN form_responses fr ON fq.question_id = fr.question_id
        """).fetchone()
        
        if qa_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Unique Questions", qa_stats[0] or 0)
            
            with col2:
                st.metric("Total Responses", qa_stats[1] or 0)
            
            with col3:
                st.metric("Applications with Q&A", qa_stats[2] or 0)
            
            with col4:
                avg_questions = (qa_stats[1] / qa_stats[2]) if qa_stats[2] and qa_stats[2] > 0 else 0
                st.metric("Avg Questions/Application", f"{avg_questions:.1f}")
    
    st.markdown("---")
    
    # Question analytics
    st.markdown("## 📊 Question Analytics")
    
    questions_df = get_question_analytics()
    
    if not questions_df.empty:
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            question_type_filter = st.multiselect(
                "Question Type",
                options=questions_df['type'].unique().tolist(),
                default=None
            )
        
        with col2:
            min_frequency = st.number_input("Min Frequency", min_value=0, value=1, step=1)
        
        with col3:
            search_question = st.text_input("🔎 Search Questions", placeholder="Enter keywords...")
        
        # Apply filters
        filtered_df = questions_df.copy()
        
        if question_type_filter:
            filtered_df = filtered_df[filtered_df['type'].isin(question_type_filter)]
        
        if min_frequency > 0:
            filtered_df = filtered_df[filtered_df['times_asked'] >= min_frequency]
        
        if search_question:
            filtered_df = filtered_df[
                filtered_df['question'].str.contains(search_question, case=False, na=False)
            ]
        
        st.markdown(f"### 📋 Found {len(filtered_df)} questions")
        
        # Questions table
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "question": st.column_config.TextColumn("Question", width="large"),
                "type": "Type",
                "times_asked": st.column_config.NumberColumn("Frequency", format="%d"),
                "most_common_answer": st.column_config.TextColumn("Most Common Answer", width="medium")
            }
        )
        
        st.markdown("---")
        
        # Question analytics charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Question Type Distribution")
            type_counts = questions_df['type'].value_counts()
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title='Questions by Type',
                hole=0.4,
                color_discrete_sequence=[COLORS['primary'], COLORS['secondary'], COLORS['info'], COLORS['success']]
            )
            fig.update_layout(height=CHART_HEIGHT)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🔥 Most Frequent Questions")
            top_questions = questions_df.nlargest(10, 'times_asked')
            fig = px.bar(
                top_questions,
                y='question',
                x='times_asked',
                orientation='h',
                title='Top 10 Most Asked Questions',
                labels={'question': '', 'times_asked': 'Times Asked'},
                color='times_asked',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=CHART_HEIGHT, yaxis={'categoryorder':'total ascending'})
            fig.update_yaxes(ticktext=[q[:50] + '...' if len(q) > 50 else q for q in top_questions['question']])
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Detailed question view
        st.markdown("## 🔍 Question Details")
        
        question_options = {
            f"{row['question'][:80]}... ({row['times_asked']} times)": row['question']
            for _, row in filtered_df.iterrows()
        }
        
        selected_question_key = st.selectbox(
            "Select a question to view details",
            options=list(question_options.keys())
        )
        
        if selected_question_key:
            selected_question = question_options[selected_question_key]
            question_data = filtered_df[filtered_df['question'] == selected_question].iloc[0]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 📝 Question")
                st.info(question_data['question'])
                
                st.markdown("### 📊 Statistics")
                st.markdown(f"**Type:** {question_data['type']}")
                st.markdown(f"**Times Asked:** {question_data['times_asked']}")
                st.markdown(f"**Most Common Answer:** {question_data['most_common_answer']}")
            
            with col2:
                st.markdown("### 💡 Answer Insights")
                
                # Get all answers for this question
                with db.get_connection() as conn:
                    answers_result = conn.execute("""
                        SELECT 
                            fr.response_value,
                            COUNT(*) as frequency
                        FROM form_responses fr
                        JOIN form_questions fq ON fr.question_id = fq.question_id
                        WHERE fq.question_text = ?
                        GROUP BY fr.response_value
                        ORDER BY frequency DESC
                        LIMIT 10
                    """, [selected_question]).fetchall()
                    
                    if answers_result:
                        answers_df = pd.DataFrame(answers_result, columns=['answer', 'frequency'])
                        
                        # Answer distribution chart
                        fig = px.bar(
                            answers_df,
                            x='frequency',
                            y='answer',
                            orientation='h',
                            title='Answer Distribution',
                            labels={'answer': 'Answer', 'frequency': 'Frequency'},
                            color='frequency',
                            color_continuous_scale='Greens'
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No answer data available")
            
            st.markdown("---")
            
            # Applications that included this question
            with db.get_connection() as conn:
                apps_result = conn.execute("""
                    SELECT 
                        a.application_id,
                        j.title,
                        j.company,
                        fr.response_value,
                        a.status,
                        a.applied_date
                    FROM form_responses fr
                    JOIN form_questions fq ON fr.question_id = fq.question_id
                    JOIN applications a ON fr.application_id = a.application_id
                    JOIN jobs j ON a.job_id = j.job_id
                    WHERE fq.question_text = ?
                    ORDER BY a.applied_date DESC
                    LIMIT 50
                """, [selected_question]).fetchall()
                
                if apps_result:
                    apps_df = pd.DataFrame(
                        apps_result,
                        columns=['app_id', 'job_title', 'company', 'your_answer', 'status', 'applied_date']
                    )
                    
                    st.markdown("### 📋 Recent Applications with this Question")
                    apps_df['applied_date'] = pd.to_datetime(apps_df['applied_date']).dt.strftime('%Y-%m-%d')
                    
                    st.dataframe(
                        apps_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "app_id": "App ID",
                            "job_title": "Job Title",
                            "company": "Company",
                            "your_answer": "Your Answer",
                            "status": "Status",
                            "applied_date": "Applied Date"
                        }
                    )
        
        st.markdown("---")
        
        # Answer templates section
        st.markdown("## 📝 Answer Templates")
        st.info("💡 **Coming Soon:** Manage default answers and create templates for common questions")
        
        with st.expander("➕ Add New Template"):
            template_question = st.text_input("Question Pattern", placeholder="e.g., How many years of experience...")
            template_answer = st.text_area("Default Answer", placeholder="Enter your standard answer...")
            
            if st.button("💾 Save Template"):
                st.success("✅ Template saved successfully!")
        
        st.markdown("---")
        
        # Export section
        st.markdown("## 📥 Export Q&A Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export Questions", use_container_width=True):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    "questions_repository.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("📋 Generate Q&A Report", use_container_width=True):
                st.info("📄 Detailed Q&A report generation coming soon!")
    
    else:
        st.info("📭 No Q&A data available yet. Apply to more jobs to build your question repository!")

except Exception as e:
    st.error(f"❌ Error loading Q&A repository: {str(e)}")
    with st.expander("🔍 Error Details"):
        st.code(str(e))
