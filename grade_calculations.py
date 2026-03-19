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

        student_subjects.setdefault(name, set()).add(subject_id)

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

    if not result:
        return
    
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

    if not result:
        return
    
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

    if not result:
        return 
    
    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/best_overall_in_{n}_subjects.csv"
        ),
        field_names=["name", "subject_name", "class"]
    )

# 2ND OR 3RD POSITION BELOW AVERAGE 80 ONLY
def calculate_2nd_and_3rd_position_below_average_80(data):
    class_name = data.get("class")["name"]
    class_group = data.get("class")["group"]

    top_students = data.get("top_students", {})

    result = []

    for position in ["second", "third"]:
        student = top_students.get(position)

        if not student:
            continue

        average = student.get("average", 0)

        # Apply condition: 70 < average < 80
        if 70 <= average < 80:
            result.append({
                "name": student.get("name"),
                "average": average,
                "position": position,
                "class": f"{class_name}{class_group}"
            })

    if not result:
        return 
    
    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/2nd_or_3rd_position_below_average_80.csv"
        ),
        field_names=["name", "average", "position", "class"]
    )

# 2ND OR 3RD POSITION BELOW AVERAGE 80, BEST IN ONE-FOUR SUBJECT
def calculate_2nd_and_3rd_position_below_average_80_best_in_n_subjects(data, config, n):
    class_name = data.get("class")["name"]
    class_group = data.get("class")["group"]

    top_students = data.get("top_students", {})
    subject_toppers = data.get("top_students_in_subjects", [])

    # subject id -> subject name lookup
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    # Step 1: count how many subjects each student is best in
    student_subjects = {}
    for item in subject_toppers:
        name = item["name"]
        subject_id = item["subject_id"]

        # ✅ Use set to avoid duplicates
        student_subjects.setdefault(name, set()).add(subject_id)

    result = []

    # Step 2: check only 2nd and 3rd positions
    for position in ["second", "third"]:
        student = top_students.get(position)

        if not student:
            continue

        name = student.get("name")
        average = student.get("average", 0)

        # Step 3: apply average condition
        if not (70 <= average < 80):
            continue

        # Step 4: check if student is best in exactly N subjects
        subjects = student_subjects.get(name, set())

        if len(subjects) == n:
            subject_names = [
                subject_lookup.get(sid, "Unknown")
                for sid in subjects
            ]

            result.append({
                "name": name,
                "average": average,
                "position": position,
                "subject_name": ", ".join(subject_names),
                "class": f"{class_name}{class_group}"
            })

    if not result:
        return

    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/"
            f"2nd_or_3rd_position_below_average_80_best_in_{n}_subjects.csv"
        ),
        field_names=["name", "average", "position", "subject_name", "class"]
    )

# 2ND OR 3RD POSITION BELOW AVERAGE 80, 1ST AMONG THE BEST, BEST IN ONE - SIX SUBJECTS
def calculate_2nd_3rd_below_80_and_overall_best_in_n_subjects(class_data_path, config, n):
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    # =========================
    # STEP 1: Get overall best per subject
    # =========================
    subject_best = {}

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

            if subject_id not in subject_best or score > subject_best[subject_id]["score"]:
                subject_best[subject_id] = {
                    "name": name,
                    "score": score,
                    "class": class_label
                }

    # =========================
    # STEP 2: Group subjects per student (overall winners)
    # =========================
    student_subjects = {}

    for subject_id, info in subject_best.items():
        name = info["name"]
        class_label = info["class"]
        subject_name = subject_lookup.get(subject_id, "Unknown")

        key = (name, class_label)
        student_subjects.setdefault(key, []).append(subject_name)

    # =========================
    # STEP 3: Filter students with exactly N subjects
    # =========================
    qualified_overall = {
        (name, class_label): subjects
        for (name, class_label), subjects in student_subjects.items()
        if len(subjects) == n
    }

    # =========================
    # STEP 4: Now filter per class for 2nd/3rd + avg condition
    # =========================
    results_by_class = {}

    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        class_name = data["class"]["name"]
        class_group = data["class"]["group"]
        class_label = f"{class_name}{class_group}"

        top_students = data.get("top_students", {})

        result = []

        for position in ["second", "third"]:
            student = top_students.get(position)

            if not student:
                continue

            name = student.get("name")
            average = student.get("average", 0)

            # condition: 70 ≤ avg < 80
            if not (70 <= average < 80):
                continue

            key = (name, class_label)

            # check if this student is among overall best in N subjects
            if key in qualified_overall:
                subjects = qualified_overall[key]

                result.append({
                    "name": name,
                    "average": average,
                    "position": position,
                    "subject_name": ", ".join(subjects),
                    "class": class_label
                })

        if result:
            results_by_class[class_label] = result

            # save per class
            save_to_csv(
                data=result,
                file_destination=os.path.join(
                    CLASSES_ROOT_DIR,
                    f"{class_name}/results/{class_name}_{class_group}/"
                    f"2nd_or_3rd_position_below_average_80_overall_best_in_{n}_subjects.csv"
                ),
                field_names=["name", "average", "position", "subject_name", "class"]
            )

# 2ND OR 3RD POSITION ABOVE AVERAGE 80 ONLY
def calculate_2nd_and_3rd_position_above_average_80(data):
    class_name = data.get("class")["name"]
    class_group = data.get("class")["group"]

    top_students = data.get("top_students", {})

    result = []

    for position in ["second", "third"]:
        student = top_students.get(position)

        if not student:
            continue

        name = student.get("name")
        average = student.get("average", 0)

        # ✅ Apply condition: average >= 80
        if average >= 80:
            result.append({
                "name": name,
                "average": average,
                "position": position,
                "class": f"{class_name}{class_group}"
            })

    if not result:
        return 
    
    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/2nd_or_3rd_position_above_average_80.csv"
        ),
        field_names=["name", "average", "position", "class"]
    )

# 2ND OR 3RD POSITION ABOVE AVERAGE 80, BEST IN ONE-SIX SUBJECT
def calculate_2nd_and_3rd_position_above_average_80_best_in_n_subjects(data, config, n):
    class_name = data.get("class")["name"].strip()
    class_group = data.get("class")["group"].strip()

    top_students = data.get("top_students", {})
    subject_toppers = data.get("top_students_in_subjects", [])

    # subject id -> subject name lookup
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    # Step 1: count how many subjects each student is best in
    student_subjects = {}
    for item in subject_toppers:
        name = item["name"]
        subject_id = item["subject_id"]

        # ✅ Use set to avoid duplicates
        student_subjects.setdefault(name, set()).add(subject_id)

    result = []

    # Step 2: check only 2nd and 3rd positions
    for position in ["second", "third"]:
        student = top_students.get(position)

        if not student:
            continue

        name = student.get("name")
        average = student.get("average", 0)

        # ✅ Step 3: apply NEW condition (above 80)
        if average < 80:
            continue

        # Step 4: check if student is best in exactly N subjects
        subjects = student_subjects.get(name, set())

        if len(subjects) == n:
            subject_names = [
                subject_lookup.get(sid, "Unknown")
                for sid in subjects
            ]

            result.append({
                "name": name,
                "average": average,
                "position": position,
                "subject_name": ", ".join(subject_names),
                "class": f"{class_name}{class_group}"
            })

    if not result:
        return

    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/"
            f"2nd_or_3rd_position_above_average_80_best_in_{n}_subjects.csv"
        ),
        field_names=["name", "average", "position", "subject_name", "class"]
    )

# 2ND OR 3RD POSITION ABOVE AVERAGE 80, 1ST AMONG THE BEST, BEST IN ONE-FIVE SUBJECTS
def calculate_2nd_3rd_above_80_and_overall_best_in_n_subjects(class_data_path, config, n):
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    # =========================
    # STEP 1: Get overall best per subject
    # =========================
    subject_best = {}

    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        class_name = data["class"]["name"].strip()
        class_group = data["class"]["group"].strip()
        class_label = f"{class_name}{class_group}"

        for item in data.get("top_students_in_subjects", []):
            subject_id = item["subject_id"]
            name = item["name"].strip()
            score = item["score"]

            if subject_id not in subject_best or score > subject_best[subject_id]["score"]:
                subject_best[subject_id] = {
                    "name": name,
                    "score": score,
                    "class": class_label
                }

    # =========================
    # STEP 2: Group subjects per student
    # =========================
    student_subjects = {}

    for subject_id, info in subject_best.items():
        name = info["name"]
        class_label = info["class"]
        subject_name = subject_lookup.get(subject_id, "Unknown")

        key = (name, class_label)
        student_subjects.setdefault(key, []).append(subject_name)

    # =========================
    # STEP 3: Filter students with exactly N subjects
    # =========================
    qualified_overall = {
        (name, class_label): subjects
        for (name, class_label), subjects in student_subjects.items()
        if len(subjects) == n
    }

    # =========================
    # STEP 4: Per-class filtering (2nd/3rd + avg >= 80)
    # =========================
    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        class_name = data["class"]["name"].strip()
        class_group = data["class"]["group"].strip()
        class_label = f"{class_name}{class_group}"

        top_students = data.get("top_students", {})

        result = []

        for position in ["second", "third"]:
            student = top_students.get(position)

            if not student:
                continue

            name = student.get("name").strip()
            average = student.get("average", 0)

            # ✅ NEW CONDITION: average >= 80
            if average < 80:
                continue

            key = (name, class_label)

            # check if student is overall best in N subjects
            if key in qualified_overall:
                subjects = qualified_overall[key]

                result.append({
                    "name": name,
                    "average": average,
                    "position": position,
                    "subject_name": ", ".join(subjects),
                    "class": class_label
                })

        if not result:
            continue

        save_to_csv(
            data=result,
            file_destination=os.path.join(
                CLASSES_ROOT_DIR,
                f"{class_name}/results/{class_name}_{class_group}/"
                f"2nd_or_3rd_position_above_average_80_overall_best_in_{n}_subjects.csv"
            ),
            field_names=["name", "average", "position", "subject_name", "class"]
        )

# 1ST POSITION BELOW AVERAGE 80 ONLY
def calculate_1st_position_below_average_80(data):
    class_name = data.get("class")["name"].strip()
    class_group = data.get("class")["group"].strip()

    top_students = data.get("top_students", {})

    result = []

    # Only FIRST position
    student = top_students.get("first")

    if student:
        name = student.get("name")
        average = student.get("average", 0)

        # Condition: 70 ≤ average < 80
        if 70 <= average < 80:
            result.append({
                "name": name,
                "average": average,
                "position": "first",
                "class": f"{class_name}{class_group}"
            })

    if not result:
        return

    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/1st_position_below_average_80.csv"
        ),
        field_names=["name", "average", "position", "class"]
    )

# 1ST POSITION BELOW AVERAGE 80, BEST IN ONE-FIVE SUBJECT
def calculate_1st_position_below_average_80_best_in_n_subjects(data, config, n):
    class_name = data.get("class")["name"].strip()
    class_group = data.get("class")["group"].strip()

    top_students = data.get("top_students", {})
    subject_toppers = data.get("top_students_in_subjects", [])

    # subject id -> subject name lookup
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    # =========================
    # STEP 1: Count subjects per student
    # =========================
    student_subjects = {}

    for item in subject_toppers:
        name = item["name"].strip()
        subject_id = item["subject_id"]

        # ✅ Use set to avoid duplicates
        student_subjects.setdefault(name, set()).add(subject_id)

    result = []

    # =========================
    # STEP 2: Check FIRST position
    # =========================
    student = top_students.get("first")

    if student:
        name = student.get("name").strip()
        average = student.get("average", 0)

        # ✅ Condition: 70 ≤ avg < 80
        if 70 <= average < 80:

            subjects = student_subjects.get(name, set())

            # ✅ Check exactly N subjects
            if len(subjects) == n:
                subject_names = [
                    subject_lookup.get(sid, "Unknown")
                    for sid in subjects
                ]

                result.append({
                    "name": name,
                    "average": average,
                    "position": "first",
                    "subject_name": ", ".join(subject_names),
                    "class": f"{class_name}{class_group}"
                })

    if not result:
        return

    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/"
            f"1st_position_below_average_80_best_in_{n}_subjects.csv"
        ),
        field_names=["name", "average", "position", "subject_name", "class"]
    )

# 1ST POSITION BELOW AVERAGE 80, 1ST AMONG THE BEST, BEST IN ONE SUBJECT
def calculate_1st_below_80_and_overall_best_in_n_subjects(class_data_path, config, n):
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    # =========================
    # STEP 1: Get overall best per subject
    # =========================
    subject_best = {}

    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        class_name = data["class"]["name"].strip()
        class_group = data["class"]["group"].strip()
        class_label = f"{class_name}{class_group}"

        for item in data.get("top_students_in_subjects", []):
            subject_id = item["subject_id"]
            name = item["name"].strip()
            score = item["score"]

            if subject_id not in subject_best or score > subject_best[subject_id]["score"]:
                subject_best[subject_id] = {
                    "name": name,
                    "score": score,
                    "class": class_label
                }

    # =========================
    # STEP 2: Group subjects per student (GLOBAL winners)
    # =========================
    student_subjects = {}

    for subject_id, info in subject_best.items():
        name = info["name"]
        class_label = info["class"]
        subject_name = subject_lookup.get(subject_id, "Unknown")

        key = (name, class_label)
        student_subjects.setdefault(key, []).append(subject_name)

    # =========================
    # STEP 3: Filter students with exactly N subjects
    # =========================
    qualified_overall = {
        (name, class_label): subjects
        for (name, class_label), subjects in student_subjects.items()
        if len(subjects) == n
    }

    # =========================
    # STEP 4: Check each class for FIRST + avg condition
    # =========================
    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        class_name = data["class"]["name"].strip()
        class_group = data["class"]["group"].strip()
        class_label = f"{class_name}{class_group}"

        top_students = data.get("top_students", {})
        student = top_students.get("first")

        if not student:
            continue

        name = student.get("name").strip()
        average = student.get("average", 0)

        # ✅ Condition: 70 ≤ avg < 80
        if not (70 <= average < 80):
            continue

        key = (name, class_label)

        # ✅ Check if student is overall best in N subjects
        if key not in qualified_overall:
            continue

        subjects = qualified_overall[key]

        result = [{
            "name": name,
            "average": average,
            "position": "first",
            "subject_name": ", ".join(subjects),
            "class": class_label
        }]

        save_to_csv(
            data=result,
            file_destination=os.path.join(
                CLASSES_ROOT_DIR,
                f"{class_name}/results/{class_name}_{class_group}/"
                f"1st_below_average_80_overall_best_in_{n}_subjects.csv"
            ),
            field_names=["name", "average", "position", "subject_name", "class"]
        )

# 1ST POSITION ABOVE AVERAGE 80 ONLY
def calculate_1st_position_above_average_80(data):
    class_name = data.get("class")["name"].strip()
    class_group = data.get("class")["group"].strip()

    top_students = data.get("top_students", {})

    result = []

    # Only FIRST position
    student = top_students.get("first")

    if student:
        name = student.get("name")
        average = student.get("average", 0)

        # ✅ Condition: average >= 80
        if average >= 80:
            result.append({
                "name": name,
                "average": average,
                "position": "first",
                "class": f"{class_name}{class_group}"
            })

    if not result:
        return

    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/1st_position_above_average_80.csv"
        ),
        field_names=["name", "average", "position", "class"]
    )

# 1ST POSITION ABOVE AVERAGE 80, BEST IN ONE SUBJECT
def calculate_1st_position_above_average_80_best_in_n_subjects(data, config, n):
    class_name = data.get("class")["name"].strip()
    class_group = data.get("class")["group"].strip()

    top_students = data.get("top_students", {})
    subject_toppers = data.get("top_students_in_subjects", [])

    # subject id -> subject name lookup
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    # =========================
    # STEP 1: Count subjects per student
    # =========================
    student_subjects = {}

    for item in subject_toppers:
        name = item["name"].strip()
        subject_id = item["subject_id"]

        # ✅ Use set to avoid duplicates
        student_subjects.setdefault(name, set()).add(subject_id)

    result = []

    # =========================
    # STEP 2: Check FIRST position
    # =========================
    student = top_students.get("first")

    if student:
        name = student.get("name").strip()
        average = student.get("average", 0)

        # ✅ Condition: average >= 80
        if average >= 80:

            subjects = student_subjects.get(name, set())

            # ✅ Check exactly N subjects
            if len(subjects) == n:
                subject_names = [
                    subject_lookup.get(sid, "Unknown")
                    for sid in subjects
                ]

                result.append({
                    "name": name,
                    "average": average,
                    "position": "first",
                    "subject_name": ", ".join(subject_names),
                    "class": f"{class_name}{class_group}"
                })

    if not result:
        return

    save_to_csv(
        data=result,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/"
            f"1st_position_above_average_80_best_in_{n}_subjects.csv"
        ),
        field_names=["name", "average", "position", "subject_name", "class"]
    )

# 1ST POSITION ABOVE AVERAGE 80, 1ST AMONG THE BEST, BEST IN ONE SUBJECT
def calculate_1st_above_80_and_overall_best_in_n_subjects(class_data_path, config, n):
    subject_lookup = {s["id"]: s["name"] for s in config["subjects"]}

    # =========================
    # STEP 1: Get overall best per subject across all class groups
    # =========================
    subject_best = {}

    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        class_name = data["class"]["name"].strip()
        class_group = data["class"]["group"].strip()
        class_label = f"{class_name}{class_group}"

        for item in data.get("top_students_in_subjects", []):
            subject_id = item["subject_id"]
            name = item["name"].strip()
            score = item["score"]

            # Update if higher score
            if subject_id not in subject_best or score > subject_best[subject_id]["score"]:
                subject_best[subject_id] = {
                    "name": name,
                    "score": score,
                    "class": class_label
                }

    # =========================
    # STEP 2: Group subjects per student (overall winners)
    # =========================
    student_subjects = {}

    for subject_id, info in subject_best.items():
        name = info["name"]
        class_label = info["class"]
        subject_name = subject_lookup.get(subject_id, "Unknown")

        key = (name, class_label)
        student_subjects.setdefault(key, []).append(subject_name)

    # =========================
    # STEP 3: Filter students with exactly N subjects
    # =========================
    qualified_overall = {
        (name, class_label): subjects
        for (name, class_label), subjects in student_subjects.items()
        if len(subjects) == n
    }

    # =========================
    # STEP 4: Check each class for 1st position + avg condition
    # =========================
    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        class_name = data["class"]["name"].strip()
        class_group = data["class"]["group"].strip()
        class_label = f"{class_name}{class_group}"

        top_students = data.get("top_students", {})
        student = top_students.get("first")

        if not student:
            continue

        name = student.get("name").strip()
        average = student.get("average", 0)

        # ✅ Condition: average ≥ 80
        if average < 80:
            continue

        key = (name, class_label)

        # ✅ Check if student is overall best in N subjects
        if key not in qualified_overall:
            continue

        subjects = qualified_overall[key]

        result = [{
            "name": name,
            "average": average,
            "position": "first",
            "subject_name": ", ".join(subjects),
            "class": class_label
        }]

        save_to_csv(
            data=result,
            file_destination=os.path.join(
                CLASSES_ROOT_DIR,
                f"{class_name}/results/{class_name}_{class_group}/"
                f"1st_above_average_80_overall_best_in_{n}_subjects.csv"
            ),
            field_names=["name", "average", "position", "subject_name", "class"]
        )

def execute_calculations(class_data_path):
    config = load_config()
    for class_group in Path(class_data_path).iterdir():
        
        with open(class_group, 'r') as file:
            data = json.load(file)

            for n in range(1, 5):
                calculate_students_best_in_n_subjects(data, config, n)

            extract_and_save_most_improved_students(data)
            calculate_2nd_and_3rd_position_below_average_80(data)

            for n in range(1, 5):
                calculate_2nd_and_3rd_position_below_average_80_best_in_n_subjects(data, config, n)

            for n in range(1, 7):
                calculate_2nd_and_3rd_position_above_average_80_best_in_n_subjects(data, config, n)

            calculate_2nd_and_3rd_position_above_average_80(data)
            calculate_1st_position_below_average_80(data)

            for n in range(1, 6):
                calculate_1st_position_below_average_80_best_in_n_subjects(data, config, n)

            for n in range(1, 6):
                calculate_1st_position_above_average_80_best_in_n_subjects(data, config, n)

            calculate_1st_position_above_average_80(data)

            for n in range(1, 9):
                calculate_1st_above_80_and_overall_best_in_n_subjects(class_data_path, config, n)

    for n in range(1, 7):
        calculate_2nd_3rd_below_80_and_overall_best_in_n_subjects(
            class_data_path, 
            config, 
            n
        )

    for n in range(1, 6):
        calculate_2nd_3rd_above_80_and_overall_best_in_n_subjects(
            class_data_path,
            config,
            n
        )

    for n in range(1, 7):
        calculate_overall_best_in_n_subjects(
            class_data_path=class_data_path,
            config=config,
            n=n
        ) 

    for n in range(1, 8):
        calculate_1st_below_80_and_overall_best_in_n_subjects(
            class_data_path,
            config,
            n
        )