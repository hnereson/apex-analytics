import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt
from decimal import Decimal
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from ddb_class import DDB
from plots import BasePlot, Boxplot, ScatterPlot, BarPlot,HeatmapPlot,HistogramPlot
from processing import get_current_timestamp, preprocess_projects, group_statuses, process_dates, remaining_budgets
from sql_queries import run_sql_query, facilities_sql
from utils import grab_s3_file, current_year, date_pull, blank,display_report, generate_presigned_url, check_s3_file


cipc_board = st.secrets['CIPC_BOARD_ID']
opc_board = st.secrets['OPC_BOARD_ID']
ddb = DDB(table='apex')

#---------------SETTINGS--------------------
page_title = "Apex Analytics   "
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
dts = date_pull() 
today = dts['today'] 
last_week = dts['last_week'] 
next_week = dts['next_week'] 

facilities_df = run_sql_query(facilities_sql)
sorted_sites = sorted(facilities_df['site_code'].unique()) 

st.sidebar.title('APEX Admin Portal')  
# st.sidebar.caption(f"Routes last calculated for: **{st.session_state.get('last_update', 'N/A')}**")
nav = st.sidebar.radio("Navigate to section", [
    'Apex Analytics', 
    'Reporting Admin'
])   
st.sidebar.markdown('-----')
enter_password = st.sidebar.text_input("Password", type = 'password')

if password_authenticate(enter_password):
    st.session_state['valid_password'] = True
else: 
    st.warning("Enter Password to Access")
    st.session_state['valid_password'] = False

password = password_authenticate(enter_password)

if nav == 'Apex Analytics':
    section = 'apex'
elif nav == 'Reporting Admin':
    section = 'reporting'


if password == "Admin":
    if section == 'apex':
        row0 = st.columns([1,3,1])
        row0[1].title(page_title)
        this_year = current_year()

        completed_projects = ddb.query_items({'scheduled_year': this_year, 'status': 'Complete'}, {})
        
        all_projects = ddb.list_items()
        projects = []
        projects_in_process = []
        projects_in_queue = []
        for project in all_projects:
            scheduled_year = project.get('scheduled_year')
            team = project.get('team')
            status = project.get('status')
            if scheduled_year ==this_year and status not in ['Complete','Inactive']:
                projects.append(project)
                group = project.get('monday_group')
                if group =='duplicate_of_reserve15117':
                    projects_in_queue.append(project)
                else:
                    projects_in_process.append(project)        
                
        budgets = grab_s3_file(f'budgets_{this_year}.csv', 'apex-project-files')
        budgets = budgets.drop(columns=['Landscaping and Snow Removal', 'Supplies'])
        remaining_budget = remaining_budgets(budgets, completed_projects)
        remaining_budget = remaining_budget.merge(facilities_df, left_on='RD', right_on='site_code', how='left')

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
            fund = form1[1].multiselect('Select Fund:', sorted(f for f in facilities_df['fund'].unique() if f is not None))
            form2 = st.columns([1,1])
            team = form2[1].multiselect('Select Teams:', ['cipc','opc'])
            assignee = form2[0].multiselect('Select Assignees:', sorted(unique_assignee_list))
            form3 = st.columns([1,1])
            project_type = form3[0].multiselect('Select Project Types:', sorted(project_type_list))
            line_item = form3[1].multiselect('Select P&L Line Item:', sorted(remaining_budget['line_item'].unique()))
            form4 = st.columns([1,1])
            in_queue_selected = form4[0].checkbox('Include In Queue Projects?')
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

            if line_item:
                project_list = [project for project in project_list if project.get('line_item') in line_item]

            if fund:
                rds_in_fund = facilities_df[facilities_df['fund'].isin(fund)]['site_code'].tolist()    
                project_list = [project for project in project_list if project.get('site_code') in rds_in_fund]
            
            return project_list

        # Apply the filter to both lists
        filtered_projects = filter_projects(projects, region, team, assignee, project_type, facilities_df)
        filtered_all_projects = filter_projects(all_projects, region, team, assignee, project_type, facilities_df)
        filtered_in_process = filter_projects(projects_in_process, region, team, assignee, project_type, facilities_df)
        
        if in_queue_selected == False:
            filtered_projects=filtered_in_process
        if not filtered_projects:
            st.error('No projects with the selected criteria')
        else:
            
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
            unique_statuses =[]
            # Process each project
            for project in projects:        
                funnel_category = project.get('grouped_status', "Other")
                priority = project.get('base_priority')
                if priority =='EMERGENCY':
                    priority ="Immediate"
                status = project.get('status')
                if status not in unique_statuses:
                    unique_statuses.append(status)
                color = priority_colors.get(priority, "grey")
                funnel_data[funnel_category][priority] += 1
            
            # st.write(unique_statuses)
            status_order = [
                'New Project',"Vendor Needed", 
                "Quote Requested", "Pending Approval", "Pending Schedule",
                "Awaiting Parts", "Scheduled","Follow Up", "Waiting for Invoice", "Other"
            ]    
            # Convert to DataFrame for easier visualization
            funnel_df = pd.DataFrame([
                {'grouped_status': status, 'base_priority': priority, 'count': count}
                for status, priority_data in funnel_data.items()
                for priority, count in priority_data.items()
            ])
            
            funnel_df['grouped_status'] = pd.Categorical(funnel_df['grouped_status'], categories=status_order, ordered=True)
            funnel_df.sort_values('grouped_status', inplace=True)

            funnel_df['base_priority'] = funnel_df['base_priority'].fillna('None')
            # funnel_df = funnel_df[funnel_df['grouped_status'] != 'New Project']
            # Aggregate the total projects by grouped_status for text labels
            total_projects_df = funnel_df.groupby('grouped_status')['count'].sum().reset_index()
            funnel_df['total_count'] = funnel_df.groupby('grouped_status')['count'].transform('sum')
            total_number_projects = funnel_df['count'].sum()
            funnel_df['projects_ratio'] = funnel_df['total_count'].astype(str) + '/' + str(total_number_projects)

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
                    alt.Tooltip('projects_ratio:N', title='Total Projects'),
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
                projects_df = pd.DataFrame(projects)
                # Convert 'grouped_status' to a categorical type with the specified order
                projects_df['grouped_status'] = pd.Categorical(projects_df['grouped_status'],categories=status_order, ordered=True)
                projects_df.sort_values('grouped_status', inplace=True)

                # Calculate the mean of 'days_in_status' for each 'status' and 'assignee'
                mean_days_df = projects_df.groupby(['grouped_status'])['days_in_status'].mean().reset_index()

                # Plotting
                duration_chart = alt.Chart(mean_days_df).mark_bar().encode(
                    x=alt.X('grouped_status:N', sort=status_order),  # Explicitly sorting the x-axis
                    y='days_in_status:Q',
                    tooltip=['grouped_status', 'days_in_status']
                ).properties(
                    title='Average Days in Status by Status',
                    width=600,
                    height=400
                )
                st.altair_chart(duration_chart)
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
                hist_data = status_df.groupby(['days_in_status']).size().reset_index(name='count')
                # st.dataframe(status_df)
                scatter_plot = ScatterPlot()
                # scatter_plot.plot_projects_scatterplot('days_in_status','status',aggregated_data, "Projects by Days Open", status_order)
                hist = HistogramPlot()
                # st.table(hist_data)
                hist.plot_histogram(hist_data,'Histogram of Duration in Status', 'Days in Status','')
            
            ########### 3. budget heatmap ##########################
                heatmap = HeatmapPlot()
                # st.write(remaining_budget.columns)
                budget_plot = remaining_budget.groupby(['fund','line_item'])['budget_left'].sum().unstack()
                budget_plot = budget_plot.drop(columns=['fund','region'])
                # st.table(budget_plot)
                budget_plot = budget_plot.reset_index()

                # Melt the DataFrame
                budget_plot = budget_plot.melt(id_vars='fund', var_name='line_item', value_name='budget_left')
                # st.table(budget_plot)
                heatmap.display_heatmap(budget_plot, 'fund', 'line_item', 'budget_left', 'Current Budgets (*not changed by filters)')

            ############ 4. Boxplot by priority_values ('value_driven_priority') ############
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
                df = df[df['Cost Efficiency']<10000]
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


    if section == 'reporting':
        st.title('Incident & Scope Form Search')

        with st.form(key='incident-form'): 
            # search by RD (site_code), date range  
            aa1, aa2 = st.columns(2)
            sites = aa1.multiselect("Site", ['', 'All', 'North Region', 'Central Region', 'South Region'] + sorted_sites)
            reports_dr = aa2.date_input("Date Range", (last_week, today))
            r1, r2 = st.columns(2)
            reporting_types = r1.multiselect("Report Types", ['All','Break Ins','Incidents','Repair Requests'])
            download_only = r2.checkbox("Download files only?")
            reports_search = st.form_submit_button("Search") 
        
        if reports_search:

            aasites = [s for s in sites if s.startswith('RD')]
            if 'All' in sites: 
                aasites = sorted_sites
            elif 'North Region' in sites:
                aasites = facilities_df[facilities_df['region'].str.contains('North')]['site_code'].tolist()
            elif 'Central Region' in sites:
                aasites = facilities_df[facilities_df['region'].str.contains('Central')]['site_code'].tolist()
            elif 'South Region' in sites:
                aasites = facilities_df[facilities_df['region'].str.contains('South')]['site_code'].tolist()
            else:
                aasites = sites
            
            reporting_sites = set(sorted(aasites)) 
            reporting_types_set = set(reporting_types)

            start_date = reports_dr[0] 
            end_date = reports_dr[1]
            reports_table = DDB('incident-scope-form')
            list_of_reports=[]

            # change names
            with st.spinner("Preparing Historical Data..."):
                for site in reporting_sites:  
                    aitems = reports_table.query_by_index(query_params={'index': 'SiteCodeIndex', 'field': 'site_code', 'value': site}) 
                    aitems = sorted(aitems, key=lambda x: x.get('created_at', ''), reverse=True)
                    # st.write(aitems)
                    for aitem in aitems:  
                        found_results = True 
                        # pull latest by created_at field  
                        # aitem = sorted(aitem, key=lambda x: x.get('created_at', ''), reverse=True)[0] 
                        report_date = aitem.get("Today's date") or aitem.get("Report date", None)
                        report_types_str = aitem.get("Which are you reporting? (Select all that apply)")

                        # Convert the string that looks like a list to an actual list
                        report_types = report_types_str.strip("[]").replace("'", "").split(', ')

                        if report_date:
                            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
                            if (report_date < start_date) or (report_date > end_date):
                                continue

                        if 'All' in reporting_types_set or any(rt.strip() in {'Break In', 'Non-Break In Incident', 'Repair Request'} for rt in report_types):
                            # if 'Incidents' in reporting_types_set and not any(rt.strip() in {'Break In', 'Non-Break In Incident'} for rt in report_types):
                            if 'Incidents' in reporting_types_set and 'Non-Break In Incident' not in report_types:
                                continue
                            if 'Break Ins' in reporting_types_set and 'Break In' not in report_types:
                                continue
                            if 'Repair Requests' in reporting_types_set and 'Repair Request' not in report_types:
                                continue

                            report_type_combined = " & ".join(report_types) if report_types else ""
                            list_of_reports.append({'aitem': aitem, 'date': report_date, 'reports': report_type_combined})

                if len(list_of_reports) ==0:
                    st.warning('No reports found.')

                if download_only == False:
                    for report_data in list_of_reports:  # assuming list_of_audits contains multiple audit data
                        report = report_data['aitem']
                        # st.write(report['id'])
                        id = report['id'][-5:]
                        # st.write(id)
                        with st.expander(f"{report_data['reports']} Report for {report['site_code']} on {report_data['date']}"):
                            # st.write(f'### **Download pdfs and pictures:**')
                            for report_pdf, path in report['file_paths'].items():
                                report_name = report_pdf.replace('_pdf_path', '')
                                report_url = generate_presigned_url('apex-project-files', path)
                                st.markdown(f'[Download {report_name} pdf]({report_url})')

                            first_path = next(iter(report['file_paths'].values()))
                            directory_path = '/'.join(first_path.split('/')[:-1])

                            attachments_zip_path = check_s3_file('apex-project-files', directory_path, id)
                            # st.write(attachments_zip_path)
                            if attachments_zip_path:
                                attachments_url = generate_presigned_url('apex-project-files', attachments_zip_path)
                            st.markdown(f"[Download All Pictures (zip file)]({attachments_url})")

                            blank()

                            try:
                                display_report(report)
                                # st.write('hi')
                            except:
                                st.warning('Error retrieving set of questions and answers. Please download the pdf file instead.')
                else:
                    blank()
                    for report_data in list_of_reports:  # Assuming list_of_reports contains multiple report data
                        report = report_data['aitem']
                        id = report['id'][-5:]
                        # st.write(report['id'])
                        report_title = f"{report['site_code']} {report_data['reports']} Report on {report_data['date']}"
                        st.write(f'**{report_title}**')  # Display the title of the report
                        # Generate and display download links for PDFs
                        for report_pdf, path in report['file_paths'].items():
                            report_name = report_pdf.replace('_pdf_path', '')
                            report_url = generate_presigned_url('apex-project-files', path)
                            st.markdown(f'[Download {report_name} pdf]({report_url})')

                        # Check for attachments and generate download link
                        first_path = next(iter(report['file_paths'].values()))
                        directory_path = '/'.join(first_path.split('/')[:-1])
                        attachments_zip_path = check_s3_file('apex-project-files', directory_path, id)
                        if attachments_zip_path:
                            attachments_url = generate_presigned_url('apex-project-files', attachments_zip_path)
                            st.markdown(f"[Download All Pictures (zip file)]({attachments_url})")
                        "---"
