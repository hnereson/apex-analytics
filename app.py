import streamlit as st
import streamlit.components.v1 as components
from sql_queries import run_sql_query, facilities_sql
import pandas as pd
from ddb_class import DDB
from plots import BasePlot, Boxplot, ScatterPlot, BarPlot
from datetime import datetime
import altair as alt
from decimal import Decimal
from collections import defaultdict
from matplotlib.sankey import Sankey
import matplotlib.pyplot as plt
from processing import get_current_timestamp, preprocess_projects, group_statuses, process_dates
from dateutil.relativedelta import relativedelta


cipc_board = st.secrets['CIPC_BOARD_ID']
opc_board = st.secrets['OPC_BOARD_ID']
ddb = DDB(table='apex')

#---------------SETTINGS--------------------
page_title = "Apex Analytics"
page_icon = ":red-circle:"  #https://www.webfx.com/tools/emoji-cheat-sheet/
layout= "centered"
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
now = get_current_timestamp()

enter_password = st.sidebar.text_input("Password", type = 'password')

if password_authenticate(enter_password):
    st.session_state['valid_password'] = True
else: 
    st.warning("Enter Password to Access")
    st.session_state['valid_password'] = False

password = password_authenticate(enter_password)

if password == "Admin":

    row0 = st.columns([1,3,1])
    row0[1].title(page_title)
    include_conditions = {'scheduled_year': '2023'}
    exclude_conditions = {'status': 'Complete'}

    st.cache(ttl=60*60*24)
    # completed_projects = ddb.query_items({'scheduled_year': '2023', 'status': 'Complete'}, {})
    projects = ddb.query_items(include_conditions, exclude_conditions)
    all_projects = ddb.list_items()
    all_projects = all_projects['Items']
    facilities_df = run_sql_query(facilities_sql)

    # Get all assignees in current projects
    assignee_list = []
    for project in all_projects:
        assignee = project.get('assignee')
        if assignee not in assignee_list:
            assignee_list.append(assignee)

    unique_assignees = set()
    for assignees in assignee_list:
        for assignee in assignees.split(','):
            unique_assignees.add(assignee.strip())

    unique_assignee_list = list(unique_assignees)

    # Get unique project types
    project_type_list = []
    for project in all_projects:
        project_type = project.get('project')
        if project_type not in project_type_list:
            project_type_list.append(project_type)

    with st.form("Filters"):
        blank()
        form1 = st.columns([1,1])
        region = form1[0].multiselect('Select Regions:',['North','Central','South'])
        team = form1[1].multiselect('Select Teams:', ['cipc','opc'])
        form2 = st.columns([1,1])
        assignee = form2[0].multiselect('Select Assignees:', unique_assignee_list)
        project_type = form2[1].multiselect('Select Project Types:', project_type_list)
        blank()
        submitted = st.form_submit_button("Confirm Selection")
        if submitted:
            st.success('Submitted')
        
    def filter_projects(project_list, region, team, assignee, project_type, facilities_df):
        if region:
            selected_site_codes = facilities_df[facilities_df['region'].isin(region)]['site_code'].tolist()
            project_list = [project for project in project_list if project.get('site_code') in selected_site_codes]

        if team:
            project_list = [project for project in project_list if project.get('team') in team]

        if assignee:
            project_list = [project for project in project_list if any(a.strip() in project.get('assignee', '').split(', ') for a in assignee)]

        if project_type:
            project_list = [project for project in project_list if project.get('project') in project_type]

        return project_list

    # Apply the filter to both lists
    filtered_projects = filter_projects(projects, region, team, assignee, project_type, facilities_df)
    filtered_all_projects = filter_projects(all_projects, region, team, assignee, project_type, facilities_df)


    projects = preprocess_projects(filtered_projects)
    all_projects = preprocess_projects(filtered_all_projects)

    ############### Funnel ###################
    blank()
    blank()
    # Priority colors
    priority_colors = {
        "Critical EMERGENCY": "red",
        "Immediate": "orange",
        "High": "#008080", # Dark Teal
        "Medium": "#40E0D0", # Teal
        "Low": "#AFEEEE", # Light Teal
        "None": "grey",
    }
    priority_order = ["Critical EMERGENCY", "Immediate", "High", "Medium", "Low", "None"]

    # Initialize a structure to hold the aggregated data
    funnel_data = defaultdict(lambda: defaultdict(int))
    projects = group_statuses(projects)

    # Process each project
    for project in projects:        
        funnel_category = project.get('grouped_status', "Other")
        priority = project.get('base_priority')
        if priority =='EMERGENCY':
            priority ="Immediate"
        color = priority_colors.get(priority, "grey")
        funnel_data[funnel_category][priority] += 1

    status_order = [
        "New Project", "Gathering Scope", "Vendor Needed", 
        "Quote Requested", "Pending Approval", "Pending Schedule",
        "Awaiting Parts", "Scheduled", "Waiting for Invoice","Follow Up", "Other"
    ]    

    # Convert to DataFrame for easier visualization
    funnel_df = pd.DataFrame([
        {'grouped_status': status, 'base_priority': priority, 'count': count}
        for status, priority_data in funnel_data.items()
        for priority, count in priority_data.items()
    ])

    # Sort the DataFrame based on the predefined status order

    funnel_df['grouped_status'] = pd.Categorical(funnel_df['grouped_status'], categories=status_order, ordered=True)
    funnel_df.sort_values('grouped_status', inplace=True)

    funnel_df['base_priority'] = funnel_df['base_priority'].fillna('None')

    # Aggregate the total projects by grouped_status for text labels
    total_projects_df = funnel_df.groupby('grouped_status')['count'].sum().reset_index()
    funnel_df['total_count'] = funnel_df.groupby('grouped_status')['count'].transform('sum')

    # Create the vertical stacked bar chart
    chart = alt.Chart(funnel_df).mark_bar(
        cornerRadiusTopLeft=3,
        cornerRadiusTopRight=3
    ).encode(
        y=alt.Y('grouped_status:N', title=None, sort=status_order),
        x=alt.X('sum(count):Q', title=None, axis=alt.Axis(labels=False, title=None, grid=False)),
        color=alt.Color('base_priority:N', scale=alt.Scale(domain=priority_order + ['None'], range=[priority_colors[p] for p in priority_order] + ['grey']),sort=priority_order),
        order=alt.Order('color_base_priority_sort_index:Q'),
        tooltip=[
            alt.Tooltip('grouped_status:N', title='Status'),
            alt.Tooltip('total_count:Q', title='Total Projects'),
            alt.Tooltip('base_priority:N', title='Priority'),
            alt.Tooltip('count:Q', title='Projects by Priority', aggregate='sum', format='.0f')
        ]
    )

    # Data labels for total number of projects
    text = alt.Chart(total_projects_df).mark_text(
        align='left',
        baseline='middle',
        dx=3  # Nudging the text to the right of the bar
    ).encode(
        y=alt.Y('grouped_status:N', sort=status_order),
        x=alt.X('count:Q', stack='zero'),  # Align text with the end of the bars
        text=alt.Text('count:Q')
    )


    # Apply styling from BasePlot
    base_plot = BasePlot()
    styled_chart = base_plot.style_chart(chart + text, "Project Distribution by Status", 500, 400, grid=False)

    # This is how you would display the chart in a Streamlit app
    st.altair_chart(styled_chart, use_container_width=True)



    with st.expander('Current Realities'):
        # row1= st.columns([1,1])

    ############ 1. # of projects by type and the avg days they've been open ##########################
        avg_days_color = 'orange'

        project_data = {}
        for project in projects:
            y_axis= project.get('project', 'Unknown')  # Providing a default project if none is found
            if y_axis not in project_data:
                project_data[y_axis] = {'count': 0, 'total_days': 0}
            project_data[y_axis]['count'] += 1
            project_data[y_axis]['total_days'] += project.get('days_open', 0)  # Default to 0 if 'days_open' is not present

        project_df = pd.DataFrame([
            {
                'project_type': y_axis,
                'projects': data['count'],
                'avg_days_open': (data['total_days'] / data['count']) if data['count'] > 0 else 0
            }
            for y_axis, data in project_data.items()
        ])
        agg_project_df = project_df.groupby('project_type')['projects'].sum().reset_index()

        # Sort in descending order
        sorted_project_types = agg_project_df.sort_values(by='projects', ascending=False)['project_type']

        # Create the bar chart with custom sorting applied
        project_type_chart = alt.Chart(project_df).mark_bar(color='teal').encode(
            x=alt.X('projects:Q',title='Number of Projects Open'),
            y=alt.Y('project_type:N', axis=alt.Axis(title=None), sort=list(sorted_project_types))
        )

        # Create the triangle chart with custom sorting applied
        triangle_avg_days = alt.Chart(project_df).mark_point(
            shape='triangle', size=150, color=avg_days_color, opacity=0.7
        ).encode(
            y=alt.Y('project_type:N', sort=list(sorted_project_types)),
            x=alt.X('avg_days_open:Q', title='Avg Days Open'),
            color=alt.value(avg_days_color)
        )
        combined_chart = alt.layer(project_type_chart, triangle_avg_days).resolve_scale(
            x='independent',
        ).encode(
            tooltip=['project_type:N', 'projects:Q', 'avg_days_open:Q']
        )

        # Apply styling
        combined_chart = BasePlot().style_chart(combined_chart, 'Current Projects by Type', width=600, height=600, grid=True)

        # Display the chart
        st.altair_chart(combined_chart)
    ############ 2. # of projects in each status and the average days in that status
        status_data = []
        for project in projects:
            status = project.get('grouped_status')
            days_in_status = project.get('days_in_status')

            if status is not None and days_in_status is not None:
                status_data.append({
                    'status': status,
                    'days_in_status': days_in_status
                })

        status_df = pd.DataFrame(status_data)
        
        # Group by 'days_in_status' and 'status' and count the number of projects
        aggregated_data = status_df.groupby(['days_in_status', 'status']).size().reset_index(name='count')

        # st.dataframe(status_df)
        scatter_plot = ScatterPlot()
        scatter_plot.plot_projects_scatterplot('days_in_status','status',aggregated_data, "Projects by Days Open", status_order)

    ############ 3. Boxplot by priority_values ('value_driven_priority') ############
        # col1,col2= st.columns([2,2])
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
        # with col1:
        boxplot_instance.display_boxplot(df, 'Cost Efficiency', 'Base Priority', title_text, color_scheme)


    with st.expander('Historical Trends'):
    ############### Opened vs Closed by Month ###################
        processed_projects = process_dates(all_projects)

        # Initialize counters
        monthly_counts = defaultdict(lambda: {'opened': 0, 'completed': 0})

        # Filter to last 12 months
        end_date = datetime.now()
        start_date = end_date - relativedelta(months=12)

        for project in processed_projects:
            open_month_year = project.get('open_month_year')
            completed_month_year = project.get('completed_month_year')

            if open_month_year and pd.to_datetime(project['open_date']) >= start_date:
                monthly_counts[open_month_year]['opened'] += 1
            if completed_month_year and pd.to_datetime(project['completed_date']) >= start_date and pd.to_datetime(project['completed_date']) <= end_date:
                monthly_counts[completed_month_year]['completed'] += 1

        # Convert to DataFrame for plotting
        monthly_data = pd.DataFrame.from_dict(monthly_counts, orient='index').reset_index().rename(columns={'index': 'month_year'})
        monthly_melted = monthly_data.melt(id_vars=['month_year'], value_vars=['opened', 'completed'], var_name='status', value_name='count')
        blank()
        # Plotting
        bar_plot = BarPlot()
        ht_row = st.columns([1,2,1])
        ht_row[1].caption('Projects Opened and Completed by Month')
        bar_plot.plot_grouped_bar(monthly_melted, 'month_year', 'count', 'status', 'Projects Opened and Completed by Month')

    ############ 4. emergency outstanding projects table ############
    with st.expander("Overdue Emergency Projects"):
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
        if not filtered_projects_df.empty: 
            filtered_projects_df['id_link'] = filtered_projects_df.apply(
                lambda row: f"<a href='https://reddotstorage2.monday.com/boards/{row['team_board']}/pulses/{row['id']}' target='_blank'>{row['id']}</a>", axis=1)
            
            filtered_projects_df.drop(columns=['id', 'team_board'], inplace=True)
            filtered_projects_df = filtered_projects_df.sort_values('Days in status',ascending=False)
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
            st.write(html, unsafe_allow_html=True)
        else:
            st.success('There are no outstanding Emergency projects.')
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
