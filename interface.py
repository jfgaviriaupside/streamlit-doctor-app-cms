import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import numpy as np

# Set page configuration (must be the first Streamlit command)
st.set_page_config(page_title="Doctor Prioritization Interface", page_icon="🏥")

# Simple password authentication
def check_password():
    st.sidebar.title("Login")
    password = st.sidebar.text_input("Password", type="password")
    if password == "your_password_here":
        return True
    else:
        if password:
            st.sidebar.error("Incorrect password")
        return False

if check_password():
    # Load the data (use your own file path)
    doctor_matching_df = pd.read_excel('Doctor_Matching_With_Procedures_Separate_Sheets.xlsx', sheet_name='Doctor_Matching')
    procedure_prioritization_df = pd.read_excel('Doctor_Matching_With_Procedures_Separate_Sheets.xlsx', sheet_name='Procedure_Prioritization')
    insurance_payments_df = pd.read_excel('Insurace_Payments.xlsx', sheet_name='Insurance Payment Avgs')

    # Clean the data by filling NaN values in relevant columns
    doctor_matching_df.fillna('', inplace=True)
    procedure_prioritization_df.fillna('', inplace=True)
    insurance_payments_df.fillna('', inplace=True)

    # Convert 'Prioritization Index' to numeric to handle mixed types
    doctor_matching_df['Prioritization Index'] = pd.to_numeric(doctor_matching_df['Prioritization Index'], errors='coerce')
    procedure_prioritization_df['Prioritization Index Procedure'] = pd.to_numeric(procedure_prioritization_df['Prioritization Index Procedure'], errors='coerce')

    # Main navigation options
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Doctor Profile Lookup", "Insurance Payment Averages"])

    if page == "Home":
        st.title("Doctor Prioritization Interface")

        # Automatically display a list of top-priority doctors sorted by general prioritization index
        st.write("## Top Priority Doctors")
        top_doctors = doctor_matching_df[['Referring Physician', 'Prioritization Index', 'Specialty', 'Insurance', 'Referrals', 'Luis, Gerardo o Alex']]
        top_doctors = top_doctors.sort_values(by='Prioritization Index', ascending=False).drop_duplicates(subset='Referring Physician').head(50).reset_index(drop=True)
        top_doctors['Rank'] = top_doctors.index + 1
        top_doctors['Insurance'] = top_doctors.groupby('Referring Physician')['Insurance'].transform(lambda x: ', '.join(x.unique()))
        top_doctors['Luis, Gerardo o Alex'] = top_doctors['Luis, Gerardo o Alex'].apply(lambda x: f"YES, {x}" if x else "NO")
        top_doctors = top_doctors[['Rank', 'Referring Physician', 'Specialty', 'Insurance', 'Referrals', 'Luis, Gerardo o Alex']]

        st.write(top_doctors)

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
            # Cross-reference 'Luis, Gerardo o Alex' from doctor_matching_df
            filtered_procedures = filtered_procedures.merge(doctor_matching_df[['Referring Physician', 'Luis, Gerardo o Alex']].drop_duplicates(subset='Referring Physician'), on='Referring Physician', how='left')
            filtered_procedures['Luis, Gerardo o Alex'] = filtered_procedures['Luis, Gerardo o Alex'].apply(lambda x: f"YES, {x}" if x else "NO")
            filtered_procedures = filtered_procedures[['Rank', 'Referring Physician', 'Procedure', 'Prioritization Index Procedure', 'Referrals', 'Luis, Gerardo o Alex']]
            
            # Display prioritization index and rank
            st.write(filtered_procedures)

        # Add a specialty-wise ranking table
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

    elif page == "Doctor Profile Lookup":
        st.title("Doctor Profile Lookup")

        # Autocomplete search for doctor name
        doctor_name = st.selectbox("Search for a doctor by name:", options=doctor_matching_df['Referring Physician'].unique(), index=0)

        # Filter the data based on the search input
        if doctor_name:
            doctor_data = doctor_matching_df[doctor_matching_df['Referring Physician'] == doctor_name]
            
            if not doctor_data.empty:
                # Display the "once-only" information in a more structured and intuitive way
                first_entry = doctor_data.iloc[0]  # Take the first row of the filtered data for once-only data
                st.write(f"## Doctor Profile: {first_entry['Referring Physician']}")
                rank_data = doctor_matching_df[['Referring Physician', 'Prioritization Index']].sort_values(by='Prioritization Index', ascending=False).reset_index(drop=True)
                rank = rank_data[rank_data['Referring Physician'] == first_entry['Referring Physician']].index
                if len(rank) > 0:
                    rank = rank[0] + 1
                    total_doctors = len(rank_data)
                    st.write(f"- **Rank:** {rank}/{total_doctors}")
                else:
                    st.write("- **Rank:** Not Available")
                
                # Tabs for organizing information
                tab1, tab2, tab3 = st.tabs(["General Info", "Addresses and Contact Information", "Map of Locations"])
                
                with tab1:
                    st.write(f"- **Specialty:** {first_entry['Specialty']}")
                    insurances = ', '.join(doctor_data['Insurance'].unique())
                    st.write(f"- **Insurances:** {insurances}")
                    luis_gerardo_alex = first_entry['Luis, Gerardo o Alex']
                    st.write(f"- **Luis, Gerardo o Alex:** {'YES, ' + luis_gerardo_alex if luis_gerardo_alex else 'NO'}")
                    procedures = procedure_prioritization_df[(procedure_prioritization_df['Referring Physician'] == doctor_name) & (procedure_prioritization_df['Prioritization Index Procedure'].notna())]
                    procedure_info = []
                    for _, row in procedures.iterrows():
                        procedure_name = row['Procedure']
                        procedure_rank_data = procedure_prioritization_df[(procedure_prioritization_df['Procedure'] == procedure_name) & (procedure_prioritization_df['Prioritization Index Procedure'].notna())]
                        procedure_rank = procedure_rank_data[procedure_rank_data['Referring Physician'] == doctor_name].index
                        if len(procedure_rank) > 0:
                            procedure_rank = procedure_rank[0] + 1
                            total_procedures = len(procedure_rank_data)
                            if procedure_rank <= total_procedures:
                                procedure_info.append(f"{procedure_name} (Rank: {procedure_rank}/{total_procedures})")
                    if procedure_info:
                        st.write(f"- **Procedures Done:** {', '.join(procedure_info)}")
                    max_referrals
