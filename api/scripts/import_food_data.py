#!/usr/bin/env python3
"""
사료 시드 데이터 가져오기 스크립트
4500개 사료 데이터를 CSV에서 읽어 DB에 삽입
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from api.db.models import FoodProduct
from api.db.session import SessionLocal


class FoodDataImporter:
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.db = SessionLocal()

    def _clean_numeric_value(self, value) -> Optional[float]:
        """숫자 값 정리"""
        if pd.isna(value) or value == "" or value is None:
            return None

        try:
            # 문자열인 경우 숫자만 추출
            if isinstance(value, str):
                # % 기호 제거
                value = value.replace("%", "")
                # 숫자와 소수점만 남기기
                value = re.sub(r"[^\d.]", "", value)
                if not value:
                    return None

            return float(value)
        except (ValueError, TypeError):
            return None

    def _clean_text_field(self, value) -> Optional[str]:
        """텍스트 필드 정리"""
        if pd.isna(value) or value == "" or value is None:
            return None

        text = str(value).strip()
        return text if text else None

    def load_csv_data(self) -> pd.DataFrame:
        """CSV 파일 로드 및 전처리"""
        print(f"Loading CSV file: {self.csv_file_path}")

        try:
            # CSV 파일 읽기
            df = pd.read_csv(self.csv_file_path)
            print(f"Loaded {len(df)} records from CSV")

            # 컬럼명 정리 (공백 제거)
            df.columns = df.columns.str.strip()

            # 필수 컬럼 확인
            required_columns = ["Product name", "Brand"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            # CSV 인덱스 추가 (0부터 시작)
            df["csv_index"] = df.index

            return df

        except Exception as e:
            print(f"Error loading CSV file: {e}")
            raise

    def process_row(self, row: dict, csv_index: int) -> FoodProduct:
        """CSV 행을 FoodProduct 객체로 변환 (단순화된 모델 버전)"""

        # 영양소 정보 처리
        nutrients = {}
        nutrient_columns = [
            "protein_pct",
            "fat_pct",
            "fiber_pct",
            "moisture_pct",
            "calcium_pct",
            "phosphorus_pct",
            "sodium_pct",
            "omega_6_pct",
            "omega_3_pct",
        ]

        for nutrient in nutrient_columns:
            nutrients[nutrient] = self._clean_numeric_value(row.get(nutrient))

        return FoodProduct(
            # CSV 매핑용 인덱스 (핵심!)
            csv_index=csv_index,
            # 기본 정보 (모두 nullable)
            product_name=self._clean_text_field(row.get("Product name")),
            url=self._clean_text_field(row.get("Url")),
            brand=self._clean_text_field(row.get("Brand")),
            price=self._clean_numeric_value(row.get("Price")),
            ingredients=self._clean_text_field(row.get("Ingredients")),
            calorie_content=self._clean_text_field(row.get("Calorie Content")),
            # 영양소 성분
            **nutrients,
        )

    def import_data(self, batch_size: int = 100):
        """데이터 가져오기 실행"""
        try:
            # 기존 데이터 확인
            existing_count = self.db.query(FoodProduct).count()

            if existing_count > 0:
                print(f"Warning: {existing_count} food product records already exist.")
                response = input(
                    "Do you want to continue? This will add duplicate data. (y/N): "
                )
                if response.lower() != "y":
                    print("Import cancelled.")
                    return

            # CSV 데이터 로드
            df = self.load_csv_data()

            # 배치별로 처리
            total_rows = len(df)
            processed = 0
            errors = 0

            print(f"Starting import of {total_rows} records...")

            for i in range(0, total_rows, batch_size):
                batch_df = df.iloc[i : i + batch_size]
                batch_products = []

                for idx, row in batch_df.iterrows():
                    try:
                        # CSV 인덱스를 명시적으로 전달
                        csv_index = int(row["csv_index"])
                        food_product = self.process_row(row.to_dict(), csv_index)
                        batch_products.append(food_product)
                        processed += 1
                    except Exception as e:
                        print(f"Error processing row {idx}: {e}")
                        errors += 1
                        continue

                # 배치 저장
                if batch_products:
                    try:
                        self.db.add_all(batch_products)
                        self.db.commit()
                        print(
                            f"Processed {processed}/{total_rows} records (errors: {errors})"
                        )
                    except Exception as e:
                        print(f"Error saving batch: {e}")
                        self.db.rollback()
                        errors += len(batch_products)

            print(f"\nImport completed!")
            print(f"Successfully imported: {processed - errors} records")
            print(f"Errors: {errors} records")

            # 최종 통계
            final_count = self.db.query(FoodProduct).count()
            print(f"Total food product records in DB: {final_count}")

            # CSV 인덱스 매핑 확인
            mapped_count = (
                self.db.query(FoodProduct)
                .filter(FoodProduct.csv_index.isnot(None))
                .count()
            )
            print(f"Records with CSV index mapping: {mapped_count}")

        except Exception as e:
            print(f"Import failed: {e}")
            self.db.rollback()
            raise
        finally:
            self.db.close()


def main():
    """메인 실행 함수"""
    # CSV 파일 경로
    csv_file_path = (
        project_root / "foodrecomender" / "data" / "dog_food_4500_with_nutrients.csv"
    )

    if not csv_file_path.exists():
        print(f"Error: CSV file not found at {csv_file_path}")
        print("Please make sure the file exists and try again.")
        return

    print("🐕 BethePet Food Data Importer (Simplified Version) 🐕")
    print("=" * 60)
    print(f"CSV file: {csv_file_path}")
    print(f"Database: PostgreSQL")
    print("Features: CSV index mapping for recommendation matching")
    print()

    # 데이터 가져오기 실행
    importer = FoodDataImporter(str(csv_file_path))
    importer.import_data(batch_size=50)


if __name__ == "__main__":
    main()
