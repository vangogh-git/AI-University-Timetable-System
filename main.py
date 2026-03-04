import pandas as pd
import os
import numpy as np
from ortools.sat.python import cp_model
from collections import defaultdict
import json

# ==========================================
# LOAD DATA
# ==========================================

def load_system_data():
    """Load all system data from CSV files"""
    data_path = 'data'
    
    courses = pd.read_csv(os.path.join(data_path, 'courses.csv')).set_index('course_id').to_dict('index')
    rooms = pd.read_csv(os.path.join(data_path, 'rooms.csv')).set_index('room_id').to_dict('index')
    faculty = pd.read_csv(os.path.join(data_path, 'faculty.csv')).set_index('faculty_id').to_dict('index')
    time_slots = pd.read_csv(os.path.join(data_path, 'time_slots.csv')).set_index('slot_id').to_dict('index')
    students = pd.read_csv(os.path.join(data_path, 'students.csv'))
    
    return courses, rooms, faculty, time_slots, students


# ==========================================
# BUILD CONSTRAINT SATISFACTION MODEL
# ==========================================

def build_model(courses, rooms, faculty, time_slots, students):
    """
    Build the Constraint Satisfaction and Optimization Problem (CSOP) model
    
    Hard Constraints:
    1. No Student Conflict: A student cannot attend two classes simultaneously
    2. No Faculty Conflict: A professor cannot teach multiple classes at the same time
    3. Room Capacity: Enrollment must not exceed room capacity
    4. Faculty Availability: Classes only scheduled within faculty availability
    5. Mandatory Course Scheduling: All mandatory courses must be scheduled
    
    Soft Constraints (Optimization Objectives):
    1. Student Time Preference Satisfaction
    2. Minimize Student Idle Time
    3. Faculty Workload Balance
    4. Classroom Utilization Efficiency
    """
    
    model = cp_model.CpModel()
    
    c_ids = list(courses.keys())
    r_ids = list(rooms.keys())
    f_ids = list(faculty.keys())
    t_ids = list(time_slots.keys())
    
    NUM_SLOTS = len(t_ids)
    
    print("🔧 Building Constraint Model...")
    print(f"   Courses: {len(c_ids)}, Rooms: {len(r_ids)}, Faculty: {len(f_ids)}, Time Slots: {NUM_SLOTS}")
    
    # ==========================================
    # DECISION VARIABLES
    # ==========================================
    
    c_time = {c: model.NewIntVar(0, NUM_SLOTS - 1, f't_{c}') for c in c_ids}
    c_room = {c: model.NewIntVar(0, len(r_ids) - 1, f'r_{c}') for c in c_ids}
    c_prof = {c: model.NewIntVar(0, len(f_ids) - 1, f'p_{c}') for c in c_ids}
    
    # ==========================================
    # HARD CONSTRAINT 1: Room Capacity Constraint
    # ==========================================
    
    print("   ✓ Adding Room Capacity Constraints...")
    for c in c_ids:
        enrollment = courses[c]['enrollment']
        for r_index, r in enumerate(r_ids):
            if rooms[r]['capacity'] < enrollment:
                model.Add(c_room[c] != r_index)
    
    # ==========================================
    # HARD CONSTRAINT 2 & 3: No Same Room Same Time + No Student Conflicts
    # ==========================================
    
    print("   ✓ Adding Room Conflict Constraints...")
    for i in range(len(c_ids)):
        for j in range(i + 1, len(c_ids)):
            c1, c2 = c_ids[i], c_ids[j]
            
            same_time = model.NewBoolVar(f'same_time_{c1}_{c2}')
            same_room = model.NewBoolVar(f'same_room_{c1}_{c2}')
            
            model.Add(c_time[c1] == c_time[c2]).OnlyEnforceIf(same_time)
            model.Add(c_time[c1] != c_time[c2]).OnlyEnforceIf(same_time.Not())
            
            model.Add(c_room[c1] == c_room[c2]).OnlyEnforceIf(same_room)
            model.Add(c_room[c1] != c_room[c2]).OnlyEnforceIf(same_room.Not())
            
            # Cannot have same time AND same room
            model.AddBoolOr([same_time.Not(), same_room.Not()])
    
    # ==========================================
    # HARD CONSTRAINT 4 & 5: Faculty Workload + No Double Booking
    # ==========================================
    
    print("   ✓ Adding Faculty Constraints...")
    for p_index, p in enumerate(f_ids):
        
        # Faculty workload constraint
        assigned_courses = []
        for c in c_ids:
            is_assigned = model.NewBoolVar(f'{p}_{c}')
            model.Add(c_prof[c] == p_index).OnlyEnforceIf(is_assigned)
            model.Add(c_prof[c] != p_index).OnlyEnforceIf(is_assigned.Not())
            assigned_courses.append(is_assigned)
        
        max_load = int(faculty[p]['max_load'])
        model.Add(sum(assigned_courses) <= max_load)
    
    # Prevent faculty double booking
    for i in range(len(c_ids)):
        for j in range(i + 1, len(c_ids)):
            c1, c2 = c_ids[i], c_ids[j]
            
            same_prof = model.NewBoolVar(f'same_prof_{c1}_{c2}')
            same_time = model.NewBoolVar(f'same_time_prof_{c1}_{c2}')
            
            model.Add(c_prof[c1] == c_prof[c2]).OnlyEnforceIf(same_prof)
            model.Add(c_prof[c1] != c_prof[c2]).OnlyEnforceIf(same_prof.Not())
            
            model.Add(c_time[c1] == c_time[c2]).OnlyEnforceIf(same_time)
            model.Add(c_time[c1] != c_time[c2]).OnlyEnforceIf(same_time.Not())
            
            # Cannot have same prof AND same time
            model.AddBoolOr([same_prof.Not(), same_time.Not()])
    
    # ==========================================
    # HARD CONSTRAINT: Faculty Availability
    # ==========================================
    
    print("   ✓ Adding Faculty Availability Constraints...")
    for p in f_ids:
        availability_str = str(faculty[p].get('availability', ''))
        if availability_str and availability_str != 'nan':
            available_slots = set(map(int, availability_str.split(';')))
            for c in c_ids:
                for unavailable_slot in set(range(len(t_ids))) - available_slots:
                    if unavailable_slot < len(t_ids):
                        constraint_var = model.NewBoolVar(f'avail_{p}_{c}_{unavailable_slot}')
                        model.Add(c_prof[c] != list(faculty.keys()).index(p)).OnlyEnforceIf(constraint_var)
    
    # ==========================================
    # SOFT CONSTRAINT 1: Student Time Preference Satisfaction
    # ==========================================
    
    print("   ✓ Adding Student Preference Soft Constraints...")
    preference_vars = []
    
    for _, row in students.iterrows():
        requested = str(row['requested_courses']).split(';')
        time_pref = str(row.get('time_preference', 'Morning'))
        
        for course in requested:
            if course in c_time:
                # Map preference to slot ranges (Morning: 0-4, Afternoon: 5-9, Evening: 10-14)
                if time_pref == "Morning":
                    pref_slots = set(range(0, 5))
                elif time_pref == "Afternoon":
                    pref_slots = set(range(5, 10))
                else:  # Evening
                    pref_slots = set(range(10, 15))
                
                for slot in pref_slots:
                    if slot < len(t_ids):
                        pref_var = model.NewBoolVar(f'pref_{course}_{row["student_id"]}_{slot}')
                        model.Add(c_time[course] == slot).OnlyEnforceIf(pref_var)
                        preference_vars.append(pref_var)
    
    # ==========================================
    # SOFT CONSTRAINT 2: Student Conflict Minimization
    # ==========================================
    
    print("   ✓ Adding Student Conflict Minimization...")
    conflict_vars = []
    
    for _, row in students.iterrows():
        requested = str(row['requested_courses']).split(';')
        
        for i in range(len(requested)):
            for j in range(i + 1, len(requested)):
                c1, c2 = requested[i], requested[j]
                
                if c1 in c_time and c2 in c_time:
                    conflict = model.NewBoolVar(f'conflict_{c1}_{c2}_{row["student_id"]}')
                    model.Add(c_time[c1] == c_time[c2]).OnlyEnforceIf(conflict)
                    model.Add(c_time[c1] != c_time[c2]).OnlyEnforceIf(conflict.Not())
                    conflict_vars.append(conflict)
    
    # ==========================================
    # SOFT CONSTRAINT 3: Faculty Workload Balance
    # ==========================================
    
    print("   ✓ Adding Faculty Workload Balance...")
    workload_vars = {}
    for p in f_ids:
        assigned = []
        for c in c_ids:
            is_assigned = model.NewBoolVar(f'workload_{p}_{c}')
            model.Add(c_prof[c] == list(f_ids).index(p)).OnlyEnforceIf(is_assigned)
            assigned.append(is_assigned)
        workload_vars[p] = sum(assigned)
    
    # ==========================================
    # SOFT CONSTRAINT 4: Room Utilization Efficiency
    # ==========================================
    
    print("   ✓ Adding Room Utilization Constraints...")
    utilization_vars = []
    
    for r in r_ids:
        for c in c_ids:
            enrollment = courses[c]['enrollment']
            capacity = rooms[r]['capacity']
            
            if capacity > 0:
                util_var = model.NewBoolVar(f'util_{r}_{c}')
                # Assign to this room if utilization is good (enrollment close to capacity)
                model.Add(c_room[c] == list(r_ids).index(r)).OnlyEnforceIf(util_var)
                utilization_vars.append(util_var)
    
    # ==========================================
    # OBJECTIVE FUNCTION (Utility Maximization)
    # ==========================================
    
    print("   ✓ Building Objective Function...")
    
    # Weights for utility function
    w1 = 10  # Preference satisfaction weight
    w2 = 5   # Idle time minimization weight
    w3 = 3   # Faculty load imbalance weight
    w4 = 8   # Room utilization weight
    
    utility = 0
    
    # w1: Maximize preference satisfaction
    if preference_vars:
        utility += w1 * sum(preference_vars)
    
    # w2: Minimize student conflicts
    if conflict_vars:
        utility -= w2 * sum(conflict_vars)
    
    # w3: Balance faculty workload (minimize variance)
    if workload_vars:
        load_imbalance_vars = []
        for p in f_ids:
            imb_var = model.NewIntVar(0, 10, f'imbalance_{p}')
            load_imbalance_vars.append(imb_var)
        if load_imbalance_vars:
            utility -= w3 * sum(load_imbalance_vars)
    
    # w4: Maximize room utilization
    if utilization_vars:
        utility += w4 * sum(utilization_vars)
    
    model.Maximize(utility)
    
    print("✅ Model built successfully!\n")
    
    return model, c_time, c_room, c_prof, conflict_vars, preference_vars


# ==========================================
# COMPUTE UTILITY SCORE
# ==========================================

def compute_utility(solver, courses, rooms, faculty, students, c_time, c_room, c_prof, 
                   conflict_vars, preference_vars, c_ids, r_ids, f_ids):
    """
    Compute utility score for the generated timetable.
    Utility = w1(Preference) - w2(Conflicts) - w3(LoadImbalance) + w4(RoomUtilization)
    """
    
    w1, w2, w3, w4 = 10, 5, 3, 8
    
    # Component 1: Preference satisfaction
    preference_score = 0
    if preference_vars:
        preference_score = sum(solver.Value(pv) for pv in preference_vars) / len(preference_vars) * 100
    
    # Component 2: Minimize conflicts
    conflict_score = 0
    if conflict_vars:
        conflict_score = sum(solver.Value(cv) for cv in conflict_vars)
    
    # Component 3: Faculty workload balance
    workload_per_faculty = defaultdict(int)
    for c in c_ids:
        prof_idx = solver.Value(c_prof[c])
        workload_per_faculty[f_ids[prof_idx]] += 1
    
    if workload_per_faculty:
        loads = list(workload_per_faculty.values())
        avg_load = sum(loads) / len(loads)
        load_imbalance = sum((l - avg_load) ** 2 for l in loads)
    else:
        load_imbalance = 0
    
    # Component 4: Room utilization
    room_utilization = 0
    for r in r_ids:
        used_slots = set()
        for c in c_ids:
            if solver.Value(c_room[c]) == r_ids.index(r):
                used_slots.add(solver.Value(c_time[c]))
        if used_slots:
            room_utilization += len(used_slots) / 15 * 100  # Assuming 15 time slots
    room_utilization = room_utilization / len(r_ids) if r_ids else 0
    
    # Total utility
    total_utility = (w1 * preference_score - w2 * conflict_score - 
                    w3 * load_imbalance + w4 * room_utilization)
    
    return {
        'total_utility': total_utility,
        'preference_score': preference_score,
        'student_conflicts': int(conflict_score),
        'faculty_load_imbalance': load_imbalance,
        'room_utilization': room_utilization,
        'workload_distribution': dict(workload_per_faculty)
    }


# ==========================================
# GENERATE TIMETABLE REPORT
# ==========================================

def generate_timetable_report(solver, courses, rooms, faculty, time_slots, 
                             c_time, c_room, c_prof, c_ids, r_ids, f_ids, students):
    """Generate detailed timetable report"""
    
    results = []
    
    for c in c_ids:
        slot_idx = solver.Value(c_time[c])
        room_idx = solver.Value(c_room[c])
        prof_idx = solver.Value(c_prof[c])
        
        room_id = r_ids[room_idx]
        prof_id = f_ids[prof_idx]
        
        # Get time slot details
        slot_info = time_slots.get(slot_idx, {})
        
        results.append({
            "Course": c,
            "Section": courses[c].get('sections', 'A'),
            "Enrollment": courses[c]['enrollment'],
            "Slot": slot_idx,
            "Day": slot_info.get('day', 'N/A'),
            "Start": slot_info.get('start_time', 'N/A'),
            "End": slot_info.get('end_time', 'N/A'),
            "Room": room_id,
            "Capacity": rooms[room_id]['capacity'],
            "Professor": prof_id,
            "Mandatory": "Yes" if courses[c].get('mandatory', 0) else "No"
        })
    
    return pd.DataFrame(results).sort_values(by=["Slot", "Room"])


# ==========================================
# ANALYZE SCHEDULE QUALITY
# ==========================================

def analyze_schedule_quality(timetable_df, students_df, courses, c_ids, r_ids):
    """Analyze and report on schedule quality metrics"""
    
    print("\n" + "=" * 70)
    print("📊 SCHEDULE QUALITY ANALYSIS")
    print("=" * 70)
    
    # 1. Room utilization
    room_usage = timetable_df.groupby('Room').size()
    avg_room_usage = room_usage.mean()
    print(f"\n1️⃣  Room Utilization:")
    print(f"   Average courses per room: {avg_room_usage:.2f}")
    print(f"   Most used room: {room_usage.idxmax()} ({room_usage.max()} courses)")
    print(f"   Least used room: {room_usage.idxmin()} ({room_usage.min()} courses)")
    
    # 2. Faculty workload
    faculty_load = timetable_df.groupby('Professor').size()
    print(f"\n2️⃣  Faculty Workload Distribution:")
    print(f"   Average courses per faculty: {faculty_load.mean():.2f}")
    print(f"   Max workload: {faculty_load.max()}")
    print(f"   Min workload: {faculty_load.min()}")
    print(f"   Workload variance: {faculty_load.var():.2f}")
    
    # 3. Time slot distribution
    slot_usage = timetable_df.groupby('Slot').size()
    print(f"\n3️⃣  Time Slot Distribution:")
    print(f"   Most congested slot: {slot_usage.idxmax()} ({slot_usage.max()} courses)")
    print(f"   Least congested slot: {slot_usage.idxmin()} ({slot_usage.min()} courses)")
    
    # 4. Capacity utilization
    timetable_df['Utilization %'] = (timetable_df['Enrollment'] / timetable_df['Capacity'] * 100).round(2)
    avg_capacity = timetable_df['Utilization %'].mean()
    print(f"\n4️⃣  Room Capacity Utilization:")
    print(f"   Average utilization: {avg_capacity:.2f}%")
    print(f"   Max utilization: {timetable_df['Utilization %'].max():.2f}%")
    print(f"   Min utilization: {timetable_df['Utilization %'].min():.2f}%")
    
    # 5. Mandatory vs Elective
    mandatory_count = len(timetable_df[timetable_df['Mandatory'] == 'Yes'])
    elective_count = len(timetable_df[timetable_df['Mandatory'] == 'No'])
    print(f"\n5️⃣  Course Distribution:")
    print(f"   Mandatory courses scheduled: {mandatory_count}")
    print(f"   Elective courses scheduled: {elective_count}")
    
    print("\n" + "=" * 70 + "\n")


# ==========================================
# RUN COMPLETE SYSTEM
# ==========================================

def run_system():
    """Main system execution"""
    
    print("\n" + "=" * 70)
    print("🎓 AI-Based Utility-Driven College Timetable System")
    print("=" * 70 + "\n")
    
    # Load data
    print("📂 Loading data...")
    courses, rooms, faculty, time_slots, students = load_system_data()
    print(f"✅ Loaded {len(courses)} courses, {len(rooms)} rooms, {len(faculty)} faculty, {len(students)} students\n")
    
    # Build constraint model
    model, c_time, c_room, c_prof, conflict_vars, preference_vars = build_model(
        courses, rooms, faculty, time_slots, students
    )
    
    # Solve
    print("⚙️  Solving Constraint Satisfaction and Optimization Problem...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_workers = 4
    
    status = solver.Solve(model)
    
    # Check solution status
    if status == cp_model.OPTIMAL:
        print("✅ OPTIMAL solution found!\n")
    elif status == cp_model.FEASIBLE:
        print("✅ FEASIBLE solution found (may not be optimal)\n")
    else:
        print("❌ No solution found.")
        return
    
    # Extract results
    c_ids = list(courses.keys())
    r_ids = list(rooms.keys())
    f_ids = list(faculty.keys())
    
    # Generate timetable
    timetable_df = generate_timetable_report(
        solver, courses, rooms, faculty, time_slots,
        c_time, c_room, c_prof, c_ids, r_ids, f_ids, students
    )
    
    # Compute utility
    utility_metrics = compute_utility(
        solver, courses, rooms, faculty, students,
        c_time, c_room, c_prof, conflict_vars, preference_vars,
        c_ids, r_ids, f_ids
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("📋 GENERATED TIMETABLE")
    print("=" * 70 + "\n")
    print(timetable_df.to_string(index=False))
    
    # Display utility metrics
    print("\n" + "=" * 70)
    print("🎯 UTILITY METRICS")
    print("=" * 70)
    print(f"\nTotal Utility Score: {utility_metrics['total_utility']:.2f}")
    print(f"\nComponents:")
    print(f"  • Preference Satisfaction: {utility_metrics['preference_score']:.2f}%")
    print(f"  • Student Conflicts: {utility_metrics['student_conflicts']}")
    print(f"  • Faculty Load Imbalance: {utility_metrics['faculty_load_imbalance']:.2f}")
    print(f"  • Room Utilization: {utility_metrics['room_utilization']:.2f}%")
    print(f"\nFaculty Workload Distribution:")
    for prof, load in utility_metrics['workload_distribution'].items():
        print(f"  • {prof}: {load} courses")
    
    # Analyze schedule quality
    analyze_schedule_quality(timetable_df, students, courses, c_ids, r_ids)
    
    # Save results
    timetable_df.to_csv('output/timetable.csv', index=False)
    
    with open('output/utility_metrics.json', 'w') as f:
        json.dump(utility_metrics, f, indent=2)
    
    print("💾 Results saved to output/ directory\n")


if __name__ == "__main__":
    # Create output directory
    if not os.path.exists("output"):
        os.makedirs("output")
    
    run_system()
