import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import numpy as np
import os
from io import BytesIO

# Set page configuration (must be the first Streamlit command)
st.set_page_config(page_title="CMS Doctor Interface 🏥", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# Define a consistent dark color palette
theme_colors = {
    "primary": "#1E3F6A",
    "secondary": "#EA622E",
    "accent": "#49A281",
    "background": "#1E1E1E",
    "text": "#F5F5F5"
}

# Set custom CSS for consistent styling
def set_custom_css():
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {theme_colors['background']};
        }}
        .css-18e3th9 {{
            color: {theme_colors['text']};
        }}
        .css-1d391kg p {{
            color: {theme_colors['text']};
        }}
        .css-1v0mbdj {{
            color: {theme_colors['text']};
        }}
        .css-10trblm a {{
            color: {theme_colors['accent']};
        }}
        .css-1aumxhk .st-bm {{
            background-color: {theme_colors['primary']};
            color: white;
        }}
        .css-1aumxhk .st-bm:hover {{
            background-color: {theme_colors['secondary']};
            color: white;
        }}
        </style>
    """, unsafe_allow_html=True)

set_custom_css()

# Simple password authentication
def check_password():
    st.sidebar.title("Login")
    password = st.sidebar.text_input("Password", type="password")
    if password == "Upside":
        return True
    else:
        if password:
            st.sidebar.error("Incorrect password")
        return False

# Function to navigate pages using session state
def navigate_to(page_name):
    st.session_state.current_page = page_name

# Initialize session state if not already set
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

if check_password():
    # Load the data (use your own file path)
    @st.cache
    def load_data():
        file_path = 'Doctor_Matching_With_Procedures_Separate_Sheets_V2.xlsx'
        if os.path.exists(file_path):
            doctor_matching_df = pd.read_excel(file_path, sheet_name='Doctor_Matching')
            procedure_prioritization_df = pd.read_excel(file_path, sheet_name='Procedure_Prioritization')
            insurance_payments_df = pd.read_excel(file_path, sheet_name='Insurance Payment Avgs')
            return doctor_matching_df, procedure_prioritization_df, insurance_payments_df
        else:
            st.error("Data file not found. Please ensure the file is uploaded correctly.")
            st.stop()

    with st.spinner("Loading data..."):
        doctor_matching_df, procedure_prioritization_df, insurance_payments_df = load_data()

    # Clean the data by filling NaN values in relevant columns
    doctor_matching_df.fillna('', inplace=True)
    procedure_prioritization_df.fillna('', inplace=True)
    insurance_payments_df.fillna('', inplace=True)

    # Convert 'Prioritization Index' to numeric to handle mixed types
    doctor_matching_df['Prioritization Index'] = pd.to_numeric(doctor_matching_df['Prioritization Index'], errors='coerce')
    procedure_prioritization_df['Prioritization Index Procedure'] = pd.to_numeric(procedure_prioritization_df['Prioritization Index Procedure'], errors='coerce')

    # Main navigation options
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Home", "Doctor Profile Lookup", "Insurance Payment Averages"],
                                index=["Home", "Doctor Profile Lookup", "Insurance Payment Averages"].index(st.session_state.current_page),
                                key='navigation')
    navigate_to(page)

    # Home Page
    if st.session_state.current_page == "Home":
        st.title("Doctor Prioritization Interface")

        # Display a list of top-priority doctors sorted by general prioritization index
        st.write("## Top Priority Doctors")
        top_doctors = doctor_matching_df[['Referring Physician', 'Prioritization Index', 'Specialty', 'Insurance', 'Referrals', 'Luis, Gerardo o Alex', 'CAGR']]
        top_doctors = top_doctors.sort_values(by='Prioritization Index', ascending=False).drop_duplicates(subset='Referring Physician').reset_index(drop=True)
        top_doctors['Rank'] = top_doctors.index + 1
        top_doctors['Insurance'] = top_doctors.groupby('Referring Physician')['Insurance'].transform(lambda x: ', '.join(x.unique()))
        top_doctors['Luis, Gerardo o Alex'] = top_doctors['Luis, Gerardo o Alex'].apply(lambda x: f"YES, {x}" if x else "NO")

        top_doctors['CAGR'] = pd.to_numeric(top_doctors['CAGR'], errors='coerce').apply(lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "N/A")
        top_doctors = top_doctors[['Rank', 'Referring Physician', 'Specialty', 'Insurance', 'CAGR', 'Referrals', 'Luis, Gerardo o Alex']]

        st.write(top_doctors)
        towrite = BytesIO()
        top_doctors.to_excel(towrite, index=False, sheet_name='Top Doctors')
        towrite.seek(0)
        st.download_button("Download Top Doctors Data", data=towrite, file_name="top_doctors.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Procedure Prioritization Ranking for All Doctors
        st.write("## Procedure Prioritization Ranking")
        available_procedures = procedure_prioritization_df['Procedure'].unique()
        selected_procedure = st.selectbox("Select a procedure to view the ranking of doctors:", available_procedures)

        if selected_procedure:
            filtered_procedures = procedure_prioritization_df[
                (procedure_prioritization_df['Procedure'] == selected_procedure) &
                (procedure_prioritization_df['Prioritization Index Procedure'].notna())
            ].sort_values(by='Prioritization Index Procedure', ascending=False).drop_duplicates(subset='Referring Physician').reset_index(drop=True)
            filtered_procedures['Rank'] = filtered_procedures.index + 1
            filtered_procedures = filtered_procedures.merge(doctor_matching_df[['Referring Physician', 'Luis, Gerardo o Alex']].drop_duplicates(subset='Referring Physician'), on='Referring Physician', how='left')
            filtered_procedures['Luis, Gerardo o Alex'] = filtered_procedures['Luis, Gerardo o Alex'].apply(lambda x: f"YES, {x}" if x else "NO")
            filtered_procedures['CAGR'] = pd.to_numeric(filtered_procedures['CAGR'], errors='coerce').apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) else "N/A")
            filtered_procedures = filtered_procedures[['Rank', 'Referring Physician', 'Procedure', 'CAGR', 'Referrals', 'Luis, Gerardo o Alex']]

            st.write(filtered_procedures)
            towrite = BytesIO()
            filtered_procedures.to_excel(towrite, index=False, sheet_name='Procedure Ranking')
            towrite.seek(0)
            st.download_button("Download Procedure Ranking Data", data=towrite, file_name="procedure_ranking.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Specialty-wise ranking table
        st.write("## Doctors Ranked by Specialty")
        available_specialties = doctor_matching_df['Specialty'].unique()
        selected_specialty = st.selectbox("Select a specialty to view the ranking of doctors:", available_specialties)

        if selected_specialty:
            filtered_specialty = doctor_matching_df[
                doctor_matching_df['Specialty'] == selected_specialty
            ].sort_values(by='Prioritization Index', ascending=False).drop_duplicates(subset='Referring Physician').reset_index(drop=True)
            filtered_specialty['Rank'] = filtered_specialty.index + 1
            filtered_specialty['Insurance'] = filtered_specialty.groupby('Referring Physician')['Insurance'].transform(lambda x: ', '.join(x.unique()))
            filtered_specialty['Luis, Gerardo o Alex'] = filtered_specialty['Luis, Gerardo o Alex'].apply(lambda x: f"YES, {x}" if x else "NO")
            filtered_specialty = filtered_specialty[['Rank', 'Referring Physician', 'Specialty', 'Insurance', 'Referrals', 'Luis, Gerardo o Alex']]

            st.write(filtered_specialty)
            towrite = BytesIO()
            filtered_specialty.to_excel(towrite, index=False, sheet_name='Specialty Ranking')
            towrite.seek(0)
            st.download_button("Download Specialty Ranking Data", data=towrite, file_name="specialty_ranking.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Doctor Profile Lookup Page
    elif st.session_state.current_page == "Doctor Profile Lookup":
        st.title("Doctor Profile Lookup")
    
        doctor_name = st.selectbox("Search for a doctor by name:", options=doctor_matching_df['Referring Physician'].unique(), index=0)
    
        if doctor_name:
            doctor_data = doctor_matching_df[doctor_matching_df['Referring Physician'] == doctor_name]
    
            if not doctor_data.empty:
                first_entry = doctor_data.iloc[0]
                st.write(f"## Doctor Profile: {first_entry['Referring Physician']}")
                rank_data = doctor_matching_df[['Referring Physician', 'Prioritization Index']].sort_values(by='Prioritization Index', ascending=False).reset_index(drop=True)
                rank = rank_data[rank_data['Referring Physician'] == first_entry['Referring Physician']].index
                if len(rank) > 0:
                    rank = rank[0] + 1
                    total_doctors = len(rank_data)
                    st.write(f"- **Rank:** {rank}/{total_doctors}")
                else:
                    st.write("- **Rank:** Not Available")
    
               
