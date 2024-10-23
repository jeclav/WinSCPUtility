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
    """
    Validates the selected operations against the defined rules.
    
    :param selected_operations: Dict of selected operations with boolean values.
    :return: True if validation passes.
    :raises ValueError: If validation fails.
    """
    # Convert selected_operations dict to a list of selected operation keys
    selected_ops = [op for op, selected in selected_operations.items() if selected]
    
    # Check for mutual exclusivity
    for op in selected_ops:
        excludes = OPERATION_RULES[op]['excludes']
        if any(excluded_op in selected_ops for excluded_op in excludes):
            excluded_op_names = [op.replace('_', ' ').title() for op in excludes if op in selected_ops]
            raise ValueError(f"Operation '{op.replace('_', ' ').title()}' cannot be selected with {', '.join(excluded_op_names)}")
    
    # Check for required operations
    for op in selected_ops:
        requires = OPERATION_RULES[op]['requires']
        if any(req_op not in selected_ops for req_op in requires):
            required_op_names = [op.replace('_', ' ').title() for op in requires]
            raise ValueError(f"Operation '{op.replace('_', ' ').title()}' requires {', '.join(required_op_names)} to be selected")
    
    # No need to enforce selection order; operations will be executed in the correct order
    return True
