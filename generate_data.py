import pandas as pd
import os
import random
from datetime import datetime, timedelta

NUM_FACULTY = 8
NUM_ROOMS = 10
NUM_COURSES = 20
NUM_STUDENTS = 200
COURSES_PER_STUDENT = 4
ROOM_MIN_CAPACITY = 40
ROOM_MAX_CAPACITY = 80
COURSE_MIN_ENROLLMENT = 30
COURSE_MAX_ENROLLMENT = 60
MAX_FACULTY_LOAD = 4
NUM_TIME_SLOTS = 15



if not os.path.exists("data"):
    os.makedirs("data")

faculty_data = {
    "faculty_id": [f"Prof{i}" for i in range(1, NUM_FACULTY + 1)],
    "max_load": [MAX_FACULTY_LOAD] * NUM_FACULTY,
    "availability": [
        ";".join([str(j) for j in random.sample(range(NUM_TIME_SLOTS), 
                                                 random.randint(8, NUM_TIME_SLOTS))])
        for _ in range(NUM_FACULTY)
    ]
}

faculty_df = pd.DataFrame(faculty_data)
faculty_df.to_csv("data/faculty.csv", index=False)

print("✅ Faculty generated:")
print(faculty_df)
print()



room_features = ["Projector", "AC", "Lab", "SmartBoard", "WiFi"]

rooms_data = {
    "room_id": [f"R{i}" for i in range(1, NUM_ROOMS + 1)],
    "capacity": [random.randint(ROOM_MIN_CAPACITY, ROOM_MAX_CAPACITY)
                 for _ in range(NUM_ROOMS)],
    "features": [
        ";".join(random.sample(room_features, random.randint(2, 4)))
        for _ in range(NUM_ROOMS)
    ]
}

rooms_df = pd.DataFrame(rooms_data)
rooms_df.to_csv("data/rooms.csv", index=False)

print("✅ Rooms generated:")
print(rooms_df)
print()



course_ids = [f"C{i:03}" for i in range(1, NUM_COURSES + 1)]
mandatory_courses = random.sample(course_ids, max(1, NUM_COURSES // 3))

courses_data = {
    "course_id": course_ids,
    "sections": [f"{cid}-A" for cid in course_ids],
    "enrollment": [random.randint(COURSE_MIN_ENROLLMENT, COURSE_MAX_ENROLLMENT)
                   for _ in range(NUM_COURSES)],
    "mandatory": [1 if cid in mandatory_courses else 0 for cid in course_ids],
    "prerequisites": [
        ";".join(random.sample(course_ids, random.randint(0, 2)))
        for _ in range(NUM_COURSES)
    ]
}

courses_df = pd.DataFrame(courses_data)
courses_df.to_csv("data/courses.csv", index=False)

print("✅ Courses generated:")
print(courses_df.head())
print(f"Total: {len(courses_df)} courses")
print()



days = ["Mon", "Tue", "Wed", "Thu", "Fri"] * (NUM_TIME_SLOTS // 5 + 1)
times = [f"{9 + (i % 3)}:00" for i in range(NUM_TIME_SLOTS)]
end_times = [f"{10 + (i % 3)}:00" for i in range(NUM_TIME_SLOTS)]

time_slots_data = {
    "slot_id": list(range(NUM_TIME_SLOTS)),
    "day": days[:NUM_TIME_SLOTS],
    "start_time": times[:NUM_TIME_SLOTS],
    "end_time": end_times[:NUM_TIME_SLOTS]
}

time_slots_df = pd.DataFrame(time_slots_data)
time_slots_df.to_csv("data/time_slots.csv", index=False)

print("✅ Time Slots generated:")
print(time_slots_df)
print()



day_scholar_hosteller = ["Day Scholar", "Hosteller"]
time_preferences = ["Morning", "Afternoon", "Evening"]

student_list = []

for i in range(1, NUM_STUDENTS + 1):
    selected_courses = random.sample(course_ids, COURSES_PER_STUDENT)
    day_scholar = random.choice(day_scholar_hosteller)
    
    # Hostellers prefer morning classes, day scholars are flexible
    if day_scholar == "Hosteller":
        pref = random.choice(["Morning", "Morning", "Afternoon"])
    else:
        pref = random.choice(time_preferences)
    
    student_list.append({
        "student_id": f"S{i:04}",
        "requested_courses": ";".join(selected_courses),
        "time_preference": pref,
        "day_scholar_hosteller": day_scholar
    })

students_df = pd.DataFrame(student_list)
students_df.to_csv("data/students.csv", index=False)

print("✅ Students generated:")
print(students_df.head())
print(f"Total: {len(students_df)} students")
print()



print("\n" + "=" * 50)
print("📊 DATA GENERATION SUMMARY")
print("=" * 50)
print(f"Faculty: {NUM_FACULTY}")
print(f"Rooms: {NUM_ROOMS}")
print(f"Courses: {NUM_COURSES} ({len(mandatory_courses)} mandatory)")
print(f"Students: {NUM_STUDENTS}")
print(f"Time Slots: {NUM_TIME_SLOTS}")
print(f"Avg courses per student: {COURSES_PER_STUDENT}")
print("=" * 50 + "\n")

print("✅ All CSV files generated successfully in 'data/' folder!")
