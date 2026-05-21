from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
import pandas as pd
import datetime
import time
import os
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Valid users for authentication
VALID_USERS = {
    "TGS001": {"password": "admin123", "name": "Ahmad Rahman"},
    "TGS002": {"password": "tech456", "name": "Sarah Lee"},
    "TGS003": {"password": "ops789", "name": "Kumar Raj"}
}

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_mor_data():
    """Load the MOR data from Excel file"""
    if not os.path.exists('MOR_KGL.xlsx'):
        raise FileNotFoundError("MOR_KGL.xlsx file not found")

    print("Found MOR_KGL.xlsx file, attempting to load...")
    
    # Try different possible sheet names
    possible_sheets = [None, 'Sheet1', 'MOR', 'Data', 'Equipment', 0]
    
    for sheet in possible_sheets:
        try:
            if sheet is None:
                df = pd.read_excel('MOR_KGL.xlsx', engine='openpyxl')
            else:
                df = pd.read_excel('MOR_KGL.xlsx', sheet_name=sheet, engine='openpyxl')
            
            print(f"Successfully loaded {len(df)} rows from MOR_KGL.xlsx (sheet: {sheet})")
            print(f"Columns found: {list(df.columns)}")
            
            # Validate that we have the required columns
            required_columns = ['Equipment', 'Failure Scenario']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"Missing required columns: {missing_columns}")
                continue
            else:
                # Clean the data
                df = df.dropna(subset=['Equipment', 'Failure Scenario'])
                print(f"After cleaning: {len(df)} rows with valid Equipment and Failure Scenario")
                return df
                    
        except Exception as e:
            print(f"Failed to load sheet {sheet}: {str(e)}")
            continue
    
    raise ValueError("Could not load valid data from any sheet in MOR_KGL.xlsx")

def init_session():
    """Initialize session variables"""
    if 'selected_equipment' not in session:
        session['selected_equipment'] = []
    if 'num_equipment_fail' not in session:
        session['num_equipment_fail'] = 1
    if 'selected_scenarios' not in session:
        session['selected_scenarios'] = []
    if 'active_scenarios' not in session:
        session['active_scenarios'] = []
    if 'timer_start' not in session:
        session['timer_start'] = None
    if 'scenario_start_time' not in session:
        session['scenario_start_time'] = None

@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('equipment'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        password = request.form['password']
        
        if staff_id in VALID_USERS and VALID_USERS[staff_id]['password'] == password:
            session['logged_in'] = True
            session['username'] = VALID_USERS[staff_id]['name']
            session['staff_id'] = staff_id
            init_session()
            return redirect(url_for('equipment'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/equipment', methods=['GET', 'POST'])
@login_required
def equipment():
    init_session()
    
    df = load_mor_data()
    # Get ALL unique equipment from the data - no filtering
    equipment_list = df['Equipment'].dropna().unique().tolist()
    
    print(f"Total equipment found: {len(equipment_list)}")
    print(f"Equipment list: {equipment_list}")
    
    if request.method == 'POST':
        if 'num_equipment' in request.form:
            session['num_equipment_fail'] = int(request.form['num_equipment'])
            session['selected_equipment'] = []
        elif 'equipment_action' in request.form:
            equipment_name = request.form['equipment_name']
            action = request.form['equipment_action']
            
            if action == 'select':
                if (equipment_name not in session['selected_equipment'] and 
                    len(session['selected_equipment']) < session['num_equipment_fail']):
                    session['selected_equipment'].append(equipment_name)
                    flash(f'✅ {equipment_name} selected!', 'success')
            elif action == 'deselect':
                if equipment_name in session['selected_equipment']:
                    session['selected_equipment'].remove(equipment_name)
                    flash(f'❌ {equipment_name} deselected!', 'info')
        elif 'clear_all' in request.form:
            session['selected_equipment'] = []
            flash('All equipment cleared', 'info')
        elif 'next_scenarios' in request.form:
            return redirect(url_for('scenario'))
    
    current_selected = len(session['selected_equipment'])
    max_allowed = session['num_equipment_fail']
    max_reached = current_selected >= max_allowed
    
    return render_template('equipment.html', 
                         equipment_list=equipment_list,
                         selected_equipment=session['selected_equipment'],
                         num_equipment_fail=session['num_equipment_fail'],
                         current_selected=current_selected,
                         max_allowed=max_allowed,
                         max_reached=max_reached)

@app.route('/debug_alarms')
@login_required
def debug_alarms():
    """Debug route to check alarm status for active scenarios"""
    
    if not session.get('active_scenarios'):
        return "<h3>No active scenarios found</h3><p>Please select scenarios first.</p>"
    
    debug_output = []
    debug_output.append("<h2>🔍 Alarm Debug Information</h2>")
    debug_output.append(f"<p><strong>Active Scenarios:</strong> {len(session['active_scenarios'])}</p>")
    
    # Process each scenario
    all_alarms = {'ATS': [], 'FSCADA': [], 'HMI': []}
    
    for i, scenario in enumerate(session['active_scenarios']):
        debug_output.append(f"<h3>Scenario {i+1}:</h3>")
        debug_output.append(f"<ul>")
        debug_output.append(f"<li><strong>Equipment:</strong> {scenario.get('Equipment', 'N/A')}</li>")
        debug_output.append(f"<li><strong>Failure Scenario:</strong> {scenario.get('Failure Scenario', 'N/A')}</li>")
        debug_output.append(f"<li><strong>Classification:</strong> {scenario.get('Failure Classification', 'N/A')}</li>")
        
        # Check alarm data
        ats_alarm = scenario.get('ATS Alarm Description', '')
        fscada_alarm = scenario.get('FSCADA Alarm Description', '')
        hmi_alarm = scenario.get('HMI Alarm', '')
        
        debug_output.append(f"<li><strong>ATS Alarm Raw:</strong> '{ats_alarm}'</li>")
        debug_output.append(f"<li><strong>FSCADA Alarm Raw:</strong> '{fscada_alarm}'</li>")
        debug_output.append(f"<li><strong>HMI Alarm Raw:</strong> '{hmi_alarm}'</li>")
        
        # Test filtering logic
        ats_valid = ats_alarm and str(ats_alarm).strip() and str(ats_alarm).strip().lower() not in ['n/a', 'no alarm triggered', 'none']
        fscada_valid = fscada_alarm and str(fscada_alarm).strip() and str(fscada_alarm).strip().lower() not in ['n/a', 'no alarm triggered', 'none']
        hmi_valid = hmi_alarm and str(hmi_alarm).strip() and str(hmi_alarm).strip().lower() not in ['n/a', 'no alarm triggered', 'none']
        
        debug_output.append(f"<li><strong>ATS Valid:</strong> {ats_valid}</li>")
        debug_output.append(f"<li><strong>FSCADA Valid:</strong> {fscada_valid}</li>")
        debug_output.append(f"<li><strong>HMI Valid:</strong> {hmi_valid}</li>")
        
        # Add to alarms if valid
        if ats_valid:
            equipment = scenario.get('Equipment', 'Unknown')
            all_alarms['ATS'].append(f"{equipment}: {ats_alarm}")
        if fscada_valid:
            equipment = scenario.get('Equipment', 'Unknown')
            all_alarms['FSCADA'].append(f"{equipment}: {fscada_alarm}")
        if hmi_valid:
            equipment = scenario.get('Equipment', 'Unknown')
            all_alarms['HMI'].append(f"{equipment}: {hmi_alarm}")
        
        debug_output.append(f"</ul>")
    
    # Show final alarm summary
    debug_output.append(f"<h3>📊 Final Alarm Summary:</h3>")
    debug_output.append(f"<ul>")
    debug_output.append(f"<li><strong>ATS Alarms:</strong> {len(all_alarms['ATS'])}")
    if all_alarms['ATS']:
        debug_output.append(f"<ul>")
        for alarm in all_alarms['ATS']:
            debug_output.append(f"<li>{alarm}</li>")
        debug_output.append(f"</ul>")
    debug_output.append(f"</li>")
    
    debug_output.append(f"<li><strong>FSCADA Alarms:</strong> {len(all_alarms['FSCADA'])}")
    if all_alarms['FSCADA']:
        debug_output.append(f"<ul>")
        for alarm in all_alarms['FSCADA']:
            debug_output.append(f"<li>{alarm}</li>")
        debug_output.append(f"</ul>")
    debug_output.append(f"</li>")
    
    debug_output.append(f"<li><strong>HMI Alarms:</strong> {len(all_alarms['HMI'])}")
    if all_alarms['HMI']:
        debug_output.append(f"<ul>")
        for alarm in all_alarms['HMI']:
            debug_output.append(f"<li>{alarm}</li>")
        debug_output.append(f"</ul>")
    debug_output.append(f"</li>")
    debug_output.append(f"</ul>")
    
    # Add navigation links
    debug_output.append(f"<hr>")
    debug_output.append(f"<p><a href='/guidelines'>← Back to Guidelines</a> | <a href='/debug_data'>Full Data Debug</a></p>")
    
    return "<br>".join(debug_output)

# Debug route to check data
@app.route('/debug_data')
@login_required
def debug_data():
    df = load_mor_data()
    
    debug_info = {
        'total_rows': len(df),
        'columns': list(df.columns),
        'unique_equipment': df['Equipment'].nunique(),
        'equipment_list': df['Equipment'].dropna().unique().tolist(),
        'sample_data': df.head(10).to_dict('records')
    }
    
    # Count scenarios per equipment
    scenarios_per_equipment = df.groupby('Equipment').size().to_dict()
    debug_info['scenarios_per_equipment'] = scenarios_per_equipment
    
    return f"<pre>{json.dumps(debug_info, indent=2, default=str)}</pre>"

# Update this section in app.py - scenario route


@app.route('/scenario', methods=['GET', 'POST'])
@login_required
def scenario():
    if not session['selected_equipment']:
        flash('Please select equipment first!', 'error')
        return redirect(url_for('equipment'))
    
    df = load_mor_data()
    print(f"Total data rows: {len(df)}")
    print(f"Unique equipment: {df['Equipment'].nunique()}")
    print(f"Equipment columns: {df['Equipment'].unique()}")
    
    if request.method == 'POST':
        if 'scenario_action' in request.form:
            equipment = request.form['equipment']
            scenario_text = request.form['scenario_text']
            action = request.form['scenario_action']
            
            # Find the scenario in the dataframe
            scenario_matches = df[(df['Equipment'] == equipment) & 
                                (df['Failure Scenario'] == scenario_text)]
            
            if len(scenario_matches) > 0:
                scenario_row = scenario_matches.iloc[0].to_dict()
                
                if action == 'select':
                    # Check if this exact scenario is already selected
                    exact_match = any(
                        s.get('Equipment') == equipment and s.get('Failure Scenario') == scenario_text 
                        for s in session['selected_scenarios']
                    )
                    
                    if exact_match:
                        flash(f'⚠️ This scenario is already selected!', 'warning')
                    else:
                        # Allow multiple scenarios from same equipment
                        session['selected_scenarios'].append(scenario_row)
                        flash(f'✅ Scenario selected from {equipment}: "{scenario_text}"', 'success')
                        print(f"Scenario added. Total selected: {len(session['selected_scenarios'])}")
                        
                elif action == 'deselect':
                    # Remove the specific scenario
                    original_count = len(session['selected_scenarios'])
                    session['selected_scenarios'] = [
                        s for s in session['selected_scenarios'] 
                        if not (s.get('Equipment') == equipment and s.get('Failure Scenario') == scenario_text)
                    ]
                    
                    if len(session['selected_scenarios']) < original_count:
                        flash(f'❌ Scenario deselected from {equipment}: "{scenario_text}"', 'info')
                        print(f"Scenario removed. Total selected: {len(session['selected_scenarios'])}")
                    else:
                        flash(f'⚠️ Scenario not found for deselection: {scenario_text}', 'warning')
            else:
                flash(f'❌ Scenario not found: "{scenario_text}" for {equipment}', 'error')
                
        elif 'clear_scenarios' in request.form:
            session['selected_scenarios'] = []
            flash('🗑️ All scenarios cleared', 'info')
            
        elif 'goto_guidelines' in request.form:
            if len(session['selected_scenarios']) >= 1:  # NEW: Only require 1 scenario
                session['active_scenarios'] = session['selected_scenarios']
                # Auto-start timer when scenarios are selected
                session['timer_start'] = time.time()
                session['scenario_start_time'] = datetime.datetime.now().isoformat()
                flash('✅ Proceeding to guidelines with selected scenarios', 'success')
                return redirect(url_for('guidelines'))
            else:
                flash(f'⚠️ Please select at least 1 scenario. Currently selected: {len(session["selected_scenarios"])}', 'warning')
    
    # Debug information
    print(f"Current selected scenarios: {len(session['selected_scenarios'])}")
    for i, scenario in enumerate(session['selected_scenarios']):
        print(f"  {i+1}. {scenario.get('Equipment')} - {scenario.get('Failure Scenario')}")
    
    # Get ALL scenarios for each selected equipment - no limits
    equipment_scenarios = {}
    for equipment in session['selected_equipment']:
        equipment_data = df[df['Equipment'] == equipment]
        equipment_scenarios[equipment] = equipment_data.to_dict('records')
        
        # Sort scenarios: MAJOR first, then MINOR
        equipment_scenarios[equipment] = sorted(
            equipment_scenarios[equipment], 
            key=lambda x: (0 if 'major' in str(x.get('Failure Classification', '')).lower() else 1, 
                          str(x.get('Failure Scenario', '')))
        )
        
        print(f"Equipment '{equipment}' has {len(equipment_scenarios[equipment])} scenarios")
    
    return render_template('scenario.html', 
                         equipment_scenarios=equipment_scenarios,
                         selected_scenarios=session['selected_scenarios'],
                         selected_equipment=session['selected_equipment'])

@app.route('/guidelines', methods=['GET', 'POST'])
@login_required
def guidelines():
    if not session['active_scenarios']:
        flash('Please select scenarios first!', 'error')
        return redirect(url_for('scenario'))
    
    if request.method == 'POST':
        if 'start_timer' in request.form:
            session['timer_start'] = time.time()
            session['scenario_start_time'] = datetime.datetime.now().isoformat()
        elif 'stop_timer' in request.form:
            session['timer_start'] = None
        elif 'save_complete' in request.form:
            # Calculate current elapsed time for status determination
            elapsed_time = 0
            if session.get('timer_start'):
                elapsed_time = time.time() - session['timer_start']
            
            # Determine status for flash message
            status = "Non-Relevant Failure" if elapsed_time <= 300 else "Relevant Failure"
            duration_min = round(elapsed_time / 60, 1)
            
            # Save the data
            save_resolution_data()
            
            # Clear session
            session.clear()
            session['logged_in'] = True
            session['username'] = request.form.get('username', '')
            session['staff_id'] = request.form.get('staff_id', '')
            init_session()
            
            # Show appropriate message based on status
            if status == "Non-Relevant Failure":
                flash(f'✅ Data saved! Status: {status} (Completed in {duration_min} min)', 'success')
            else:
                flash(f'⚠️ Data saved! Status: {status} (Took {duration_min} min - exceeded 5 min limit)', 'warning')
            
            return redirect(url_for('equipment'))
        elif 'new_scenario' in request.form:
            session['active_scenarios'] = []
            session['selected_scenarios'] = []
            session['timer_start'] = None
            return redirect(url_for('scenario'))
    
    # Timer should already be started from scenario page, but ensure it's running
    if session['timer_start'] is None:
        session['timer_start'] = time.time()
        session['scenario_start_time'] = datetime.datetime.now().isoformat()
    
    # FIXED: Calculate alarm status from ALL selected scenarios with better NaN/N/A handling
    all_alarms = {'ATS': [], 'FSCADA': [], 'HMI': []}
    
    def is_valid_alarm(alarm_value):
        """Check if alarm value is valid (not NaN, N/A, None, or empty)"""
        if alarm_value is None or pd.isna(alarm_value):
            return False
        
        alarm_str = str(alarm_value).strip().lower()
        
        # List of invalid alarm indicators
        invalid_indicators = [
            '', 'n/a', 'na', 'no alarm triggered', 'none', 
            'no alarm', 'nil', 'null', 'nan', '-', 'no data',
            'not applicable', 'not available'
        ]
        
        return alarm_str not in invalid_indicators
    
    for scenario in session['active_scenarios']:
        equipment = clean_text_encoding(scenario.get('Equipment', 'Unknown'))
        ats_alarm = scenario.get('ATS Alarm Description', '')
        fscada_alarm = scenario.get('FSCADA Alarm Description', '')
        hmi_alarm = scenario.get('HMI Alarm', '')
        
        # Clean and validate alarms
        ats_alarm_clean = clean_text_encoding(ats_alarm) if ats_alarm else ''
        fscada_alarm_clean = clean_text_encoding(fscada_alarm) if fscada_alarm else ''
        hmi_alarm_clean = clean_text_encoding(hmi_alarm) if hmi_alarm else ''
        
        # Only add to alarm list if valid
        if is_valid_alarm(ats_alarm_clean):
            all_alarms['ATS'].append(f"{equipment}: {ats_alarm_clean}")
            print(f"Valid ATS alarm found: {equipment}: {ats_alarm_clean}")
        else:
            print(f"Invalid ATS alarm skipped: {equipment}: '{ats_alarm}' -> '{ats_alarm_clean}'")
            
        if is_valid_alarm(fscada_alarm_clean):
            all_alarms['FSCADA'].append(f"{equipment}: {fscada_alarm_clean}")
            print(f"Valid FSCADA alarm found: {equipment}: {fscada_alarm_clean}")
        else:
            print(f"Invalid FSCADA alarm skipped: {equipment}: '{fscada_alarm}' -> '{fscada_alarm_clean}'")
            
        if is_valid_alarm(hmi_alarm_clean):
            all_alarms['HMI'].append(f"{equipment}: {hmi_alarm_clean}")
            print(f"Valid HMI alarm found: {equipment}: {hmi_alarm_clean}")
        else:
            print(f"Invalid HMI alarm skipped: {equipment}: '{hmi_alarm}' -> '{hmi_alarm_clean}'")
    
    # Debug: Print final alarm counts
    print(f"Final alarm counts - ATS: {len(all_alarms['ATS'])}, FSCADA: {len(all_alarms['FSCADA'])}, HMI: {len(all_alarms['HMI'])}")
    
    # Equipment that use numbered format (i, ii, iii)
    numbered_format_equipment = [
        'Trackside ATO', 
        'Wayside - Train Communication Channel', 
        'ATS', 
        'Switch Machine', 
        '750 VDC Switchgear'
    ]
    
    # Get guidelines from ALL selected scenarios
    guidelines_data = []
    for i, scenario in enumerate(session['active_scenarios']):
        equipment = clean_text_encoding(scenario.get('Equipment', 'N/A'))
        failure_scenario = clean_text_encoding(scenario.get('Failure Scenario', 'N/A'))
        guidelines = clean_text_encoding(scenario.get('Guidelines for the Chief Controller', 'N/A'))
        local_response = clean_text_encoding(scenario.get('Local Response', 'N/A'))
        classification = clean_text_encoding(scenario.get('Failure Classification', 'N/A'))
        
        # Check if this equipment uses numbered format
        use_numbered_format = equipment in numbered_format_equipment
        
        if use_numbered_format:
            # Parse numbered format (i., ii., iii.) - IMPROVED VERSION
            guideline_steps = []
            
            if guidelines != 'N/A' and guidelines.strip():
                # Split by numbered points and clean up
                parts = guidelines.replace('i.', '|i.|').replace('ii.', '|ii.|').replace('iii.', '|iii.|').split('|')
                
                for part in parts:
                    part = part.strip()
                    content = ""
                    step_num = ""
                    
                    if part.startswith('i.|'):
                        content = part.replace('i.|', '').strip()
                        step_num = 'i'
                    elif part.startswith('ii.|'):
                        content = part.replace('ii.|', '').strip()
                        step_num = 'ii'
                    elif part.startswith('iii.|'):
                        content = part.replace('iii.|', '').strip()
                        step_num = 'iii'
                    elif part and not any(part.startswith(x) for x in ['i.|', 'ii.|', 'iii.|']):
                        # Handle cases where numbering might be different or missing
                        content = part
                        if len(guideline_steps) == 0:
                            step_num = 'i'
                        elif len(guideline_steps) == 1:
                            step_num = 'ii'
                        elif len(guideline_steps) == 2:
                            step_num = 'iii'
                    
                    # IMPROVED: Only add if content is meaningful (not just "i." or empty)
                    if content and content.lower() not in ['i', 'ii', 'iii', 'i.', 'ii.', 'iii.', 'n/a', 'na', '-']:
                        guideline_steps.append((step_num, content))
            
            # IMPROVED: Only add default if no meaningful steps were found
            if not guideline_steps:
                # Try to use the original guidelines text if it has meaningful content
                if guidelines and guidelines.strip() and guidelines.lower() not in ['n/a', 'na', '-']:
                    guideline_steps = [('i', guidelines.strip())]
                else:
                    guideline_steps = [('i', 'Follow standard protocol')]
            
            guidelines_data.append({
                'equipment': equipment,
                'failure_scenario': failure_scenario,
                'classification': classification,
                'format_type': 'numbered',
                'guideline_steps': guideline_steps,
                'local_response': local_response
            })
        else:
            # Parse standard format (Train Entering Service, Train already in Service, Note)
            train_entering = ""
            train_in_service = ""
            note = ""
            
            if guidelines != 'N/A' and guidelines.strip():
                if 'Train Entering service:' in guidelines:
                    parts = guidelines.split('Train Entering service:')
                    if len(parts) > 1:
                        remaining = parts[1]
                        if 'Train already in service:' in remaining:
                            enter_parts = remaining.split('Train already in service:')
                            train_entering = enter_parts[0].strip()
                            if len(enter_parts) > 1:
                                if 'Note:' in enter_parts[1]:
                                    service_parts = enter_parts[1].split('Note:')
                                    train_in_service = service_parts[0].strip()
                                    if len(service_parts) > 1:
                                        note = service_parts[1].strip()
                                else:
                                    train_in_service = enter_parts[1].strip()
                else:
                    train_entering = guidelines.strip()
            
            guidelines_data.append({
                'equipment': equipment,
                'failure_scenario': failure_scenario,
                'classification': classification,
                'format_type': 'standard',
                'train_entering': train_entering if train_entering else guidelines,
                'train_in_service': train_in_service,
                'note': note if note else "N/A",
                'local_response': local_response
            })
    
    return render_template('guidelines.html', 
                         active_scenarios=session['active_scenarios'],
                         all_alarms=all_alarms,
                         guidelines_data=guidelines_data,
                         timer_start=session['timer_start'])

def clean_text_encoding(text):
    """Clean text from encoding issues"""
    if not text or pd.isna(text):
        return text
    
    # Convert to string and clean encoding issues
    text = str(text)
    text = text.replace('Ã¢â‚¬Â¢', '')  # Remove bullet encoding
    text = text.replace('Ã¢â‚¬"', '-')   # Replace em dash
    text = text.replace('Ã¢â‚¬â„¢', "'")  # Replace apostrophe
    text = text.replace('Ã¢â‚¬Å"', '"')   # Replace left quote
    text = text.replace('Ã¢â‚¬', '"')     # Replace right quote
    text = text.replace('Ã‚', '')        # Remove non-breaking space
    text = text.replace('â€¢', '')       # Remove bullet points
    text = text.replace('â€"', '-')      # Replace em dash
    text = text.replace('â€™', "'")      # Replace right single quote
    text = text.replace('â€œ', '"')      # Replace left double quote
    text = text.replace('â€', '"')       # Replace right double quote
    
    # Clean multiple spaces and trim
    text = ' '.join(text.split())
    return text.strip()

def save_resolution_data():
    """Save resolution data to CSV with updated status terminology"""
    if not session['active_scenarios']:
        return
    
    end_time = datetime.datetime.now()
    
    # Calculate elapsed time from timer start
    if session.get('timer_start'):
        elapsed_time = time.time() - session['timer_start']
        start_time = datetime.datetime.fromtimestamp(session['timer_start'])
    else:
        elapsed_time = 0
        start_time = end_time
    
    for scenario in session['active_scenarios']:
        # Updated status logic:
        # Non-Relevant Failure = solved within 5 minutes (≤ 300 seconds)
        # Relevant Failure = not solved within 5 minutes (> 300 seconds)
        status = "Non-Relevant Failure" if elapsed_time <= 300 else "Relevant Failure"
        
        # Clean all text fields from encoding issues
        equipment = clean_text_encoding(scenario.get('Equipment', 'N/A'))
        failure_scenario = clean_text_encoding(scenario.get('Failure Scenario', 'N/A'))
        guidelines = clean_text_encoding(scenario.get('Guidelines for the Chief Controller', 'N/A'))
        local_response = clean_text_encoding(scenario.get('Local Response', 'N/A'))
        
        resolution_data = {
            "Staff ID": session['staff_id'],
            "Start Time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Stop Time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Equipment": equipment,
            "Failure Scenario": failure_scenario,
            "Status": status,
            "Guideline for Chief Controller": guidelines,
            "Local Response": local_response,
            "Duration (min)": round(elapsed_time / 60, 1)
        }
        
        # Use new filename to avoid confusion with old data
        filename = "tgs_resolution_history_v2.csv"
        try:
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                # Clean existing data if any
                for col in ['Equipment', 'Failure Scenario', 'Guideline for Chief Controller', 'Local Response']:
                    if col in df.columns:
                        df[col] = df[col].apply(clean_text_encoding)
                df = pd.concat([df, pd.DataFrame([resolution_data])], ignore_index=True)
            else:
                df = pd.DataFrame([resolution_data])
            
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename} with status: {status}")
        except Exception as e:
            print(f"Error saving data: {str(e)}")

@app.route('/timer_data')
@login_required
def timer_data():
    """API endpoint to get current timer data"""
    if session.get('timer_start'):
        elapsed_seconds = time.time() - session['timer_start']
        minutes = int(elapsed_seconds // 60)
        seconds = int(elapsed_seconds % 60)
        
        if elapsed_seconds > 300:
            status = "CRITICAL"
            color = "#dc3545"
            icon = "🚨"
        elif elapsed_seconds > 180:
            status = "ALERT"
            color = "#fd7e14"
            icon = "⚠️"
        else:
            status = "NORMAL"
            color = "#003b70"
            icon = "⏱️"
        
        return jsonify({
            'elapsed_seconds': elapsed_seconds,
            'minutes': minutes,
            'seconds': seconds,
            'status': status,
            'color': color,
            'icon': icon,
            'display': f"{minutes:02d}:{seconds:02d}",
            'timer_running': True
        })
    
    return jsonify({
        'elapsed_seconds': 0, 
        'minutes': 0, 
        'seconds': 0, 
        'status': 'NORMAL', 
        'color': '#003b70', 
        'icon': '⏱️', 
        'display': '00:00',
        'timer_running': False
    })

@app.route('/download_history')
@login_required
def download_history():
    """Download user's resolution history with updated filename"""
    # Try new filename first, then fall back to old one
    filenames = ["tgs_resolution_history_v2.csv", "tgs_resolution_history.csv"]
    
    for filename in filenames:
        if os.path.exists(filename):
            try:
                df = pd.read_csv(filename)
                user_df = df[df['Staff ID'] == session['staff_id']]
                
                if not user_df.empty:
                    # Clean all text columns before download
                    text_columns = ['Equipment', 'Failure Scenario', 'Guideline for Chief Controller', 'Local Response']
                    for col in text_columns:
                        if col in user_df.columns:
                            user_df[col] = user_df[col].apply(clean_text_encoding)
                    
                    user_filename = f"TGS_History_{session['staff_id']}_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
                    user_df.to_csv(user_filename, index=False)
                    return send_file(user_filename, as_attachment=True)
                    
            except Exception as e:
                flash(f"Error loading history from {filename}: {str(e)}", "error")
                continue
    
    flash("No history found for your account", "info")
    return redirect(url_for('guidelines'))

def init_app():
    """Initialize app and migrate old data if needed"""
    migrate_old_data()
    
# Migration function to convert old data to new format (optional)
def migrate_old_data():
    """Convert old CSV data to new format with updated status"""
    old_filename = "tgs_resolution_history.csv"
    new_filename = "tgs_resolution_history_v2.csv"
    
    if os.path.exists(old_filename) and not os.path.exists(new_filename):
        try:
            df = pd.read_csv(old_filename)
            
            # Update status column
            if 'Status' in df.columns:
                df['Status'] = df['Status'].apply(lambda x: 
                    "Non-Relevant Failure" if x == "Resolved" else "Relevant Failure")
            
            # Clean text columns
            text_columns = ['Equipment', 'Failure Scenario', 'Guideline for Chief Controller', 'Local Response']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].apply(clean_text_encoding)
            
            df.to_csv(new_filename, index=False)
            print(f"Migrated data from {old_filename} to {new_filename}")
            return True
        except Exception as e:
            print(f"Error migrating data: {str(e)}")
            return False
    return False

if __name__ == '__main__':
    init_app()  # Initialize and migrate data if needed
    app.run(debug=True)