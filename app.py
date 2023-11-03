import streamlit as st
import pandas as pd
from ddb_class import DDB
from plots import BasePlot, Boxplot
from datetime import datetime
import altair as alt
from decimal import Decimal


cipc_board = st.secrets['CIPC_BOARD_ID']
opc_board = st.secrets['OPC_BOARD_ID']
ddb = DDB(table='apex')

#---------------SETTINGS--------------------
page_title = "Apex Analytics"
page_icon = ":red-circle:"  #https://www.webfx.com/tools/emoji-cheat-sheet/
layout= "wide"
initial_sidebar_state="expanded"
#-------------------------------------------

st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout, initial_sidebar_state=initial_sidebar_state)

# --- HIDE STREAMLIT STYLE ---
hide_st_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

def password_authenticate(pwsd):

    if pwsd in st.secrets["ADMIN"]:
        return "Admin"
    else:
        return False

def blank(): return st.write('') 

enter_password = st.sidebar.text_input("Password", type = 'password')

if password_authenticate(enter_password):
    st.session_state['valid_password'] = True
else: 
    st.warning("Enter Password to Access")
    st.session_state['valid_password'] = False

password = password_authenticate(enter_password)

if password == "Admin":

    row0 = st.columns([1,1,1])
    row0[1].title(page_title)

    include_conditions = {'scheduled_year': '2023'}
    exclude_conditions = {'status': 'Complete'}

    st.cache(ttl=60*60*24)
    completed_projects = ddb.query_items({'scheduled_year': '2023', 'status': 'Complete'}, {})
    projects = ddb.query_items(include_conditions, exclude_conditions)

    def get_current_timestamp():
        return datetime.utcnow()
    now = get_current_timestamp()

    # Convert string dates to datetime objects and calculate days
    for project in projects:
        status_last_change = project.get('status_last_change')
        open_date = project.get('open_date')

        if status_last_change:
            project['status_last_change'] = datetime.strptime(status_last_change, '%Y-%m-%d %H:%M:%S')
            project['days_in_status'] = (now - project['status_last_change']).days
        else:
            project['days_in_status'] = None  # Or set a default value like 0 or -1

        if open_date:
            project['open_date'] = datetime.strptime(open_date.replace(' UTC', ''), '%Y-%m-%d %H:%M:%S')
            project['days_open'] = (now - project['open_date']).days
        else:
            project['days_open'] = None  # Or set a default value like 0 or -1

    with st.expander('Current Realities'):
        row1= st.columns([1,1])

    ############ 1. # of projects in each status and the average days in that status
        status_data = {}
        for project in projects:
            status = project.get('status')
            if status:
                if status not in status_data:
                    status_data[status] = {'count': 0, 'total_days': 0}
                status_data[status]['count'] += 1
                # Add the days in status only if it is not None
                if project.get('days_in_status') is not None:
                    status_data[status]['total_days'] += project['days_in_status']

        status_df = pd.DataFrame([
            {
                'status': status,
                'projects': data['count'],
                'avg_days_in_status': (data['total_days'] / data['count']) if data['count'] > 0 else 0
            }
            for status, data in status_data.items()
        ])

        # Define colors for the legend
        project_color = 'teal'
        avg_days_color = 'orange'

        # Create the bar chart for the number of projects
        bar_projects = alt.Chart(status_df).mark_bar(opacity=1, color=project_color).encode(
            x=alt.X('status:N', axis=alt.Axis(title='')),
            y=alt.Y('projects:Q', axis=alt.Axis(title='')),
            # Add a legend by using the color encoding with a condition
            color=alt.value(project_color)  # Use a constant color value for the bars
        )

        # Create the bar chart for the average days in status
        bar_avg_days = alt.Chart(status_df).mark_bar(opacity=0.7, color=avg_days_color).encode(
            x='status:N',
            y=alt.Y('avg_days_in_status:Q', axis=alt.Axis(title='')),
            # Make this bar skinnier by adjusting the size
            size=alt.value(10),  # Adjust the size as needed
            # Add a legend by using the color encoding with a condition
            color=alt.value(avg_days_color)  # Use a constant color value for the bars
        )

        # Combine the charts
        combined_chart = alt.layer(bar_projects, bar_avg_days).resolve_scale(
            y='independent'
        )

        # Add tooltip
        combined_chart = combined_chart.encode(
            tooltip=['status:N', 'projects:Q', 'avg_days_in_status:Q']
        )

        # Add a custom legend by creating dummy data for the legend
        legend_data = pd.DataFrame({
            'category': ['Count of Projects', 'Avg Days in Status'],
            'color': [project_color, avg_days_color]
        })

        # Create the legend chart
        legend = alt.Chart(legend_data).mark_square(size=100).encode(
            y=alt.Y('category:N', axis=alt.Axis(orient='right', title='')),
            color=alt.Color('color:N', scale=None)  # Prevent Altair from using its own color scale
        )

        # Display the chart in Streamlit
        row1[0].altair_chart(alt.hconcat(combined_chart, legend), use_container_width=True)
        # row1[0].altair_chart(status_chart, use_container_width=True)


    ############ 2. # of projects by priority and the avg days they've been open ##########################
        priority_data = {}
        for project in projects:
            priority = project.get('base_priority', 'Unknown')  # Providing a default priority if none is found
            if priority not in priority_data:
                priority_data[priority] = {'count': 0, 'total_days': 0}
            priority_data[priority]['count'] += 1
            priority_data[priority]['total_days'] += project.get('days_open', 0)  # Default to 0 if 'days_open' is not present

        priority_df = pd.DataFrame([
            {
                'priority': priority,
                'projects': data['count'],
                'avg_days_open': (data['total_days'] / data['count']) if data['count'] > 0 else 0
            }
            for priority, data in priority_data.items()
        ])

        priority_chart = BasePlot().style_chart(
            alt.Chart(priority_df).mark_bar(color='teal').encode(
                x='projects:Q',
                y='priority:N',
                tooltip=['priority:N', 'projects:Q', 'avg_days_open:Q']
            ),
            'Projects by Priority'
        )

        row1[1].altair_chart(priority_chart)

    ############ 3. Boxplot by priority_values ('value_driven_priority') ############
        col1,col2= st.columns([2,2])
        cost_efficiencies = {}

        # Calculate cost efficiency for each project
        for entry in projects:
            base_priority = entry.get('base_priority', 'Unknown')  # Handle case if 'base_priority' is not set
            value_priority = entry.get('value_driven_priority')
            cost = entry.get('cost') if entry['cost'] != 0 else Decimal('1')
            
            if value_priority and cost:
                efficiency = float(value_priority) / float(cost)
                
                # Add efficiency to the correct list in our dictionary
                if base_priority not in cost_efficiencies:
                    cost_efficiencies[base_priority] = []
                cost_efficiencies[base_priority].append(efficiency)

        boxplot_instance = Boxplot()
        df = pd.DataFrame([
            {'Base Priority': base_priority, 'Cost Efficiency': efficiency}
            for base_priority, efficiencies in cost_efficiencies.items()
            for efficiency in efficiencies
        ])
        df = df[df['Cost Efficiency']<100000]
        # Define the title and color scheme for the boxplot
        title_text = 'Cost Efficiency by Priority'
        color_scheme = 'teals'

        # Use the display_boxplot method from Boxplot to display the chart
        with col1:
            boxplot_instance.display_boxplot(df, 'Cost Efficiency', 'Base Priority', title_text, color_scheme)

    ############ 4. emergency outstanding projects table ############
        filtered_projects = []
        priorities = []
        # Iterate over each project
        for project in projects:
            # Skip projects that do not have the specified status
            if project['base_priority'] not in ['Critical EMERGENCY', 'Immediate']:
                continue
            
            # Calculate the days in status
            status_last_changed = project.get('status_last_change')
            if isinstance(status_last_changed, str):
                last_change_date = datetime.strptime(status_last_changed, '%Y-%m-%d %H:%M:%S')
            elif isinstance(status_last_changed, datetime):
                last_change_date = status_last_changed
            else:
                # Handle the case where 'status_last_changed' is neither a string nor a datetime object
                # Perhaps raise an error or continue to the next project
                continue
            # last_change_date = datetime.strptime(status_last_changed, '%Y-%m-%d %H:%M:%S')
            days_in_status = (now - last_change_date).days

            # Check if days in status is greater than 3
            if days_in_status > 3:
                # Create a dictionary of the information you want to include in your table
                team_board = cipc_board if project['team'] == 'cipc' else opc_board

                filtered_project_info = {
                    'Name': project['project_name'],
                    'Status': project['status'],
                    'Days in status': days_in_status,
                    'team_board': team_board,
                    'id': project['id']
                }
                priorities.append(project['base_priority'])
                # Add the dictionary to your list of filtered projects
                filtered_projects.append(filtered_project_info)

        # Convert the list of filtered projects to a DataFrame
        filtered_projects_df = pd.DataFrame(filtered_projects)

        filtered_projects_df['id_link'] = filtered_projects_df.apply(
            lambda row: f"<a href='https://reddotstorage2.monday.com/boards/{row['team_board']}/pulses/{row['id']}' target='_blank'>{row['id']}</a>", axis=1)
        
        filtered_projects_df.drop(columns=['id', 'team_board'], inplace=True)

        # Rename 'id_link' to 'id' if that's what you want your column header to be
        filtered_projects_df.rename(columns={'id_link': 'id'}, inplace=True)

        def highlight_critical_emergency(row_index):
            # RGBA: R=255, G=165, B=0, A=0.7 for orange color with 70% opacity
            if priorities[row_index] == 'Critical EMERGENCY':
                return ['background-color: rgba(255, 165, 0, 0.7);'] * len(filtered_projects_df.columns)
            else:
                return [''] * len(filtered_projects_df.columns)

        # Apply the highlighting function row-wise
        styled_df = filtered_projects_df.style.apply(lambda x: highlight_critical_emergency(x.name), axis=1)
        html = styled_df.to_html(escape=False, index=False)

        # Output the DataFrame to display the table
        if len(filtered_projects) == 0:
            with col2:
                st.success('There are no outstanding Emergency projects.')
        else:
            # Output the DataFrame to display the table
            with col2:
                st.write(html, unsafe_allow_html=True)

    ############ 5. # projects completed by week and month over time ############

        # completed_projects = [p for p in projects if p.get('status') == 'Complete']
        # completed_df = pd.DataFrame(completed_projects)
        # completed_df['status_last_change'] = pd.to_datetime(completed_df.get('status_last_change'))

        # completed_df['completed_week'] = completed_df['status_last_change'] - pd.to_timedelta(completed_df['status_last_change'].dt.dayofweek, unit='d')
        # completed_df['completed_month'] = completed_df['status_last_change'].dt.to_period('M').dt.to_timestamp()

        # base_plot = BasePlot()

        # weekly_completed_chart = alt.Chart(completed_df).mark_line().encode(
        #     x=alt.X('completed_week:T', title='Week Starting'),
        #     y='count():Q',
        #     tooltip=['completed_week:T', 'count():Q']
        # )
        # styled_weekly_chart = base_plot.style_chart(weekly_completed_chart, 'Weekly Completed Projects')
        # st.altair_chart(styled_weekly_chart, use_container_width=True)

        # monthly_completed_chart = alt.Chart(completed_df).mark_line().encode(
        #     x=alt.X('completed_month:T', title='Month Starting'),
        #     y='count():Q',
        #     tooltip=['completed_month:T', 'count():Q']
        # )
        # styled_monthly_chart = base_plot.style_chart(monthly_completed_chart, 'Monthly Completed Projects')
        # st.altair_chart(styled_monthly_chart, use_container_width=True)


    ############
    ############
    ############
    with st.expander('FS Feedback'):
        include_conditions = {'fs_submitted_feedback': True}
        exclude_conditions = {'status': 'Complete'}

    # st.cache(ttl=60*60*24)
        fs_feedback = ddb.query_items(include_conditions, exclude_conditions)
        if not fs_feedback:
            st.warning('No feedback received.')
        
        # Step 1: Organize feedback by site_code
        feedback_by_site = {}
        for entry in fs_feedback:
            site_code = entry.get('site_code')
            if entry.get('fs_submitted_feedback') and site_code:
                if site_code not in feedback_by_site:
                    feedback_by_site[site_code] = []
                feedback_by_site[site_code].extend(entry.get('feedback_history', []))

        # Step 2: Sort the feedback entries by timestamp in descending order
        for site_code, feedback_list in feedback_by_site.items():
            feedback_by_site[site_code] = sorted(feedback_list, key=lambda x: datetime.strptime(x['fs_feedback_timestamp'], '%Y-%m-%dT%H:%M:%S'), reverse=True)

        # Step 3: Use Streamlit's expander feature to display feedback
        for site_code, feedback_list in feedback_by_site.items():
            with st.expander(f"Feedback for site code: {site_code}"):
                for feedback in feedback_list:
                    st.markdown(f"#### Feedback by {feedback['fs_feedback_name']} on {feedback['fs_feedback_timestamp']}")
                    st.text(feedback['fs_feedback_text'])
                    # Handle displaying images if there are any
                    if feedback['fs_feedback_pics']:
                        for file_path in feedback.get('fs_feedback_file_paths', []):
                            st.image(file_path)
