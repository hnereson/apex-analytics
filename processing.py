

status_mapping = {
    "New Project": "New Project",
    "Gathering Scope": "Gathering Scope",
    "Vendor Needed": "Vendor Needed",
    "Quote Requested": "Quote Requested",
    "Estimate Walk Scheduled": "Quote Requested",
    "Waiting for Estimate": "Quote Requested",
    "Waiting for Estimate/Proof": "Quote Requested",
    "Pending Approval": "Pending Approval",
    "Pending 2nd Approval": "Pending Approval",
    "Pending Schedule": "Pending Schedule",
    "Awaiting Parts": "Awaiting Parts",
    "Scheduled": "Scheduled",
    "FS Handling": "Scheduled",
    "FS Queue": "Scheduled",
    "In Progress": "Scheduled",
    "Waiting for Invoice": "Waiting for Invoice",
    "Waiting on Paperwork": "Waiting for Invoice",
    "Follow Up":"Follow Up"
}

def group_statuses(projects):
    for project in projects:
        project['grouped_status'] = status_mapping.get(project.get('status'), 'Other')
    return projects