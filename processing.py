from datetime import datetime

def get_current_timestamp():
        return datetime.utcnow()

def preprocess_projects(projects):
    now = get_current_timestamp()
    # Convert string dates to datetime objects and calculate days
    for project in projects:
        status_last_change = project.get('status_last_change')
        open_date = project.get('open_date')
        completed_date = project.get('completed_date')
        scheduled_dates = project.get('scheduled_dates')

        if status_last_change:
            project['status_last_change'] = datetime.strptime(str(status_last_change), '%Y-%m-%d %H:%M:%S')
            project['days_in_status'] = (now - project['status_last_change']).days
        else:
            project['days_in_status'] = None  # Or set a default value like 0 or -1

        if completed_date:
            project['completed_date'] = datetime.strptime(str(completed_date), '%Y-%m-%d').date()

        if open_date:
            project['open_date'] = datetime.strptime(str(open_date).replace(' UTC', ''), '%Y-%m-%d %H:%M:%S')
            project['days_open'] = (now - project['open_date']).days
        else:
            project['days_open'] = None  # Or set a default value like 0 or -1
        if scheduled_dates:
            # Split the dates
            start_date_str, end_date_str = scheduled_dates.split(' - ')
            
            # Convert to datetime objects
            project['min_scheduled_date'] = datetime.strptime(start_date_str, '%Y-%m-%d')
            project['max_scheduled_date']= datetime.strptime(end_date_str, '%Y-%m-%d')
    return projects

status_mapping = {
    "New Project": "New Project",
    'New Project*':'New Project',
    "Gathering Scope": "Gathering Scope",
    "Vendor Needed": "Vendor Needed",
    "Quote Requested": "Quote Requested",
    "Estimate Walk Scheduled": "Quote Requested",
    "Waiting for Estimate": "Quote Requested",
    "Waiting for Estimate/Proof": "Quote Requested",
    "Pending Approval": "Pending Approval",
    "Pending 2nd Approval": "Pending Approval",
    "Approved":"Pending Schedule",
    "Pending Schedule": "Pending Schedule",
    "Awaiting Parts": "Awaiting Parts",
    "Shipped":"Awaiting Parts",
    "Scheduled": "Scheduled",
    "FS Handling": "Scheduled",
    "FS Queue": "Scheduled",
    "In Progress": "Scheduled",
    "Waiting for Invoice": "Waiting for Invoice",
    "Waiting on Paperwork": "Waiting for Invoice",
    "Follow Up":"Follow Up",
    "FS Verifying":"Follow Up"
}

def group_statuses(projects):
    if projects:
        for project in projects:
            project['grouped_status'] = status_mapping.get(project.get('status'), 'Other')
    return projects

# Function to process dates and add month-year info
def process_dates(projects):
    processed = []
    for project in projects:
        open_date = project.get('open_date')
        completed_date = project.get('completed_date')

        # Format open_date if it exists
        if open_date:
            project['open_month_year'] = open_date.strftime('%Y-%m')

        # Format completed_date if it exists
        if completed_date:
            project['completed_month_year'] = completed_date.strftime('%Y-%m')

        processed.append(project)
    return processed

def remaining_budgets(budgets, completed_projects):
    budget_df = budgets.copy()
    costs = {}
    # Step 1: Aggregate Costs
    for item in completed_projects:
        site_code = item.get('site_code')
        line_item = item.get('line_item')
        cost = float(item.get('cost'))  # Assuming Decimal can be converted to float
        costs[(site_code, line_item)] = costs.get((site_code, line_item), 0) + cost

    # Step 2: Subtract Costs from Budget DataFrame
    for site_code, line_item in costs:
        if line_item in budget_df.columns and site_code in budget_df['RD'].values:
            budget_df.loc[budget_df['RD'] == site_code, line_item] -= costs[(site_code, line_item)]
    # budget_df = budget_df.drop(columns='recast_capex')
    budget_df = budget_df.melt('RD', var_name = 'line_item', value_name='budget_left')
    return budget_df