# from sql_queries import run_sql_query, facilities_sql

# facilities = run_sql_query(facilities_sql)
# rd_list = facilities['rd'].to_list()
# rd_list.insert(0, "")
# # rd_list.insert(0,'testing')

# fs_list = facilities['fs'].to_list()
# names_insert = ['Kevin Lindsey', 'Jason Turner', 'Jonah Godwin', 'Ty Rivers', 'James Behrnes','Derek Chmielewski']
# fs_list += names_insert
# fs_list = list(set(fs_list))
# fs_list.sort()
# fs_list.insert(0, "")
fs_list = []
rd_list =[]

scope_general_questions = {
    "What is your name?": {'answers': fs_list, 'type': 'selectbox',
            'branch_to':{
                '':{"If name not found, please type it here.": {'answers':'text box', 'type':'text_input'}}
            }},
    "RD": {'answers': rd_list, 'type': 'selectbox'},
    "Report date": {'answers': '', 'type':'date_input'},
    "Which are you reporting? (Select all that apply)": {'answers':['Break In', 'Non-Break In Incident', 'Repair Request'],'type':'multiselect'}
}

break_in_general = {
    "Date of Last Visit": {'type':'date_input','answers':''},
    "How did you discover the break-in?": {'type': 'selectbox', 'answers': ['', 'During a Rent Roll', 'Alerted by ENP Process','Contacted by Police','Customer Notified During Visit','Slack','Other']},
    "How did the suspect gain access to the facility?": {'type': 'selectbox', 'answers': ['', 'Used a Gate Code', 'Fence was Cut','On Foot', 'Gate was Down', 'Unknown', 'Other']
        , 'branch_to': {
            'Used a Gate Code':{"What unit number was the gate code associated with?": {'type': 'selectbox', 'answers': 'unit_list'}},
            'Fence was Cut':{"Will a task need to be created to repair the fence?": {'type': 'selectbox', 'answers': ['', 'Yes', 'No, repairs were done by FS']}}, # create task
            'Gate was Down':{"Will a task need to be created for the gate being down?": {'type': 'selectbox', 'answers': ['', 'Yes', 'No, the issue has been resolved']}} # create task
        }},
    "Did you check the footage?": {'type': 'selectbox', 'answers': ['', 'Yes', 'No']
        , 'branch_to':{
            'No':{"Why were you unable to check the footage?": {'type': 'selectbox', 'answers':['','DVR Down', 'Cameras Down']}}, # create task,
            'Yes':{"Please write in detail what you saw on the footage:": {'type': 'text_input','answers':'text box'},
                "Where did you save the footage?": {'type': 'text_input','answers':'text box'}}
        }},
    "Did you check the gate logs for unusual activity?": {'type': 'selectbox', 'answers': ['', 'Yes', 'No']
        , 'branch_to': {
            'Yes':{"Where did you save the gate logs?": {'type': 'text_input','answers':'text box'},
                    "Please detail any unusual/suspicious information gathered from the gate logs.": {'type': 'text_input', 'answers':'text box'}}
        }},
     "Were the Police called?": {'type': 'selectbox', 'answers': ['', 'Yes', 'No']
            , 'branch_to':{
                'Yes':{"Responding Officer's Name and Police Report #": {'type': 'text_input','answers':'text box'}},
                'No':{"Please detail why the police were not contacted.": {'type': 'text_input','answers':'text box'}}
            }}
}

break_in_units = {
    "Which units were broken into?": {'type': 'multiselect', 'answers': 'unit_list'}  # Dynamic list from SQL query
}

def generate_unit_specific_questions(selected_units):
    unit_specific_questions = {}
    for unit in selected_units:
        unit_specific_questions[f"For unit {unit}, what was the method of entry?"] = {'type': 'selectbox', 'answers': ['', 'Lock Cut', 'Lock Missing', 'Forced Entry', 'Other']}
        unit_specific_questions[f"Upload pictures of the entry point for unit {unit}"] = {'type': 'file_upload', 'answers': ''}
        unit_specific_questions[f"Has the Entry Point Been Fixed for unit {unit}?"] = {'type': 'selectbox', 'answers': ['', 'Yes', 'No'],
                                                                                    'branch_to': {'No': {f"Please explain why entry point was not fixed for unit {unit}.": {'type': 'text_input', 'answers': 'text box'}}}}
    return unit_specific_questions

non_break_in = {
     "Please select the date of the incident.": {
        'type': 'date_input',
        'answers': ''
    },
    "Please select the type of incident that occurred.": {
        'type': 'selectbox',
        'answers': ['','Specific Unit(s)','Property Damage (Confirm that you indicated a Repair Request in the last question of the General Section.)','RDs Vehicle Incident','Tenant Vehicle', 'Sign (Confirm that you indicated a Repair Request in the last question of the General Section.)', 'Individual','Fire','Customer Property Damage', 'Other'] ,
        'branch_to':{
            'Specific Unit(s)':{"Please enter the unit(s) involved in the incident": {
                'type': 'multiselect','answers': 'unit_list'}
                },
            'Tenant Vehicle':{'Please provide specifics about the vehicle involved including make, model, and plate number':{'type':'text_input','answers':''}}
    }},
    "Please describe how you were made aware of the incident": {
        'type': 'text_input',
        'answers': ''
    },
    "Please provide the specifics of the incident and actions taken":{'type':'text_input','answers':''},
    "Were the police, fire department, or any other government agencies involved?":{'type':'selectbox','answers':['','Yes','No'],
            'branch_to':{
                'Yes':{'Please provide the name, phone number, and report number of the responding agencies agent.':{'type':'text_input','answers':''}}
            }},
    "Please provide any requests for follow up action needed by the BOT/RM/CS or Operations Team":{'type':'text_input','answers':''},
    "Please upload any pictures you have around the incident.": {'type': 'file_upload','answers': '','optional':True},
    "Is there any video or other documentation surrounding the incident?":{'type':'selectbox','answers':['','Yes','No'],
            'branch_to':{
                'Yes':{"Please outline where you have saved this other documentation.": {'type': 'text_input','answers': ''}}
            }}
}

scope_intake = {
    "Which item(s) needs to be repaired or maintained?": {'type':'multiselect', 'answers':['Asphalt / Concrete', 'Bollard', 'Doors', 'Electrical', 'Exterior Building Walls', 'Fence', 'Fire Extinguishers', 'Gate', 'Gutters', 'HVAC', 'Landscaping', 'Lighting', 'Mold', 'Pest Control', 'Roof Leak', 'Sealcoat', 'Signage', 'Unit Interior', 'Video Surveillance', 'Windows']}
}
scope_outtake = {
    "Please upload pictures of the damage and/or affected area.":{'type':'file_upload','answers':''},
    "Notes Section / Additional Comments":{'type':'text_input','answers':''},
    "If applicable, please enter vendor information":{'type':'text_input','answers':''},
    "Reference Line (Is this related to another project?)":{'type':'text_input','answers':''}
}

gate = {
    "What gate are you reporting?": {'type': 'selectbox', 'answers': ['Entrance Gate', 'Pedestrial Gate', 'Snow Gate', 'Other']},
    "Is the gate operable?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'No':{"Is there another gate customers can use?": {'type': 'selectbox', 'answers': ['','Yes','No']}}
            }},
    "What is the current status of the gate?": {'type': 'selectbox', 'answers': ['Open', 'Closed', 'Other'],
            'branch_to':{
                'Other':{'Please specify the gate status': {'type':'text_input', 'answers':''}}
            }},
    "Have you troubleshooted with the gate tech?": {'type': 'selectbox', 'answers': ['','Yes','No (please contact gate tech for further information)'],
            'branch_to':{
                'Yes': {"If yes, what was their solution or opinion?": {'type': 'text_input', 'answers': ''}}
            }},
    "Power connection": {'type': 'selectbox', 'answers': ['','Yes','No']},
    "Gate Type": {'type': 'selectbox', 'answers': ['','Slide','Swing','Chop','Other'],
            'branch_to':{
                'Other':{'Please specify the gate type': {'type':'text_input', 'answers':''}}
            }},
    "Gate Material": {'type': 'selectbox', 'answers': ['','Wrought Iron','Chain Link','Other'],
            'branch_to':{
                'Other':{'Please specify the gate material': {'type':'text_input', 'answers':''}}
            }},
    "Gate Measurements (in feet)": {'type': 'number_input', 'answers': '','min_number':0.0},
    "Gate name (select A if there is only 1 gate)": {'type': 'selectbox', 'answers': ['A','B','C','D','E']},
    "Keypad type (PTI, Open Tech, etc)": {'type': 'text_input', 'answers': ''},
    "Operator type": {'type': 'text_input', 'answers': ''},
    "Gate fence damaged?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{
                    "If yes, what is the length of fence repairs needed near the gate? (in feet)": {'type': 'number_input', 'answers': '','min_number':0.0},
                    "If yes, what is the fence material needing repaired?": {'type': 'selectbox', 'answers': ['Wrought Iron','Chain Link','Wood','Other'],
                            'branch_to':{
                                'Other':{'Please specify the fence material near gate': {'type':'text_input', 'answers':''}}
                            }},
                    "If yes, is there barbed wire on the fencing?": {'type': 'selectbox', 'answers': ['','Yes','No']}
                }}
            },
    "Description of gate damage": {'type': 'text_input', 'answers': ''},
    "Improvement suggestions": {'type': 'text_input', 'answers': '','optional':True}
}

fence = {
    "Temporarily repaired?": {'type': 'selectbox', 'answers': ['','Yes','No']},
    "Fence material": {'type': 'selectbox', 'answers': ['Wrought Iron','Chain Link','Wood','Other'],
            'branch_to':{
                'Other':{'Please specify the fence material': {'type':'text_input', 'answers':''}}
            }},
    "What is the size of the hole? (inches)": {'type': 'number_input', 'answers': '','min_number':0.0},
    "Describe the location of the repair. What side of the property? Near which building #?": {'type': 'text_input', 'answers': ''},
    "Describe the damage. (Hole in fence? Barbed wire needs repaired? Fence leaning? Pole needs repairing?)": {'type': 'text_input', 'answers': ''},
    "Upload facility map noting where repairs are needed.": {'type': 'file_upload', 'answers': ''}
}

video_surveillance = {
    "What are the camera serial number(s) that are not working? (Numbers can be found on the DVR). Write \"N/A\" if you cannot find it": {'type': 'text_input', 'answers': ''},
    "How many cameras are down or in need of repair?": {'type': 'number_input', 'answers': '','min_number':0},
    "Near which building #?": {'type': 'text_input', 'answers': ''},
    "Near which unit #?": {'type': 'selectbox', 'answers': 'unit_list'},
    "System Operable?": {'type': 'selectbox', 'answers': ['Yes', 'No', 'Partial'],
            'branch_to':{
                'Partial':{"If partial, what are the issues with the system?": {'type': 'text_area', 'answers': ''}}
            }},
    "Are you experiencing any monitor issues?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, what are the issues?": {'type': 'text_area', 'answers': ''}}
            }},
    "Is the DVR operable?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'No': {"If no, what are the issues with the DVR?": {'type': 'text_area', 'answers': []}} 
           }},
    "Is there power to the system?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'No':{"If no, is there a power outage in the area?": {'type': 'selectbox', 'answers': ['','Yes (notify POA)', 'No'],
                      'branch_to':{'Yes (notify POA)':{"If yes, is there an estimated time for power to be turned back on?": {'type': 'text_input', 'answers': ''}}}}},
                'Yes':{"Is the internet on and working?": {'type': 'selectbox', 'answers': ['','Yes', 'No (contact POA)']}}
            }},
    "Is there any missing equipment?": {'type': 'selectbox', 'answers': ['','No','DVR','Internet router','Cameras','Camera wiring','Other'],
            'branch_to':{
                'Other':{'Please specify what equipment is missing':{'type':'text_input','answers':''}}
            }},
    "DVR system info (login, manufacturer, etc.)": {'type': 'text_input', 'answers': ''},
    "Are additional cameras needed?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{'How many cameras are needed':{'type':'number_input','answers':'','min_number':1},
                       "If yes, upload a facility map notating where new cameras are needed.": {'type': 'file_upload', 'answers': ''}}
            }}
}

bollard = {
    "What's the building number?": {'type': 'text_input', 'answers': ''},
    "Which unit is this near?": {'type': 'selectbox', 'answers': 'unit_list'},
    "Quantity needing repaired": {'type': 'number_input', 'answers': '','min_number':1},
    "Size - height and diameter (ex. 3ft, 6in)": {'type': 'text_input', 'answers': ''},
    "Condition (Is the bollard still intact?)": {'type': 'text_input', 'answers': ''},
    "Is the bollard detached from the concrete?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes': {"If yes, where is the bollard being stored temporarily?": {'type': 'text_input', 'answers': ''},
                        "If yes, how large is the hole that the bollard has detached from? (inches)": {'type': 'number_input', 'answers': '','min_number':0.0}
                        }
            }},
    "Is there a safety hazard from the bollard?": {'type': 'selectbox', 'answers': ['Yes','No'],
            'branch_to':{
                'Yes':{"If yes, what safety precautions has the FS taken?": {'type': 'multiselect', 'answers': ['Cones','Rope','Caution Tape','Warning Signs','Other']},
                       "If you included 'Other' in the last question, please specify. Otherwise, skip to the next question.":{'type':'text_input', 'answers':''}}
            }},
    "Is a new bollard needed where one didn't exist before?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, why does a new bollard need to be installed?": {'type': 'text_input', 'answers': ''},
                    "If yes, where does the new bollard need installed?": {'type': 'text_input', 'answers': ''},
                    "If yes, upload a photo or facility map of where to place bollard.": {'type': 'file_upload', 'answers': '','optional':True}}
            }}  
}

exterior_building_walls = {
    "Which building?": {'type': 'text_input', 'answers': ''},
    "Which unit number is it near/on?": {'type': 'selectbox', 'answers': 'unit_list'},
    "Which wall is damaged? (north/west, back/front, etc?)": {'type': 'selectbox', 'answers': ['North','West','Back','Front']},
    "Type of Wall": {'type': 'selectbox', 'answers': ['Brick','Metal','Concrete','Drywall', 'Wood','Other'],
            'branch_to':{
                'Other': {'If Other, specify the wall material':{'type':'text_input','answers':''}}
            }},
    "Please describe the damage.": {'type': 'text_input', 'answers': ''},
    "Is there a safety concern?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, describe how this area is unsafe.": {'type': 'text_input', 'answers': ''}}
            }},
    "Are units unsecured due to damage?": {'type': 'selectbox', 'answers': ['','Yes','No']},
    "Measurement of damaged area": {'type': 'text_input', 'answers': ''}
}

gutters = {
    "Which building(s) are affected?": {'type': 'text_input', 'answers': ''},
    "What unit is the damage near?": {'type': 'selectbox', 'answers': 'unit_list'},
    "Description of the damage": {'type': 'multiselect', 'answers': ['Sagging','Leaking','Clogged/Blocked','Damaged','Crunched','Other']},
    "If you selected 'Other,' please specify the damage. Otherwise, skip.":{'type': 'text_input', 'answers': '','optional':True},
    "Type of Material": {'type': 'selectbox', 'answers': ['Aluminum','Vinyl','Copper','Galvanized (Steel)','Plastic','Other'],
            'branch_to':{
                'Other': {'If Other, specify the gutter material':{'type':'text_input','answers':''}}
            }},                         
    "Type of Gutter": {'type': 'selectbox', 'answers': ['Seamless aluminum (1 piece)','Seamless half-round (6 in)','Seamless box gutter','Seamless 5 or 6 inch','Other'],
            'branch_to':{
                'Other': {'If Other, specify the gutter type':{'type':'text_input','answers':''}}
            }},            
    "What is the color of the gutter?": {'type': 'text_input', 'answers': ''},
    "Do they need cleaning?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, when were the gutters last cleaned?": {'type': 'date_input', 'answers': ''}}
            }}    
}

roof_leak = {
    "Which building number?": {'type': 'text_input', 'answers': ''},
    "What unit number(s) is it affecting?": {'type': 'multiselect', 'answers': 'unit_list'},
    "Is there an active tenant?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, has BOT been contacted?": {'type': 'selectbox', 'answers': ['Yes','No'],
                        'branch_to':{
                            'Yes':{"If yes, has an OL been placed?": {'type': 'selectbox', 'answers': ['Yes','No']}}
                        }}}
            }},
    "Describe the damage.": {'type': 'text_input', 'answers': ''},
    "How was the leak discovered?": {'type': 'text_input', 'answers': ''},
    "Can you see holes in the ceiling?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{'How many holes?':{'type':'number_input', 'answers': '','min_number':0.0}}
            }},
    "Are insulation repairs needed? (If unable to be repaired in house)": {'type': 'selectbox', 'answers': ['','Yes','No']},
    "Roof Type": {'type': 'selectbox', 'answers': ['Shingle','Tile','Metal','Flat','Other'],
            'branch_to':{
                'Other': {'If Other, specify the roof type':{'type':'text_input','answers':''}}
            }},                  
    "Is mold present?": {'type': 'selectbox', 'answers': ['','Yes','No']}
}

asphalt_concrete = {
    "Location(s) on property": {'type': 'text_input', 'answers': ''},
    "Is there a safety hazard?2": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, what safety precautions has FS taken?": {'type': 'multiselect', 'answers': ['Cones','Rope','Caution tape','Warning signs','Other']},
                       "If you selected 'Other' in the previous question, please specify":{'type':'text_input','answers':'','optional':True}}
            }},
    "What type of material?": {'type': 'selectbox', 'answers': ['','Asphalt','Concrete','Gravel / Dirt'],
            'branch_to':{
                'Asphalt':{"Type of damage (Asphalt)": {'type': 'selectbox', 'answers': ['Pothole','Alligator cracking','Edge cracks','Erosion','Manhole','Other'],
                            'branch_to': {"Other":{"If Other, please specify the asphalt damage":{'type':'text_input','answers':''}}}}},
                'Concrete':{"Type of damage (Concrete)": {'type': 'selectbox', 'answers': ['Spalling (flaking/peeling)','Settling (sinking)','Cracking','Potholes','Lifting (not level)','Other'],
                            'branch_to': {"Other":{"If Other, please specify the concrete damage":{'type':'text_input','answers':''}}}}}
            }},
    "What are the measurements of the damage?": {'type': 'text_input', 'answers': ''},
    "Does grading need to occur?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, what areas need to be graded?": {'type': 'selectbox', 'answers': ['Entire lot','Drive aisles','Other'],
                       'branch_to':{"Other":{"If Other, please specify the areas needing to be graded":{'type':'text_input','answers':''}}}}}
            }},
    "Are there areas that need to be filled in?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{'Upload a photo of the area that needs to be filled in':{'type':'file_upload','answers':''},
                       "If yes, how large is the area that needs to be filled?": {'type': 'text_input', 'answers': ''}}
            }},
    "Is this affecting the parking area?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, are there vehicles parked on the area?": {'type': 'selectbox', 'answers': ['','Yes','No']},
                    "If yes, has BOT been informed, so they can contact tenant(s)?": {'type': 'selectbox', 'answers': ['','Yes','No']}}
            }}
}

sealcoat = {
    "Does the entire property need to be sealcoated?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'No':{"If no, what is the location that needs to be sealcoated?": {'type':'text_input','answers':''},
                      'Upload a photo of the area that needs to be sealcoated':{'type': 'file_upload', 'answers': ''}
        }}},
    "Do you know when the last sealcoat was completed?": {'type': 'selectbox', 'answers': ['','Yes','No']},
    "If yes, enter month and year. If no, what is your estimate on last time it was completed?": {'type': 'date_input', 'answers': ''},
    "How much longer do you think it will last?": {'type': 'text_input', 'answers': ''},
    "Is the lack of sealcoat affecting the parking area?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, are there vehicles parked in the area?": {'type': 'selectbox', 'answers': ['Yes','No']}}
            }},
    "Is there any striping that needs to occur?": {'type': 'selectbox', 'answers': ['','Yes','No'],
        'branch_to':{
                        'Yes':{"If yes, what is the location(s)?": {'type': 'text_input', 'answers': ''}}
                    }}
}

windows = {
    "What is wrong with the window?": {'type': 'selectbox', 'answers': ['Broken','Cracked',"Can't shut",'Other'],
            'branch_to':{
                'If Other, please specify what is wrong with the window':{'type':'text_input','answers':''}
            }},
    "Description of issue": {'type': 'text_input', 'answers': ''},
    "Is there a safety or security hazard?": {'type': 'selectbox', 'answers': ['','Yes','No'],
            'branch_to':{
                'Yes':{"If yes, how is this a safety hazard?": {'type': 'selectbox', 'answers': ['Broken glass','Unsecured office','Other'],
                       'branch_to':{"Other":{"If Other, please specify how this is a safety hazard":{'type':'text_input','answers':''}}}}}
            }},
    "# of windows damaged": {'type': 'number_input', 'answers': '','min_number':0},
    "Measurements and quantity of each window": {'type': 'text_input', 'answers': ''},
    "Upload facility photo notating the windows' locations.": {'type': 'file_upload', 'answers': ''}
}

fire_extinguishers = {
    "How many fire extinguishers are needed?": {'type': 'number_input', 'answers': '', 'min_number': 0},
    "How many fire extinguishers are expired?": {'type': 'number_input', 'answers': '', 'min_number': 0},
    "What is the location of the extinguishers on the property?": {'type': 'text_input', 'answers': ''},
    "Upload a map of the property with locations of the extinguishers": {'type': 'file_upload', 'answers': '','optional':True},
    "Are any of the cases damaged?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"How many cases are needed?": {'type': 'number_input', 'answers': '', 'min_number': 0}}
            }}
}

mold = {
    "What is the unit number(s) affected by mold?": {'type': 'multiselect', 'answers': 'unit_list'},
    "Where is the mold located within the unit? Wall, floor, ceiling, other (specify)": {'type': 'text_input', 'answers': ''},
    "What is the color of the mold?": {'type': 'text_input', 'answers': ''},
    # "Upload a photo of the mold": {'type': 'file_upload', 'answers': ''},
    "Is there an active tenant at this unit with mold?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"Has BOT been contacted for tenant transfer?": {'type': 'selectbox', 'answers': ['','Yes', 'No']}}
            }},
    "Are there signs of water intrusion?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Where is the water coming from? Roof, ground, walls, other (specify)": {'type': 'text_input', 'answers': ''}
}

pest_control = {
    "What type of pest control is needed?": {'type': 'selectbox', 'answers': ['Spiders','Rodents','Bees','Dead animal','Other'],
            'branch_to':{
                'Other':{'If Other, specify the pest control needed':{'type':'text_input','answers':''}}
            }},
    "Is there an active tenant at this unit?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "What areas need serviced?": {'type': 'selectbox', 'answers': ['Entire property','Building','Interior','Exterior','Other'],
            'branch_to':{
                'Other':{'If Other, specify the area needing service':{'type':'text_input','answers':''}}
            }}
}

landscaping = {
    "What type of project?": {'type': 'selectbox', 'answers': ['Tree trimming','Vegetation control','Weed control','Gutters','Emergency','Other'],
            'branch_to':{
                'Other':{'If Other, specify the project':{'type':'text_input','answers':''}}
            }},
    "What is the location on the property?": {'type': 'text_input', 'answers': ''},
    "Please describe the situation": {'type': 'text_input', 'answers': ''},
    # "Please upload a photo of the area": {'type': 'file_upload', 'answers': ''}
}

doors = {
    "Which building number(s) is affected?": {'type': 'text_input', 'answers': ''},
    "What kind of doors?": {'type': 'selectbox', 'answers': ['Unit Doors','Building Doors']}}

unit_doors ={
    "Which unit numbers are affected?": {'type': 'multiselect', 'answers': 'unit_list'},
    "Does this repair request include an occupied unit or units?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"Which unit or units is/are occupied?": {'type': 'multiselect', 'answers': 'unit_list'},
                    "Has BOT been contacted to inquire about transfer?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
                    "Has an overlock been placed and the customer lock removed?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
                    "Has the tenant been informed of the door repair process? (Ex: Moved items 5-6 ft, OL placement length, scheduling vendors with FS, etc.)": {'type': 'selectbox', 'answers': ['','Yes', 'No']}}
            }},
    "Description of door damage": {'type': 'selectbox', 'answers': ['','Off Track','Door Springs','Dented','Other'],
            'branch_to':{
                'Other':{'If Other, specify the door damage':{'type':'text_input','answers':''}}
            }}
}
building_doors = {
    "What type of door needs to be repaired?": {'type': 'selectbox', 'answers': ['','Entry','Sliding Doors','Back Office Door','Other'],
            'branch_to':{
                'Entry':{"What is wrong with the entry door?": {'type': 'selectbox', 'answers': ['',"Won't close easily",'Stuck open','Maglock','Not secure','Other'],
                            'branch_to':{'Other':{'If Other, what is wrong with the entry door':{'type':'text_input','answers':''}}}},
                        "How many entry doors need serviced?": {'type': 'number_input', 'answers': '', 'min_number': 1},
                        "Is the entry door able to be secured?": {'type': 'selectbox', 'answers': ['Yes', 'No'],
                            'branch_to':{'No':{"Has the RM been contacted to help determine a way to secure the door?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
                                                'branch_to':{'No':{"Is the door behind the gate?": {'type': 'selectbox', 'answers': ['Yes', 'No']}}}}}},
                        'What type of door?':{'type':'selectbox','answers':['Metal slab','Wooden','Aluminum with Glass','Other'],
                                              'branch_to':{'Other':{'If other, what type of door is the entry door?':{'type':'text_input','answers':''}}}}}},
                'Sliding Doors':{"What is wrong with the sliding doors?": {'type': 'selectbox', 'answers': ["Won't close","Won't open with code",'Off track','Other'],
                                                                           'branch_to':{'If other, what is wrong with the sliding door?':{'type':'text_input','answers':''}}},
                    "Where is the sliding door located?": {'type': 'text_input', 'answers': ''},
                    "Is the door functioning?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
                    "Is there a safety hazard from the doors?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
                                                  'branch_to':{'Yes':{"Has a sign been placed to use side doors?": {'type': 'selectbox', 'answers': ['Yes', 'No']},
                                                                      "Has the sliding door been locked to prevent entry and further damage?": {'type': 'selectbox', 'answers': ['','Yes', 'No']}}}}},
                'Back Office Door':{"What is wrong with the back office door?": {'type': 'selectbox', 'answers': ['','Unable to close','Frame needs to be repaired','Door busted','Other'],
                                                 'branch_to':{'Other':{'If other, what is wrong with the back office door?':{'type':'text_input','answers':''}}}},
                                    "Can customers gain access to the back office door?": {'type': 'selectbox', 'answers': ['Yes', 'No'],
                                            'branch_to':{'Yes':{"Is the back office door able to be secured?": {'type': 'selectbox', 'answers': ['','Yes', 'No','Other'],
                                                                                                                'branch_to':{"Other":{'If other, please explain.':{'type': 'text_input', 'answers': ''}}}}}}}},
                'Other':{'If other, please describe what type of door is damaged and what needs to be repaired.':{'type':'text_input','answers':''}}
            }}
}

electrical = {
    "Does this repair pose any safety hazard?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"What safety precautions has FS taken?": {'type': 'selectbox', 'answers': ['Cones','Rope','Caution tape','Warning signs','Other'],
                                                                 'branch_to':{'Other':{'If other, please specify the precautions.':{'type':'text_input','answers':''}}}}}
            }},
    "Is power out at any portion of property?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "What type of electrical repair is needed?": {'type': 'selectbox', 'answers': ['Electrical panel','Wiring','Outlet','Other'],
                                                  'branch_to':{'Other':{'If other, specify the electrical repair needed.':{'type':'text_input','answers':''}}}},
    "Has this issue affected the gate or internet?": {'type': 'selectbox', 'answers': ['','Gate','Internet','Other'],
            'branch_to':{
                'Gate':{"Has the gate technician been contacted for troubleshooting?": {'type': 'selectbox', 'answers': ['','Yes', 'No']}},
                'Internet':{"Has POA or IT been contacted?": {'type': 'selectbox', 'answers': ['','POA','IT', 'No']}},
                'Other':{"Where is the issue located?": {'type': 'text_input', 'answers': ''}}
            }},
    # "Which ones? Please be specific": {'type': 'text_input', 'answers': ''},
    "Were any circuit breakers turned off?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"Can a vehicle roll over the wire?": {'type': 'selectbox', 'answers': ['','Yes', 'No']}}
            }},
    "Is there exposed wiring?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"Where is the exposed wiring coming from?": {'type': 'selectbox', 'answers': ['Ground','Pole','Building','Unit','Gate','Other'],
                                                                    'branch_to':{'Other':{'If other, please specify where the wiring is coming from.':{'type':'text_input','answers':''}}}},
                    "Can anything be done to reduce the hazard?": {'type': 'text_input', 'answers': ''},
                    "Does it pose a trip hazard?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
                                                    'branch_to':{'Yes':{"Is the wire from the pole safely out of the way?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
                                                        "Does it look more like a telephone or power cable?": {'type': 'selectbox', 'answers': ['Telephone', 'Power', 'Gas','Unknown','Other'],
                                                                                                               'branch_to':{'Other':{'If other, specify what the cable looks like.':{'type':'text_input','answers':''}}}}}}},
                    "What do you think is the source of the wire?": {'type': 'text_input', 'answers': ''},
                    "Was the cable coming from the building attached to a pole?": {'type': 'selectbox', 'answers': ['','Yes', 'No']}
    }}}    
}

hvac = {
    'Which hvac units seem to be down? Please note the RD Unit SKU#.' :{'type':'text_input','answers':''}
}

hvac_technician = {
    "Which climate controlled building is it in?": {'type': 'text_input', 'answers': ''},
    "How many total HVAC units are down?": {'type': 'number_input', 'answers': '', 'min_number': 0},
    "HVAC type?": {'type': 'selectbox', 'answers': ['','Central', 'Window Unit', 'Split', 'Packaged', 'Other']},
    "What are the HVAC unit numbers?": {'type': 'text_input', 'answers': ''},
    "What is the nearest unit number to the affected HVAC?": {'type': 'selectbox', 'answers': 'unit_list'},
    "Are you able to access the HVAC yourself?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'No':{"Why? Is it located on the roof, above the rafters, etc.?": {'type': 'text_input', 'answers': ''}}
            }},
    "Has troubleshooting maintenance been completed as noted on Page 27 of the Field Operations Handbook?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Did you check the breaker?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Did you check the filter?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"When was it last changed?": {'type': 'date_input', 'answers': ''}}
            }},
    "Did you check the drain line pan?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Did you check the coils?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Did you check the thermostat batteries?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "What is wrong with the unit? What is it doing, can you hear it, is there no heat/AC, etc.": {'type': 'text_input', 'answers': ''},
    "Is it making loud noises?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Is it off completely?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"Is it able to be turned on?": {'type': 'selectbox', 'answers': ['','Yes', 'No']}}
            }},
    "Is it blowing warm air?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Is there water leaking from the HVAC unit?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"Is the water leaking into a customer unit?": {'type': 'selectbox', 'answers': ['','Yes', 'No']}}
            }},
    "Did you turn any units off?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"Which ones?": {'type': 'text_input', 'answers': ''}}
            }},
    "Where is the unit located?": {'type': 'selectbox', 'answers': ['Roof','Company Unit','Exterior of building','Apartment','Back office','Other'],
                                   'branch_to':{
                                       'Other':{'If other, explain where the unit is located.':{'type':'text_input','answers':''}}
                                   }},
    "Please upload images of the unit and any relevant components of it": {'type': 'file_upload', 'answers': ''}
}

unit_interior = {
    "What is the building number?": {'type': 'text_input', 'answers': ''},
    "What is the unit number?": {'type': 'selectbox', 'answers': 'unit_list'},
    "Is this unit occupied?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"Has BOT been contacted?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
                    "Has an OL been placed?": {'type': 'selectbox', 'answers': ['','Yes', 'No']}}
            }},
    "Is the unit secure?": {'type': 'selectbox', 'answers': ['Yes', 'No']},
    "What type of damage?": {'type': 'selectbox', 'answers': ['Wall','Ceiling (if different from roof)','Roof','Mesh wire','Insulation','Beams','Floor','Unit wall','Other'],
            'branch_to':{
                'Other':{'If other, explain the damage type.':{'type':'text_input','answers':''}}
            }},
    "What type of wall?": {'type': 'selectbox', 'answers': ['','Drywall', 'Brick', 'Concrete','Metal','Wood','Insulation','Mesh wire', 'Other']},
    "What is the location of the damage? For example, looking at the building, left/right/back/front/ceiling/roof/floor": {'type': 'text_input', 'answers': ''},
    "Describe the damage": {'type': 'selectbox', 'answers': ['Vehicle','Vandalism','Erosion','Water','Break In','Other'],
            'branch_to':{
                'Other':{'If other, explain the damage.':{'type':'text_input','answers':''}}
            }},
    "Is there a safety issue?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"What is the safety issue? (Mold, Pieces falling, etc.)": {'type': 'text_input', 'answers': ''}}
            }},
    "What is the measurement of the damaged area?": {'type': 'text_input', 'answers': ''}
}

lighting = {
    "Is there a safety issue due to live electrical?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Exterior or interior lights?": {'type': 'selectbox', 'answers': ['','Exterior', 'Interior','Both']},
    "What is wrong with the lights?": {'type': 'selectbox', 'answers': ['','Out','Flickering','Staying on']},
    "How many lights are having issues?": {'type': 'number_input', 'answers': '',  'min_number': 1},
    "What type of lights?": {'type': 'selectbox', 'answers': ['Wall pack','Pole light','Ballast bulbs','Other'],
            'branch_to':{
                'Other':{'If other, specify the lighting type.':{'type':'text_input','answers':''}}
            }},
    "What building(s) need to be serviced?": {'type': 'text_input', 'answers': ''},
    "Is the issue with the lights themselves or a bigger electrical issue throughout the property?": {'type': 'selectbox', 'answers': ['','Fixture related','Electrical','Other'],
            'branch_to':{
                'Other':{'If other, specify the issue.':{'type':'text_input','answers':''}}
            }},
    "Are multiple lights in a row or entire buildings having issues?": {'type': 'selectbox', 'answers': ['','Entire Row','Entire Building', 'No']},
    "Please upload a photo of each/all types of lights that are not working": {'type': 'file_upload', 'answers': ''},
    "Please upload a map with locations of the lights that are not working": {'type': 'file_upload', 'answers': ''},
    "Is any additional lighting needed?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"How many additional lights?": {'type': 'number_input', 'answers': '', 'min_number': 1},
                    "If yes, exterior or interior lighting?": {'type': 'selectbox', 'answers': ['','Exterior', 'Interior']},
                    "Please mark on facility map for additional light placement and upload photo here": {'type': 'file_upload', 'answers': ''}}
            }},
    "If you have any suggestions for improvement, please write them here": {'type': 'text_input', 'answers': '','optional':True}
}

signage = {
    "Is there physical sign damage?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Where is the sign located on the property? (Front, rear, etc.)": {'type': 'text_input', 'answers': ''},
    "Is the sign illuminated?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "What type of sign is it?": {'type': 'selectbox', 'answers': ['Cabinet (box sign)', 'Monument (ground sign)','Pole (pole sign)', 'Channel lettering (lettering on building)','Other'],
            'branch_to':{
                'Other':{'If other, describe the sign type.':{'type':'text_input','answers':''}}
            }},
    "What is the approximate height of the sign? (feet)": {'type': 'number_input', 'answers': '', 'min_number': 0.0},
    "Will a bucket lift be required to service the sign?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "Is there damage done to the foundation of the sign?": {'type': 'selectbox', 'answers': ['','Yes', 'No']},
    "What is the material of the foundation?": {'type': 'selectbox', 'answers': ['Brickwork','Landscape','Pole','Other'],
            'branch_to':{
                'Other':{'If other, describe the foundation material.':{'type':'text_input','answers':''}}
            }},
    "Is there a safety hazard from the sign damage?": {'type': 'selectbox', 'answers': ['','Yes', 'No'],
            'branch_to':{
                'Yes':{"How does this pose a safety hazard?": {'type': 'text_input', 'answers': ''}}
            }},
    # "Please upload image(s) of the sign": {'type': 'file_upload', 'answers': ''}
}

