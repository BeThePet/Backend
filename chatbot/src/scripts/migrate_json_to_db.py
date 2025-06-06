# import json
# import os
# from datetime import datetime
# from pathlib import Path

# from sqlalchemy.orm import Session

# from ..database.base import SessionLocal
# from api.db.models.chat import NewSymptom, SymptomLog


# def load_json_file(file_path: Path) -> dict:
#     try:
#         with open(file_path, encoding="utf-8") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         print(f"Warning: File not found - {file_path}")
#         return {}
#     except json.JSONDecodeError:
#         print(f"Warning: Invalid JSON format in file - {file_path}")
#         return {}


# def migrate_new_symptoms(db: Session, data_dir: Path):
#     new_symptoms_file = data_dir / "dynamic" / "new_symptoms.json"
#     data = load_json_file(new_symptoms_file)

#     if not data or "symptoms" not in data:
#         print("No new symptoms data to migrate")
#         return

#     for symptom_name, symptom_data in data["symptoms"].items():
#         new_symptom = NewSymptom(
#             symptom_name=symptom_name,
#             normalized_name=symptom_data.get("normalized_name"),
#             category=symptom_data.get("category"),
#             severity=symptom_data.get("severity"),
#             description=symptom_data.get("description"),
#             related_symptoms=symptom_data.get("related_symptoms", []),
#             possible_causes=symptom_data.get("possible_causes", []),
#         )
#         db.add(new_symptom)

#     try:
#         db.commit()
#         print(f"Successfully migrated {len(data['symptoms'])} new symptoms")
#     except Exception as e:
#         db.rollback()
#         print(f"Error during new symptoms migration: {e}")


# def migrate_symptom_logs(db: Session, data_dir: Path):
#     symptoms_log_file = data_dir / "dynamic" / "logs" / "symptoms_log.json"
#     logs = load_json_file(symptoms_log_file)

#     if not logs:
#         print("No symptom logs to migrate")
#         return

#     for log in logs:
#         # Note: Since we don't have chat_room_id in the original JSON,
#         # we'll need to create a default chat room or link these to
#         # existing chat rooms based on your business logic
#         continue  # Skip for now as we need chat_room_id

#     print("Symptom logs migration requires chat room association")


# def main():
#     # Get the base directory
#     base_dir = Path(__file__).parent.parent
#     data_dir = base_dir / "data"

#     # Create DB session
#     db = SessionLocal()

#     try:
#         # Migrate new symptoms
#         migrate_new_symptoms(db, data_dir)

#         # Migrate symptom logs
#         migrate_symptom_logs(db, data_dir)

#     finally:
#         db.close()


# if __name__ == "__main__":
#     main()
