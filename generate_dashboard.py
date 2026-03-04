import pandas as pd
import json
import os

def generate_html_dashboard(timetable_csv, utility_json):
    """
    Generate an interactive HTML dashboard from timetable and metrics data
    
    Args:
        timetable_csv: Path to timetable.csv
        utility_json: Path to utility_metrics.json
    """
    
    # Load data
    timetable_df = pd.read_csv(timetable_csv)
    
    with open(utility_json, 'r', encoding='utf-8') as f:
        metrics = json.load(f)
    
    # Prepare timetable data for JavaScript
    timetable_data = []
    for idx, row in timetable_df.iterrows():
        timetable_data.append({
            'course': row['Course'],
            'day': row['Day'],
            'slot': int(row['Slot']),
            'room': row['Room'],
            'professor': row['Professor'],
            'time': f"{row['Start']}-{row['End']}",
            'capacity': int(row['Capacity']),
            'enrollment': int(row['Enrollment'])
        })
    
    # Get unique professors
    professors = sorted(timetable_df['Professor'].unique().tolist())
    rooms = sorted(timetable_df['Room'].unique().tolist())
    
    # Prepare room capacities
    room_capacities = {}
    for idx, row in timetable_df.iterrows():
        room_capacities[row['Room']] = int(row['Capacity'])
    
    # Generate HTML
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Timetable Management System</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --primary: #028090;
            --secondary: #00A896;
            --accent: #02C39A;
            --dark: #1B3A3A;
            --light: #F0F8F8;
            --white: #FFFFFF;
            --text: #2C3E50;
            --border: #D5E8E8;
            --hover: #E8F5F5;
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--light) 0%, #E8F5F5 100%);
            color: var(--text);
        }}

        /* Header */
        .header {{
            background: var(--primary);
            color: var(--white);
            padding: 2rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(2, 128, 144, 0.15);
        }}

        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }}

        .header p {{
            font-size: 1.1rem;
            opacity: 0.95;
            color: var(--secondary);
        }}

        /* Main Container */
        .container {{
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}

        /* Metrics Dashboard */
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            background: var(--white);
            border-radius: 12px;
            padding: 1.5rem;
            border-left: 4px solid var(--primary);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(2, 128, 144, 0.12);
        }}

        .metric-card.success {{
            border-left-color: var(--success);
        }}

        .metric-label {{
            font-size: 0.9rem;
            color: var(--text);
            opacity: 0.7;
            margin-bottom: 0.5rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.3rem;
        }}

        .metric-card.success .metric-value {{
            color: var(--success);
        }}

        .metric-subtext {{
            font-size: 0.85rem;
            color: var(--text);
            opacity: 0.6;
        }}

        /* Controls */
        .controls {{
            background: var(--white);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }}

        .control-group {{
            display: flex;
            gap: 0.8rem;
            align-items: center;
        }}

        .control-group label {{
            font-weight: 600;
            color: var(--text);
            font-size: 0.95rem;
        }}

        select {{
            padding: 0.7rem 1rem;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.95rem;
            font-family: inherit;
        }}

        select:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(2, 128, 144, 0.1);
        }}

        .btn {{
            padding: 0.7rem 1.5rem;
            background: var(--primary);
            color: var(--white);
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.95rem;
        }}

        .btn:hover {{
            background: var(--secondary);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(2, 128, 144, 0.2);
        }}

        /* Timetable */
        .timetable-section {{
            background: var(--white);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            overflow-x: auto;
            margin-bottom: 2rem;
        }}

        .timetable-section h2 {{
            margin-bottom: 1.5rem;
            color: var(--primary);
            font-size: 1.5rem;
            border-bottom: 2px solid var(--border);
            padding-bottom: 1rem;
        }}

        .timetable {{
            display: grid;
            grid-template-columns: 150px repeat(5, 1fr);
            gap: 1px;
            background: var(--border);
            border-radius: 8px;
            overflow: hidden;
            min-width: 100%;
        }}

        .timetable-header {{
            background: var(--primary);
            color: var(--white);
            padding: 1rem;
            font-weight: 600;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .timetable-slot {{
            background: var(--white);
            padding: 1rem;
            text-align: center;
            font-size: 0.9rem;
            color: var(--text);
            font-weight: 600;
        }}

        .timetable-slot.time-header {{
            background: var(--light);
            color: var(--primary);
            font-weight: 700;
        }}

        .course-cell {{
            background: linear-gradient(135deg, var(--light) 0%, var(--hover) 100%);
            border: 1px solid var(--secondary);
            border-radius: 6px;
            padding: 0.8rem;
            min-height: 80px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .course-cell::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--secondary);
        }}

        .course-cell:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(0, 168, 150, 0.2);
        }}

        .course-code {{
            font-weight: 700;
            color: var(--primary);
            font-size: 0.95rem;
            margin-bottom: 0.3rem;
        }}

        .course-room {{
            font-size: 0.8rem;
            color: var(--text);
            opacity: 0.7;
            margin-bottom: 0.2rem;
        }}

        .course-prof {{
            font-size: 0.75rem;
            color: var(--secondary);
            font-weight: 600;
        }}

        .empty-slot {{
            background: var(--hover);
            color: var(--text);
            opacity: 0.4;
        }}

        /* Distribution */
        .distribution-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}

        .distribution-card {{
            background: var(--white);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }}

        .distribution-card h3 {{
            color: var(--primary);
            margin-bottom: 1.5rem;
            font-size: 1.2rem;
        }}

        .faculty-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.8rem 0;
            border-bottom: 1px solid var(--border);
        }}

        .faculty-item:last-child {{
            border-bottom: none;
        }}

        .faculty-name {{
            font-weight: 600;
            color: var(--text);
        }}

        .faculty-load {{
            background: var(--light);
            padding: 0.4rem 0.8rem;
            border-radius: 4px;
            font-weight: 600;
            color: var(--primary);
            font-size: 0.9rem;
        }}

        .progress-bar {{
            width: 100%;
            height: 6px;
            background: var(--border);
            border-radius: 3px;
            margin-top: 0.5rem;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--secondary), var(--accent));
            border-radius: 3px;
        }}

        .room-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1.5rem;
        }}

        .room-card {{
            background: linear-gradient(135deg, var(--light) 0%, var(--hover) 100%);
            border: 2px solid var(--secondary);
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
        }}

        .room-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 168, 150, 0.15);
            border-color: var(--accent);
        }}

        .room-name {{
            font-weight: 700;
            color: var(--primary);
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
        }}

        .room-info {{
            font-size: 0.85rem;
            color: var(--text);
            opacity: 0.7;
            margin-bottom: 1rem;
        }}

        .room-capacity {{
            background: var(--primary);
            color: var(--white);
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}

        .room-utilization {{
            font-size: 0.9rem;
            color: var(--secondary);
            font-weight: 600;
        }}

        .footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text);
            opacity: 0.7;
            margin-top: 3rem;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8rem;
            }}
            .timetable {{
                grid-template-columns: 100px repeat(5, 1fr);
            }}
        }}

        @media print {{
            body {{
                background: var(--white);
            }}
            .controls {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <h1>[AI] TIMETABLE MANAGEMENT SYSTEM</h1>
        <p>Constraint Satisfaction & Optimization Dashboard</p>
    </div>

    <!-- Main Container -->
    <div class="container">
        <!-- Metrics -->
        <div class="metrics" id="metricsContainer">
            <div class="metric-card success">
                <div class="metric-label">Total Utility Score</div>
                <div class="metric-value">{metrics['total_utility']:.1f}</div>
                <div class="metric-subtext">Multi-objective optimization</div>
            </div>
            <div class="metric-card success">
                <div class="metric-label">Preference Satisfaction</div>
                <div class="metric-value">{metrics['preference_score']:.1f}%</div>
                <div class="metric-subtext">Students in preferred times</div>
            </div>
            <div class="metric-card success">
                <div class="metric-label">Student Conflicts</div>
                <div class="metric-value">{metrics['student_conflicts']}</div>
                <div class="metric-subtext">Scheduling overlaps detected</div>
            </div>
            <div class="metric-card success">
                <div class="metric-label">Room Utilization</div>
                <div class="metric-value">{metrics['room_utilization']:.1f}%</div>
                <div class="metric-subtext">Capacity efficiency</div>
            </div>
        </div>

        <!-- Controls -->
        <div class="controls">
            <div class="control-group">
                <label for="dayFilter">Filter by Day:</label>
                <select id="dayFilter">
                    <option value="">All Days</option>
                    <option value="Mon">Monday</option>
                    <option value="Tue">Tuesday</option>
                    <option value="Wed">Wednesday</option>
                    <option value="Thu">Thursday</option>
                    <option value="Fri">Friday</option>
                </select>
            </div>
            <div class="control-group">
                <label for="professorFilter">Filter by Professor:</label>
                <select id="professorFilter">
                    <option value="">All Professors</option>
                    {"".join([f'<option value="{prof}">{prof}</option>' for prof in professors])}
                </select>
            </div>
            <button class="btn" onclick="downloadCSV()">Download CSV</button>
            <button class="btn" onclick="window.print()" style="background: #00A896;">Print</button>
        </div>

        <!-- Timetable -->
        <div class="timetable-section">
            <h2>WEEKLY SCHEDULE GRID</h2>
            <div class="timetable" id="timetableGrid"></div>
        </div>

        <!-- Distribution -->
        <div class="distribution-section">
            <div class="distribution-card">
                <h3>FACULTY WORKLOAD DISTRIBUTION</h3>
                <div id="facultyWorkload"></div>
            </div>
            <div class="distribution-card">
                <h3>ROOM CAPACITY USAGE</h3>
                <div class="room-grid" id="roomGrid"></div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="footer">
        <p>Generated by AI-Based Constraint Satisfaction System</p>
        <p style="font-size: 0.9rem; margin-top: 0.5rem;">Classical AI: Constraint Programming + Multi-Objective Optimization</p>
    </div>

    <script>
        const timetableData = {json.dumps(timetable_data)};
        const roomCapacities = {json.dumps(room_capacities)};
        const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
        const times = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '13:00-14:00', '14:00-15:00'];

        function initDashboard() {{
            generateTimetableGrid();
            generateFacultyWorkload();
            generateRoomUtilization();
            setupFilters();
        }}

        function generateTimetableGrid() {{
            const grid = document.getElementById('timetableGrid');
            grid.innerHTML = '';

            grid.appendChild(createHeaderCell('Time Slot'));
            days.forEach(day => grid.appendChild(createHeaderCell(day)));

            times.forEach((time, idx) => {{
                grid.appendChild(createHeaderCell(time.split('-')[0], 'time-header'));
                days.forEach(day => {{
                    const course = timetableData.find(t => t.day === day && t.slot === idx);
                    if (course) {{
                        const cell = document.createElement('div');
                        cell.className = 'course-cell';
                        cell.innerHTML = `
                            <div class="course-code">${{course.course}}</div>
                            <div class="course-room">Room: ${{course.room}}</div>
                            <div class="course-prof">Prof: ${{course.professor}}</div>
                        `;
                        cell.title = `${{course.course}} | ${{course.room}} | ${{course.professor}}\\nEnrollment: ${{course.enrollment}}/${{course.capacity}}`;
                        grid.appendChild(cell);
                    }} else {{
                        const emptyCell = document.createElement('div');
                        emptyCell.className = 'timetable-slot empty-slot';
                        emptyCell.textContent = '-';
                        grid.appendChild(emptyCell);
                    }}
                }});
            }});
        }}

        function createHeaderCell(text, className = '') {{
            const cell = document.createElement('div');
            cell.className = `timetable-header ${{className}}`;
            cell.textContent = text;
            return cell;
        }}

        function generateFacultyWorkload() {{
            const container = document.getElementById('facultyWorkload');
            container.innerHTML = '';

            const loads = {{}};
            timetableData.forEach(t => {{
                loads[t.professor] = (loads[t.professor] || 0) + 1;
            }});

            const maxLoad = Math.max(...Object.values(loads));
            Object.entries(loads).forEach(([prof, load]) => {{
                const item = document.createElement('div');
                item.className = 'faculty-item';
                item.innerHTML = `
                    <span class="faculty-name">${{prof}}</span>
                    <span class="faculty-load">${{load}} courses</span>
                `;
                const progressBar = document.createElement('div');
                progressBar.className = 'progress-bar';
                progressBar.innerHTML = `<div class="progress-fill" style="width: ${{(load / maxLoad) * 100}}%"></div>`;
                item.appendChild(progressBar);
                container.appendChild(item);
            }});
        }}

        function generateRoomUtilization() {{
            const container = document.getElementById('roomGrid');
            container.innerHTML = '';

            const rooms = Object.keys(roomCapacities);
            rooms.forEach(room => {{
                const usage = timetableData.filter(t => t.room === room).length;
                const capacity = roomCapacities[room];

                const card = document.createElement('div');
                card.className = 'room-card';
                card.innerHTML = `
                    <div class="room-name">${{room}}</div>
                    <div class="room-info">Capacity: ${{capacity}}</div>
                    <div class="room-capacity">Courses: ${{usage}}/5</div>
                    <div class="room-utilization">${{Math.round((usage/5)*100)}}% utilized</div>
                `;
                container.appendChild(card);
            }});
        }}

        function setupFilters() {{
            document.getElementById('dayFilter').addEventListener('change', filterTimetable);
            document.getElementById('professorFilter').addEventListener('change', filterTimetable);
        }}

        function filterTimetable() {{
            const dayFilter = document.getElementById('dayFilter').value;
            const professorFilter = document.getElementById('professorFilter').value;

            document.querySelectorAll('.course-cell').forEach(cell => {{
                let match = true;
                const courseCode = cell.querySelector('.course-code').textContent;
                const professor = cell.querySelector('.course-prof').textContent.replace('Prof: ', '');
                const courseData = timetableData.find(t => t.course === courseCode);

                if (dayFilter && courseData.day !== dayFilter) match = false;
                if (professorFilter && professor !== professorFilter) match = false;

                cell.style.opacity = match ? '1' : '0.2';
                cell.style.pointerEvents = match ? 'auto' : 'none';
            }});
        }}

        function downloadCSV() {{
            let csv = 'Course,Day,Time,Room,Professor,Capacity,Enrollment\\n';
            timetableData.forEach(item => {{
                csv += `${{item.course}},${{item.day}},${{item.time}},${{item.room}},${{item.professor}},${{item.capacity}},${{item.enrollment}}\\n`;
            }});

            const blob = new Blob([csv], {{ type: 'text/csv' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'timetable.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        }}

        window.addEventListener('load', initDashboard);
    </script>
</body>
</html>
"""
    
    return html_template


if __name__ == "__main__":
    # Check if files exist
    if os.path.exists('output/timetable.csv') and os.path.exists('output/utility_metrics.json'):
        html_content = generate_html_dashboard('output/timetable.csv', 'output/utility_metrics.json')
        
        with open('output/timetable_dashboard.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("SUCCESS: Dashboard generated: output/timetable_dashboard.html")
        print("Open in browser to view interactive timetable!")
    else:
        print("ERROR: Run main.py first to generate timetable data")
        print("Expected files: output/timetable.csv and output/utility_metrics.json")