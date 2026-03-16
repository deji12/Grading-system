from utils import save_to_csv, CLASSES_ROOT_DIR, load_config
import os
from pathlib import Path
import json

def calculate_students_best_in_n_subjects(data, config, n):
    subject_toppers = data.get("top_students_in_subjects", [])
    class_name = data.get("class")["name"]
    class_group = data.get("class")["group"]

    # subject id -> subject name lookup
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    student_subjects = {}

    # group subjects by student
    for item in subject_toppers:
        name = item["name"]
        subject_id = item["subject_id"]

        student_subjects.setdefault(name, []).append(subject_id)

    result = []

    # filter students with exactly n subjects
    for name, subjects in student_subjects.items():
        if len(subjects) == n:
            subject_names = [
                subject_lookup.get(sid, "Unknown")
                for sid in subjects
            ]

            result.append({
                "name": name,
                "subject_name": ", ".join(subject_names)
            })

    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/best_in_{n}_subjects.csv"
        ),
        field_names=["name", "subject_name"]
    )

def extract_and_save_most_improved_students(data):
    class_name = data.get("class")["name"]
    class_group = data.get("class")["group"]

    improved_students = data.get("most_improved_students", [])

    result = []

    for student in improved_students:
        result.append({
            "name": student.get("name", "").strip(),
            "improvement": student.get("improvement")
        })

    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/most_improved_students.csv"
        ),
        field_names=["name", "improvement"]
    )

def calculate_overall_best_in_n_subjects(class_data_path, config, n):
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    subject_best = {}

    # Step 1: collect best scores per subject across all class groups
    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        class_name = data["class"]["name"]
        class_group = data["class"]["group"]
        class_label = f"{class_name}{class_group}"

        for item in data.get("top_students_in_subjects", []):
            subject_id = item["subject_id"]
            name = item["name"].strip()
            score = item["score"]

            # if subject not seen or this score is higher
            if subject_id not in subject_best or score > subject_best[subject_id]["score"]:
                subject_best[subject_id] = {
                    "name": name,
                    "score": score,
                    "class": class_label
                }

    # Step 2: group subjects by winning student
    student_subjects = {}

    for subject_id, info in subject_best.items():
        name = info["name"]
        class_label = info["class"]
        subject_name = subject_lookup.get(subject_id, "Unknown")

        key = (name, class_label)

        student_subjects.setdefault(key, []).append(subject_name)

    # Step 3: filter students with exactly n subjects
    result = []

    for (name, class_label), subjects in student_subjects.items():
        if len(subjects) == n:
            result.append({
                "name": name,
                "subject_name": ", ".join(subjects),
                "class": class_label
            })

    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/best_overall_in_{n}_subjects.csv"
        ),
        field_names=["name", "subject_name", "class"]
    )

def execute_calculations(class_data_path):
    config = load_config()
    for class_group in Path(class_data_path).iterdir():
        with open(class_group, 'r') as file:
            data = json.load(file)
            for n in range(1, 5):
                calculate_students_best_in_n_subjects(data, config, n)

            extract_and_save_most_improved_students(data)

    for n in range(1, 7):
        calculate_overall_best_in_n_subjects(
            class_data_path=class_data_path,
            config=config,
            n=n
        ) 