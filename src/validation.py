# validation.py
OPERATION_RULES = {
    'compare_file_versions': {
        'order': 1,
        'excludes': [],
        'requires': [],
    },
    'download_logs': {
        'order': 2,
        'excludes': [],
        'requires': [],
    },
    'update_file_versions': {
        'order': 3,
        'excludes': [],
        'requires': [],
    },
    'nvram_reset': {
        'order': 4,
        'excludes': ['nvram_demo_reset'],
        'requires': [],
    },
    'nvram_demo_reset': {
        'order': 4,
        'excludes': ['nvram_reset'],
        'requires': [],
    },
}

def validate_operations(selected_operations):
    selected_ops = [op for op, selected in selected_operations.items() if selected]
    for op in selected_ops:
        excludes = OPERATION_RULES[op]['excludes']
        if any(excluded_op in selected_ops for excluded_op in excludes):
            raise ValueError(f"Operation '{op.replace('_', ' ').title()}' cannot be selected with {', '.join(excludes)}")
    for op in selected_ops:
        requires = OPERATION_RULES[op]['requires']
        if any(req_op not in selected_ops for req_op in requires):
            raise ValueError(f"Operation '{op.replace('_', ' ').title()}' requires {', '.join(requires)} to be selected")
    ordered_ops = sorted(selected_ops, key=lambda op: OPERATION_RULES[op]['order'])
    if ordered_ops != selected_ops:
        correct_order = " > ".join([op.replace('_', ' ').title() for op in ordered_ops])
        raise ValueError(f"Operations must be executed in the correct order: {correct_order}")
    return True
