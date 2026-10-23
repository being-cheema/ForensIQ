"""
feature_eng2.py
===============
Backward compatibility wrapper forwarding to feature_engineering.py.
"""

from feature_engineering import (
    FEATURE_COLUMNS,
    load_json,
    get_active_event_log_path,
    build_macb_features,
    build_log_gap_features,
    build_feature_matrix,
    main
)

if __name__ == "__main__":
    main()
