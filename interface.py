import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import numpy as np
import os

# Set page configuration (must be the first Streamlit command)
st.set_page_config(page_title="CMS Doctor Interface 🏥", page_icon="🏥")

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

# Cache data loading to optimize performance
@st.cache
def load_data():
    file_path = 'Doctor_Matching_With_Procedures_Separate_Sheets_V2.xlsx'
    if os.path.exists(file_path):
        doctor_matching_df = pd.read_excel(file_path, sheet_name='Doctor_Matching')
        procedure_prioritization_df = pd.read_excel(file_path, sheet_name='Procedure_Prioritization')
        insurance_payments_df = pd.read_excel(file_path, sheet_name='Insurance Payment Avgs')
        return doctor_matching_df, procedure_prioritization_df, insurance_payments_df
    else:
        return None, None, None

if check_password():
    # Load the data with a loading spinner
    with st.spinner("Loading data..."):
        doctor_matching_df, procedure_prioritization_df, insurance_payments_df = load_data()
        
    if doctor_matching_df is None:
        st.error("Data file not found. Please ensure the file is uploaded correctly.")
        st.stop()

    # Clean the data by filling NaN values in relevant columns
    doctor_matching_df.fillna('', inplace=True)
    procedure_prioritization_df.fillna('', inplace=True)
    insurance_payments_df.fillna('', inplace=True)

    # Convert 'Prioritization Index' to numeric to handle mixed types
    doctor_matching_df['Prioritization Index'] = pd.to_numeric(doctor_matching_df['Prioritization Index'], errors='coerce')
    procedure_prioritization_df['Prioritization Index Procedure'] = pd.to_numeric(procedure_prioritization_df['Prioritization Index Procedure'], errors='coerce')

    # Improved Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Home", "Doctor Profile Lookup", "Insurance Payment Averages"],
        index=["Home", "Doctor Profile Lookup", "Insurance Payment Averages"].index(st.session_state.current_page),
        key='navigation'
    )
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
        st.download_button(label="Download Top Doctors as CSV", data=top_doctors.to_csv(index=False), file_name='top_doctors.csv', mime='text/csv')

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
            st.download_button(label="Download Procedure Ranking as CSV", data=filtered_procedures.to_csv(index=False), file_name='procedure_ranking.csv', mime='text/csv')

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
    
                # Display information in card format using beta_columns (or st.columns)
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"- **Specialty:** {first_entry['Specialty']}")
                    insurances = ', '.join(doctor_data['Insurance'].unique())
                    st.write(f"- **Insurances:** {insurances}")
                with col2:
                    luis_gerardo_alex = first_entry['Luis, Gerardo o Alex']
                    st.write(f"- **Luis, Gerardo o Alex:** {'YES, ' + luis_gerardo_alex if luis_gerardo_alex else 'NO'}")
                    max_referrals = doctor_data['Referrals'].max()
                    st.write(f"- **Max Referrals in a Month:** {max_referrals}")

                # Procedures Done Section
                procedures = procedure_prioritization_df[
                    (procedure_prioritization_df['Referring Physician'] == doctor_name) &
                    (procedure_prioritization_df['Prioritization Index Procedure'].notna())
                ].reset_index(drop=True)
                
                procedure_info = []
                for _, row in procedures.iterrows():
                    procedure_name = row['Procedure']
                    procedure_rank_data = procedure_prioritization_df[
                        (procedure_prioritization_df['Procedure'] == procedure_name) &
                        (procedure_prioritization_df['Prioritization Index Procedure'].notna())
                    ].sort_values(by='Prioritization Index Procedure', ascending=False).reset_index(drop=True)
                    procedure_rank = procedure_rank_data[procedure_rank_data['Referring Physician'] == doctor_name].index
                    
                    if len(procedure_rank) > 0:
                        procedure_rank = procedure_rank[0] + 1
                        total_procedures = len(procedure_rank_data)
                        if procedure_rank <= total_procedures:
                            procedure_info.append(f"{procedure_name} (Rank: {procedure_rank}/{total_procedures})")
                
                if procedure_info:
                    st.write(f"- **Procedures Done:** {', '.join(procedure_info)}")
                else:
                    st.write("- **Procedures Done:** Not Available")
