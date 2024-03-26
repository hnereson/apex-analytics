import pandas as pd
import boto3 
import json  
from io import StringIO  
import streamlit as st
from datetime import datetime, timedelta 
from PIL import Image 
from io import BytesIO
import incident_scope_questions as incident_questions

MASTER_ACCESS_KEY = st.secrets["MASTER_ACCESS_KEY"]
MASTER_SECRET = st.secrets["MASTER_SECRET"]

def s3_init():  
    
    # --- s3 client --- 
    s3 = boto3.client('s3', region_name = 'us-west-1', 
          aws_access_key_id=MASTER_ACCESS_KEY, 
          aws_secret_access_key=MASTER_SECRET) 
    return s3 

st.cache(ttl=60*60*24)
def grab_s3_file(f, bucket, idx_col=None, is_json=False):
    s3 = s3_init()
    data = s3.get_object(Bucket=bucket, Key=f)['Body'].read().decode('utf-8') 
    
    # Check if the file is a JSON
    if is_json:
        return json.loads(data)  # Return the parsed JSON data as a dictionary
    
    # If the file is a CSV
    if idx_col is None:
        data = pd.read_csv(StringIO(data)) 
    else:
        data = pd.read_csv(StringIO(data), index_col=idx_col)

    return data 

def current_year():
    return str(datetime.now().year)

def get_dates(lookahead=1):
    # Get today's date
    today = datetime.now().date()
    # Add one week to today's date 
    if lookahead > 0: 
        next_week = today + timedelta(weeks=1)  
        return today, next_week 
    else: 
        last_week = today - timedelta(weeks=abs(lookahead)) 
        return last_week, today
    
@st.cache(ttl=6*60*60) # allow_output_mutation=True, 
def date_pull(): 
    today, next_week = get_dates()  
    last_week, today = get_dates(lookahead=-1) 
    
    return {'last_week': last_week, 'today': today, 'next_week': next_week} 

def blank():
    st.write(' ')


def get_s3(): 
    MASTER_ACCESS_KEY = st.secrets['MASTER_ACCESS_KEY']  
    MASTER_SECRET = st.secrets['MASTER_SECRET']

    s3 = boto3.client('s3', region_name = 'us-west-1', 
        aws_access_key_id=MASTER_ACCESS_KEY, 
        aws_secret_access_key=MASTER_SECRET)  
    
    return s3

def display_image_from_s3(bucket_name, key):
    """ Fetch and display an image from S3 """ 

    s3 = get_s3() 

    try:
        response = s3.get_object(Bucket=bucket_name, Key=key)
        img_data = response['Body'].read()

        if img_data:
            image = Image.open(BytesIO(img_data))
            st.image(image)
            return True  # Image loaded successfully
        else:
            return False  # No image data
    except Exception as e:
        print(f"Error fetching or displaying image: {e}")
        return False 
    
def escape_hash(s):
    return s.replace("#", "\#") if isinstance(s, str) else s

def string_to_list(s):
    if isinstance(s, str):
        return s.strip("[]").replace("'", "").split(', ')
    return [s]

def display_report(report):
    
    sections = {
        'General':incident_questions.scope_general_questions,
        'Break In General': incident_questions.break_in_general,
        'Break In Units': incident_questions.break_in_units,
        'Non-Break In': incident_questions.non_break_in,
        'Scope Intake': incident_questions.scope_intake,
        'Gate': incident_questions.gate,
        'Fence': incident_questions.fence,
        'Video Surveillance': incident_questions.video_surveillance,
        'Bollard': incident_questions.bollard,
        'Exterior Building Walls': incident_questions.exterior_building_walls,
        'Gutters': incident_questions.gutters,
        'Roof Leak': incident_questions.roof_leak,
        'Asphalt / Concrete': incident_questions.asphalt_concrete,
        'Sealcoat': incident_questions.sealcoat,
        'Windows': incident_questions.windows,
        'Fire Extinguishers': incident_questions.fire_extinguishers,
        'Mold': incident_questions.mold,
        'Pest Control': incident_questions.pest_control,
        'Landscaping': incident_questions.landscaping,
        'Doors': {**incident_questions.doors, **incident_questions.unit_doors, **incident_questions.building_doors},  # Merging dictionaries
        'Electrical': incident_questions.electrical,
        'HVAC': {**incident_questions.hvac, **incident_questions.hvac_technician},  # Merging dictionaries
        'Unit Interior': incident_questions.unit_interior,
        'Lighting': incident_questions.lighting,
        'Signage': incident_questions.signage,
        'Scope Outtake': incident_questions.scope_outtake
    }
        
    field_name_mapping = {
        'site_code': 'Site Code',
        'submitted_by': 'Submitted By',
        "Today's date": 'Report Date'  # Assuming you also want to capitalize 'date'
    }
    
    blank()
    # Print top fields
    for field in ['site_code', 'submitted_by', "Today's date"]:
        display_name = field_name_mapping.get(field, field)
        st.write(f"{display_name}: **{report.get(field, '')}**")

    st.write('---')
    # Define section order
    # section_order = ['Break In General', 'Break In Units', 'Non-Break In Incident', 'Scope Intake']
    # other_sections = [key for key in report.keys() if key not in section_order and key not in ['site_code', 'submitted_by', 'Report date', 'Scope Outtake', 'created_at', 'Which are you reporting? (Select all that apply)', 'file_paths', 'id', 'What is your name?', 'If name not found, please type it here.']]

    # Display sections in the desired order
    for section, section_questions in sections.items():
        if section in report:
            st.write(f"### **{section}**")
            displayed_questions = set()
            for question in section_questions:
                if question in report[section]:
                    answer = report[section][question]
                    display_question_answer(question, answer,section)
                    displayed_questions.add(question)

            # Check for additional questions in this section not predefined
            for question, answer in report[section].items():
                if question not in displayed_questions:
                    display_question_answer(question, answer,section)

# Function to display question and answer
def display_question_answer(question, answer,section):
    if section == 'Scope Intake':
        st.write(f' - {question}:')
        items = string_to_list(answer)
        for idx, item in enumerate(items, 1):
            st.write(f"     {idx}. {escape_hash(item)} ")
            blank()
    elif isinstance(answer, str) and answer.startswith('[') and answer.endswith(']') and ('upload' in question.lower()):
        st.write(f" - {escape_hash(question)}:")
        # Convert string list to actual list
        image_paths = answer.strip("[]").replace("'", "").split(', ')
        for image_path in image_paths:
            success = display_image_from_s3('apex-project-files', image_path.strip())
            if not success:
                st.warning(f"Failed to load image: {image_path}")
    else:
        st.write(f" - {escape_hash(question)}: {escape_hash(answer)}")

def generate_presigned_url(bucket_name, object_name, expiration=3600): 
    
    s3 = s3_init() 
    try:
        response = s3.generate_presigned_url('get_object',
                                            Params={'Bucket': bucket_name,
                                                    'Key': object_name},
                                            ExpiresIn=expiration)  
        return response
    except: 
        return None