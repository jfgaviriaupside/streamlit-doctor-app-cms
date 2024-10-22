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
    if password == "Upside":
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
            filtered_procedures = filtered_procedures[['Rank', 'Referring Physician', 'Procedure', 'Referrals', 'Luis, Gerardo o Alex']]
            
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
                    max_referrals = doctor_data['Referrals'].max()
                    st.write(f"- **Max Referrals in a Month:** {max_referrals}")
                    cagr_last_3_months = doctor_data['CAGR'].iloc[0] * 100 if 'CAGR' in doctor_data.columns and not doctor_data['CAGR'].isna().iloc[0] else None
                    st.write(f"- **3 Last Month CAGR:** {cagr_last_3_months:.2f}%" if cagr_last_3_months is not None else "- **3 Last Month CAGR:** Not Available")
                
                with tab2:
                    st.write("### Addresses and Contact Information:")
                    addresses = doctor_data[['Insurance', 'Address', 'Phone Number', 'Latitude', 'Longitude']].drop_duplicates()
                    for _, row in addresses.iterrows():
                        st.write(f"  - **Address:** {row['Address']}")
                        st.write(f"  - **Phone Number:** {row['Phone Number']}")
                        st.write(f"  - **Gotten from:** {row['Insurance']}")
                        st.write("---")

                with tab3:
                    st.write("### Map of Locations:")
                    # Create a folium map centered at an average location
                    avg_lat = doctor_data['Latitude'].mean() if 'Latitude' in doctor_data.columns else 0
                    avg_lon = doctor_data['Longitude'].mean() if 'Longitude' in doctor_data.columns else 0
                    doctor_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
                    
                    # Add markers for each location
                    for _, row in doctor_data.iterrows():
                        if row['Latitude'] and row['Longitude']:
                            folium.Marker(
                                location=[row['Latitude'], row['Longitude']],
                                popup=f"{row['Referring Physician']} - {row['Specialty']}",
                                icon=folium.Icon(color='blue', icon='info-sign')
                            ).add_to(doctor_map)
                    
                    # Add a standard location marker for "CMS Diagnostic Services"
                    folium.Marker(
                        location=[25.701410, -80.342660],
                        popup="CMS Diagnostic Services",
                        icon=folium.Icon(color='red', icon='hospital')
                    ).add_to(doctor_map)
                    
                    # Display the map in Streamlit
                    folium_static(doctor_map)
            else:
                st.write("No doctor found with that name.")

        # Add a button to go back to the main page
        if st.button("Back to Home"):
            st.session_state.page = "Home"
            st.experimental_rerun()

    elif page == "Insurance Payment Averages":
        st.title("Insurance Payment Averages per Procedure")

        # Filter by procedure
        available_procedures = insurance_payments_df['Procedure'].unique()
        selected_procedure = st.selectbox("Select a procedure to view insurance payment averages:", available_procedures)

        if selected_procedure:
            filtered_payments = insurance_payments_df[insurance_payments_df['Procedure'] == selected_procedure]
            filtered_payments = filtered_payments[['Insurance', 'Avg Payment', 'Margin']]
            filtered_payments = filtered_payments[filtered_payments['Insurance'] != '']
            filtered_payments['Avg Payment'] = pd.to_numeric(filtered_payments['Avg Payment'], errors='coerce').apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
            filtered_payments['Margin'] = pd.to_numeric(filtered_payments['Margin'], errors='coerce').apply(lambda x: f"{int(x)}%" if pd.notnull(x) else "N/A")
            filtered_payments['Avg Payment'] = pd.to_numeric(filtered_payments['Avg Payment'].str.replace('[\$,]', '', regex=True), errors='coerce')
            filtered_payments = filtered_payments.sort_values(by='Avg Payment', ascending=False).reset_index(drop=True)
            
            # Display payment averages and margin without row numbers
            st.write(filtered_payments)

    # Set the session state for navigation
    if 'page' not in st.session_state:
        st.session_state.page = "Home"

    if st.session_state.page != page:
        st.session_state.page = page
        st.experimental_rerun()
