import pandas as pd
from fuzzywuzzy import process
from tqdm import tqdm

# Load your files
doctor_file_path = 'Doctor Research CMS (3).xlsx'
prioritization_file_path = 'Final_Adjusted_Dropoff_Prioritization_Index.xlsx'

# Read the main doctor data
doctor_data = pd.read_excel(doctor_file_path, sheet_name='Main')

# Read both sheets from the prioritization file
prioritization_data = pd.read_excel(prioritization_file_path, sheet_name=0)
prioritization_procedures = pd.read_excel(prioritization_file_path, sheet_name=1)

# Standardize doctor names
def standardize_name(name):
    if isinstance(name, str):
        return name.replace('MD', '').replace(',', '').strip().lower()
    return ''

doctor_data['Standardized Doctor Name'] = doctor_data['Doctor Name'].apply(standardize_name)
prioritization_data['Standardized Referring Physician'] = prioritization_data['Referring Physician'].apply(standardize_name)
prioritization_procedures['Standardized Referring Physician'] = prioritization_procedures['Referring Physician'].apply(standardize_name)

# Fuzzy matching function with a similarity threshold
def fuzzy_match_doctor(doctor_name, doctor_list):
    result = process.extractOne(doctor_name, doctor_list)
    if result:
        return result[0], result[1]  # return both the match and score
    return None, 0

# Apply fuzzy matching with progress updates
matched_doctors = []
scores = []

print("Matching doctors, please wait...")

for doctor in tqdm(prioritization_data['Standardized Referring Physician'], desc="Matching Doctors"):
    matched_doctor, score = fuzzy_match_doctor(doctor, doctor_data['Standardized Doctor Name'])
    matched_doctors.append(matched_doctor)
    scores.append(score)

# Add the matched doctor names and scores to the prioritization data
prioritization_data['Matched Doctor'] = matched_doctors
prioritization_data['Score'] = scores

# Filter out low-score matches (keeping only those above 85)
prioritization_data_filtered = prioritization_data[prioritization_data['Score'] > 85]

# Merge data with matches
matched_data = pd.merge(prioritization_data_filtered, doctor_data, how='left', left_on='Matched Doctor', right_on='Standardized Doctor Name')

# Handle non-matched doctors, keeping all prioritization data
unmatched_data = prioritization_data[prioritization_data['Score'] <= 85].copy()

# Append unmatched doctors to the final dataset
final_data = pd.concat([matched_data, unmatched_data], ignore_index=True)

# Save the final data to Excel, keeping all columns from both sheets
output_file = 'Doctor_Matching_With_Procedures_Separate_Sheets.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Save the main matching result to one sheet
    final_data.to_excel(writer, sheet_name='Doctor_Matching', index=False)

    # Save the prioritization procedures to a separate sheet
    prioritization_procedures.to_excel(writer, sheet_name='Procedure_Prioritization', index=False)

print(f"Matching process complete. Results saved to '{output_file}' with separate sheets.")
