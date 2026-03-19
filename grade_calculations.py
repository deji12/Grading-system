from utils import save_to_csv, CLASSES_ROOT_DIR, load_config
import os
from pathlib import Path
import json


def _get_class_info(data):
    cls = data.get("class") or {}
    class_name = (cls.get("name") or "").strip()
    class_group = (cls.get("group") or "").strip()
    return class_name, class_group, f"{class_name}{class_group}"


def _get_subject_lookup(config):
    return {s.get("id"): s.get("name") for s in config.get("subjects", [])}


def _write_class_csv(class_name, class_group, filename, data, field_names):
    save_to_csv(
        data=data,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{class_name}_{class_group}/{filename}"
        ),
        field_names=field_names,
    )


def _write_overall_csv(class_name, filename, data, field_names):
    save_to_csv(
        data=data,
        file_destination=os.path.join(
            CLASSES_ROOT_DIR,
            f"{class_name}/results/{filename}"
        ),
        field_names=field_names,
    )


def _count_best_subjects_per_student(subject_toppers):
    student_subjects = {}
    for item in subject_toppers:
        name = (item.get("name") or "").strip()
        subject_id = item.get("subject_id")
        if not name or subject_id is None:
            continue
        student_subjects.setdefault(name, set()).add(subject_id)
    return student_subjects


def _get_overall_best_by_n(class_data_path, config):
    subject_lookup = _get_subject_lookup(config)

    # Find the best score per subject across all class group files
    subject_best = {}
    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        cls = data.get("class") or {}
        class_label = f"{(cls.get('name') or '').strip()}{(cls.get('group') or '').strip()}"

        for item in data.get("top_students_in_subjects", []):
            subject_id = item.get("subject_id")
            name = (item.get("name") or "").strip()
            score = item.get("score", 0)

            if subject_id is None or not name:
                continue

            existing = subject_best.get(subject_id)
            if existing is None or score > existing["score"]:
                subject_best[subject_id] = {"name": name, "score": score, "class": class_label}

    # Group best subjects per student + class label, keyed by number of subjects
    overall_best_by_n = {}
    by_student = {}
    for subject_id, info in subject_best.items():
        key = (info["name"], info["class"])
        by_student.setdefault(key, []).append(subject_lookup.get(subject_id, "Unknown"))

    for key, subjects in by_student.items():
        overall_best_by_n.setdefault(len(subjects), {})[key] = subjects

    return overall_best_by_n


def _get_class_name_from_data_path(class_data_path):
    """Return the class name for the given data folder by reading the first JSON file."""
    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
        cls = data.get("class") or {}
        return (cls.get("name") or "").strip()
    return ""


def _generate_position_report_for_class(
    data,
    config=None,
    positions=None,
    avg_min=None,
    avg_max=None,
    best_scope=None,
    best_n=None,
    overall_best_by_n=None,
    filename=None,
):
    if config is None:
        config = load_config()
    if positions is None:
        positions = []
    """Generic engine for generating a per-class position/average based report.

    - positions: list of position keys (e.g. ['second', 'third']).
    - avg_min/avg_max: inclusive lower bound and exclusive upper bound for average.
    - best_scope: None|'local'|'overall'.
    - best_n: if best_scope is set, this is the exact number of subjects.
    - overall_best_by_n: precomputed map from n -> {(name, class): [subjects]}.
    - filename: output filename (required).
    """

    if filename is None:
        return

    class_name, class_group, class_label = _get_class_info(data)
    top_students = data.get("top_students", {}) or {}

    subject_lookup = _get_subject_lookup(config)

    # If we need local "best in N subjects" info, compute it once per class.
    student_subjects = None
    if best_scope == "local":
        student_subjects = _count_best_subjects_per_student(
            data.get("top_students_in_subjects", [])
        )

    # If we need overall-best info, make sure it's been computed.
    qualified_overall = None
    if best_scope == "overall":
        if overall_best_by_n is None:
            return
        qualified_overall = overall_best_by_n.get(best_n, {})

    result = []

    for position in positions:
        student = top_students.get(position)
        if not student:
            continue

        name = (student.get("name") or "").strip()
        average = student.get("average", 0)

        if avg_min is not None and average < avg_min:
            continue
        if avg_max is not None and average >= avg_max:
            continue

        subject_names = None

        if best_scope == "local":
            subjects = student_subjects.get(name, set())
            if best_n is not None and len(subjects) != best_n:
                continue
            subject_names = [
                subject_lookup.get(sid, "Unknown")
                for sid in subjects
            ]

        elif best_scope == "overall":
            key = (name, class_label)
            subjects = qualified_overall.get(key)
            if not subjects:
                continue
            subject_names = subjects

        row = {
            "name": name,
            "average": average,
            "position": position,
            "class": class_label,
        }

        if subject_names is not None:
            row["subject_name"] = ", ".join(subject_names)

        result.append(row)

    if not result:
        return

    field_names = ["name", "average", "position"]
    if any("subject_name" in r for r in result):
        field_names.insert(3, "subject_name")
    field_names.append("class")

    _write_class_csv(class_name, class_group, filename, result, field_names)


def calculate_students_best_in_n_subjects(data, config, n):
    class_name, class_group, _ = _get_class_info(data)

    subject_lookup = _get_subject_lookup(config)
    student_subjects = _count_best_subjects_per_student(
        data.get("top_students_in_subjects", [])
    )

    result = []
    for name, subjects in student_subjects.items():
        if len(subjects) != n:
            continue

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

    _write_class_csv(
        class_name,
        class_group,
        f"best_in_{n}_subjects.csv",
        result,
        ["name", "subject_name"],
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
    class_name = _get_class_name_from_data_path(class_data_path)
    if not class_name:
        return

    overall_best_by_n = _get_overall_best_by_n(class_data_path, config)
    entries = overall_best_by_n.get(n)
    if not entries:
        return

    result = [
        {
            "name": name,
            "subject_name": ", ".join(subjects),
            "class": class_label,
        }
        for (name, class_label), subjects in entries.items()
    ]

    _write_overall_csv(
        class_name,
        f"best_overall_in_{n}_subjects.csv",
        result,
        ["name", "subject_name", "class"],
    )

# 2ND OR 3RD POSITION BELOW AVERAGE 80 ONLY
def calculate_2nd_and_3rd_position_below_average_80(data):
    _generate_position_report_for_class(
        data=data,
        positions=["second", "third"],
        avg_min=70,
        avg_max=80,
        filename="2nd_or_3rd_position_below_average_80.csv",
    )

# 2ND OR 3RD POSITION BELOW AVERAGE 80, BEST IN ONE-FOUR SUBJECT
def calculate_2nd_and_3rd_position_below_average_80_best_in_n_subjects(data, config, n):
    _generate_position_report_for_class(
        data=data,
        config=config,
        positions=["second", "third"],
        avg_min=70,
        avg_max=80,
        best_scope="local",
        best_n=n,
        filename=f"2nd_or_3rd_position_below_average_80_best_in_{n}_subjects.csv",
    )

# 2ND OR 3RD POSITION BELOW AVERAGE 80, 1ST AMONG THE BEST, BEST IN ONE - SIX SUBJECTS
def calculate_2nd_3rd_below_80_and_overall_best_in_n_subjects(
    class_data_path,
    config,
    n,
    overall_best_by_n=None,
):
    if overall_best_by_n is None:
        overall_best_by_n = _get_overall_best_by_n(class_data_path, config)

    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        _generate_position_report_for_class(
            data=data,
            config=config,
            positions=["second", "third"],
            avg_min=70,
            avg_max=80,
            best_scope="overall",
            best_n=n,
            overall_best_by_n=overall_best_by_n,
            filename=f"2nd_or_3rd_position_below_average_80_overall_best_in_{n}_subjects.csv",
        )

# 2ND OR 3RD POSITION ABOVE AVERAGE 80 ONLY
def calculate_2nd_and_3rd_position_above_average_80(data):
    _generate_position_report_for_class(
        data=data,
        positions=["second", "third"],
        avg_min=80,
        filename="2nd_or_3rd_position_above_average_80.csv",
    )

# 2ND OR 3RD POSITION ABOVE AVERAGE 80, BEST IN ONE-SIX SUBJECT
def calculate_2nd_and_3rd_position_above_average_80_best_in_n_subjects(data, config, n):
    _generate_position_report_for_class(
        data=data,
        config=config,
        positions=["second", "third"],
        avg_min=80,
        best_scope="local",
        best_n=n,
        filename=f"2nd_or_3rd_position_above_average_80_best_in_{n}_subjects.csv",
    )

# 2ND OR 3RD POSITION ABOVE AVERAGE 80, 1ST AMONG THE BEST, BEST IN ONE-FIVE SUBJECTS
def calculate_2nd_3rd_above_80_and_overall_best_in_n_subjects(
    class_data_path,
    config,
    n,
    overall_best_by_n=None,
):
    if overall_best_by_n is None:
        overall_best_by_n = _get_overall_best_by_n(class_data_path, config)

    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        _generate_position_report_for_class(
            data=data,
            config=config,
            positions=["second", "third"],
            avg_min=80,
            best_scope="overall",
            best_n=n,
            overall_best_by_n=overall_best_by_n,
            filename=f"2nd_or_3rd_position_above_average_80_overall_best_in_{n}_subjects.csv",
        )

# 1ST POSITION BELOW AVERAGE 80 ONLY
def calculate_1st_position_below_average_80(data):
    _generate_position_report_for_class(
        data=data,
        positions=["first"],
        avg_min=70,
        avg_max=80,
        filename="1st_position_below_average_80.csv",
    )

# 1ST POSITION BELOW AVERAGE 80, BEST IN ONE-FIVE SUBJECT
def calculate_1st_position_below_average_80_best_in_n_subjects(data, config, n):
    _generate_position_report_for_class(
        data=data,
        config=config,
        positions=["first"],
        avg_min=70,
        avg_max=80,
        best_scope="local",
        best_n=n,
        filename=f"1st_position_below_average_80_best_in_{n}_subjects.csv",
    )

# 1ST POSITION BELOW AVERAGE 80, 1ST AMONG THE BEST, BEST IN ONE SUBJECT
def calculate_1st_below_80_and_overall_best_in_n_subjects(
    class_data_path,
    config,
    n,
    overall_best_by_n=None,
):
    if overall_best_by_n is None:
        overall_best_by_n = _get_overall_best_by_n(class_data_path, config)

    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        _generate_position_report_for_class(
            data=data,
            config=config,
            positions=["first"],
            avg_min=70,
            avg_max=80,
            best_scope="overall",
            best_n=n,
            overall_best_by_n=overall_best_by_n,
            filename=f"1st_below_average_80_overall_best_in_{n}_subjects.csv",
        )

# 1ST POSITION ABOVE AVERAGE 80 ONLY
def calculate_1st_position_above_average_80(data):
    _generate_position_report_for_class(
        data=data,
        positions=["first"],
        avg_min=80,
        filename="1st_position_above_average_80.csv",
    )

# 1ST POSITION ABOVE AVERAGE 80, BEST IN ONE SUBJECT
def calculate_1st_position_above_average_80_best_in_n_subjects(data, config, n):
    _generate_position_report_for_class(
        data=data,
        config=config,
        positions=["first"],
        avg_min=80,
        best_scope="local",
        best_n=n,
        filename=f"1st_position_above_average_80_best_in_{n}_subjects.csv",
    )

# 1ST POSITION ABOVE AVERAGE 80, 1ST AMONG THE BEST, BEST IN ONE SUBJECT
def calculate_1st_above_80_and_overall_best_in_n_subjects(
    class_data_path,
    config,
    n,
    overall_best_by_n=None,
):
    if overall_best_by_n is None:
        overall_best_by_n = _get_overall_best_by_n(class_data_path, config)

    for file in Path(class_data_path).glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)

        _generate_position_report_for_class(
            data=data,
            config=config,
            positions=["first"],
            avg_min=80,
            best_scope="overall",
            best_n=n,
            overall_best_by_n=overall_best_by_n,
            filename=f"1st_above_average_80_overall_best_in_{n}_subjects.csv",
        )

def execute_calculations(class_data_path):
    config = load_config()
    overall_best_by_n = _get_overall_best_by_n(class_data_path, config)
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
                calculate_1st_above_80_and_overall_best_in_n_subjects(
                    class_data_path,
                    config,
                    n,
                    overall_best_by_n=overall_best_by_n,
                )

    for n in range(1, 7):
        calculate_2nd_3rd_below_80_and_overall_best_in_n_subjects(
            class_data_path,
            config,
            n,
            overall_best_by_n=overall_best_by_n,
        )

    for n in range(1, 6):
        calculate_2nd_3rd_above_80_and_overall_best_in_n_subjects(
            class_data_path,
            config,
            n,
            overall_best_by_n=overall_best_by_n,
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
            n,
            overall_best_by_n=overall_best_by_n,
        )