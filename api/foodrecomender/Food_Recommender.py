import re
from pathlib import Path

import pandas as pd

# 한글-영문 알러지 매핑 (동의어 확장)
ALLERGY_KO_TO_EN = {
    # 단백질 및 육류
    "닭고기": "Chicken",
    "소고기": "Beef",
    "돼지고기": "Pork",
    "양고기": "Lamb",
    "칠면조": "Turkey",
    "오리고기": "Duck",
    "토끼고기": "Rabbit",
    "사슴고기": "Venison",
    "캥거루고기": "Kangaroo",
    "메추라기": "Quail",
    # 해산물
    "연어": "Salmon",
    "참치": "Tuna",
    "흰살생선": "Whitefish",
    "멸치": "Anchovy",
    "고등어": "Mackerel",
    "정어리": "Sardine",
    # 곡물
    "밀": "Wheat",
    "옥수수": "Corn",
    "대두": "Soybeans",
    "쌀": "Rice",
    "보리": "Barley",
    "귀리": "Oats",
    "호밀": "Rye",
    "퀴노아": "Quinoa",
    "기장": "Millet",
    "메밀": "Buckwheat",
    # 유제품
    "우유": "Milk",
    "치즈": "Cheese",
    "요거트": "Yogurt",
    # 첨가물
    "인공색소": "Artificial Colors",
    "인공향료": "Artificial Flavors",
    "BHA/BHT": "BHA",  # BHA와 BHT는 개별적으로 처리
}

# 추가 동의어 매핑
EXTRA_SYNONYMS = {
    "Beef": [
        "ground beef",
        "beef liver",
        "beef heart",
        "beef kidney",
        "beef spleen",
        "beef by-product",
        "beef by product",
        "beef byproduct",
    ],
    "Wheat": ["wheat gluten", "wheat bran", "wheat germ", "wheat protein"],
    "Milk": ["whey", "casein", "dairy", "lactose"],
}

# 추가 동의어 매핑 확장
EXTRA_SYNONYMS.update(
    {
        # 단백질 및 육류
        "Pork": [
            "pork liver",
            "pork meal",
            "pork by-product",
            "ground pork",
            "pork protein",
        ],
        "Lamb": ["lamb meal", "lamb liver", "ground lamb", "lamb by-product"],
        "Turkey": ["turkey meal", "turkey liver", "ground turkey", "turkey by-product"],
        "Duck": ["duck meal", "duck liver", "ground duck", "duck by-product"],
        "Rabbit": ["rabbit meal", "rabbit liver", "ground rabbit", "rabbit by-product"],
        "Venison": ["venison meal", "deer", "venison liver", "ground venison"],
        "Kangaroo": ["kangaroo meal", "kangaroo meat", "ground kangaroo"],
        "Quail": ["quail meal", "ground quail", "quail meat"],
        # 해산물
        "Tuna": ["tuna meal", "tuna fish", "ground tuna"],
        "Whitefish": ["white fish", "whitefish meal", "cod", "haddock", "pollock"],
        "Anchovy": ["anchovy meal", "anchovy fish", "european anchovy"],
        "Mackerel": ["mackerel meal", "mackerel fish", "atlantic mackerel"],
        "Sardine": ["sardine meal", "sardine fish", "pilchard"],
        # 곡물
        "Corn": ["corn meal", "corn gluten", "corn flour", "ground corn", "maize"],
        "Soybeans": ["soy", "soya", "soybean meal", "soy protein", "soy flour"],
        "Rice": ["rice flour", "rice bran", "brown rice", "white rice", "rice protein"],
        "Barley": ["barley flour", "ground barley", "barley grass", "barley protein"],
        "Oats": ["oat flour", "ground oats", "oat bran", "oat protein", "oat grass"],
        "Rye": ["rye flour", "ground rye", "rye protein", "rye grass"],
        "Quinoa": ["quinoa flour", "ground quinoa", "quinoa protein"],
        "Millet": ["millet flour", "ground millet", "millet protein"],
        "Buckwheat": ["buckwheat flour", "ground buckwheat", "buckwheat protein"],
        # 유제품 (이미 있음)
        # 첨가물
        "Artificial Colors": [
            "red 40",
            "yellow 5",
            "yellow 6",
            "blue 1",
            "artificial coloring",
        ],
        "Artificial Flavors": [
            "artificial flavoring",
            "synthetic flavor",
            "artificial taste",
        ],
        "BHA": ["butylated hydroxyanisole"],
        "BHT": ["butylated hydroxytoluene"],
    }
)


class PetFoodFilter:
    def __init__(self, data_dir: Path = Path("/data")):
        """
        반려동물 사료 필터링 시스템 초기화

        Args:
            data_dir: 데이터 파일이 있는 디렉토리 경로
        """
        self.data_dir = data_dir

        # 사료 데이터 로드 (영양 정보 포함)
        self.food_df = pd.read_csv(data_dir / "dog_food_4500_with_nutrients.csv")

        # 알러지, 질병 매핑 정보 로드
        self.allergy_map = pd.read_csv(data_dir / "allergy_mapping.csv")
        self.disease_map = pd.read_csv(data_dir / "disease_avoid.csv")

        # Ingredients 전처리
        self.food_df["processed"] = self.food_df["Ingredients"].apply(
            self._preprocess_ingredients
        )

        # 연령대 분류 추가
        self.food_df["life_stage"] = self.food_df.apply(self._detect_lifestage, axis=1)

    def _preprocess_ingredients(self, text: str) -> list[str]:
        """Ingredients 컬럼(쉼표 구분 문자열)을 소문자 리스트로 변환"""
        if pd.isna(text):
            return []
        text = re.sub(r"[\(\)\[\]\{\}]", "", text)  # 괄호류 제거
        items = [t.strip().lower() for t in text.split(",") if t.strip()]
        return items

    def _detect_lifestage(self, row) -> str:
        """Product row → 'puppy' | 'adult' | 'senior' | 'all' | 'unknown'"""
        LIFE_KEYWORDS = {
            "puppy": ["puppy", "puppies", "junior", "growth"],
            "senior": ["senior", "mature", "geriatric"],
            "adult": ["adult", "maintenance"],
            "all": ["all life stages", "all-life", "all breed stages"],
        }

        text_blobs = [
            str(row.get("Product Name", "")),
            str(row.get("Url", "")),
            str(row.get("Feeding Rates/Instructions", "")),
            str(row.get("Nutritional Information", "")),
        ]
        blob = " ".join(text_blobs).lower()

        # 1) 명시적 키워드 우선
        for stage, kws in LIFE_KEYWORDS.items():
            for kw in kws:
                if kw in blob:
                    return stage

        # 2) 영양 성분 기반 휴리스틱
        try:
            prot = float(row.get("protein_pct", 0))
            fat = float(row.get("fat_pct", 0))
            fiber = float(row.get("fiber_pct", 0))

            if prot >= 28 and fat >= 18:
                return "puppy"
            if prot <= 24 and fat <= 12 and fiber >= 6:
                return "senior"
        except (ValueError, TypeError):
            pass

        return "adult"  # 기본값

    def filter_by_life_stage(self, stage: str) -> pd.DataFrame:
        """
        연령대별 사료 필터링

        Args:
            stage: 'puppy', 'adult', 'senior', 'all' 중 하나

        Returns:
            필터링된 DataFrame
        """
        if stage not in ["puppy", "adult", "senior", "all"]:
            raise ValueError(
                "Invalid life stage. Must be one of: puppy, adult, senior, all"
            )

        filtered = self.food_df[
            (self.food_df["life_stage"] == stage)
            | (self.food_df["life_stage"] == "all")  # all life stages는 항상 포함
        ]
        return filtered.reset_index(drop=True)

    def filter_by_allergies(
        self, allergies: list[str], base_df: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        알러지 성분 기반 필터링

        Args:
            allergies: 한글 알러지 성분 리스트 (예: ["닭고기", "소고기"])
            base_df: 기준 데이터프레임 (None인 경우 self.food_df 사용)

        Returns:
            필터링된 DataFrame
        """
        if base_df is None:
            base_df = self.food_df

        excluded, patterns = self._build_exclude_set(allergies, [])
        return self._hard_filter(base_df, excluded, patterns)

    def filter_by_disease(self, disease: str) -> pd.DataFrame:
        """
        질병 기반 영양 성분 필터링

        Args:
            disease: 질병명 (예: "Obesity", "Kidney Disease")

        Returns:
            필터링된 DataFrame
        """
        disease_filter = DiseaseNutrientFilter()
        return disease_filter.filter_by_disease(self.food_df, disease)

    def filter_by_allergies_and_disease(
        self, allergies: list[str], disease: str
    ) -> pd.DataFrame:
        """
        알러지와 질병 모두 고려한 필터링

        Args:
            allergies: 한글 알러지 성분 리스트
            disease: 질병명

        Returns:
            필터링된 DataFrame
        """
        # 1. 알러지 필터링
        filtered_df = self.filter_by_allergies(allergies)

        # 2. 영양 정보와 병합 (인덱스 기준으로 병합)
        filtered_with_nutrients = pd.merge(
            filtered_df,
            self.food_df,
            left_index=True,
            right_index=True,
            how="inner",
        )

        # 3. 질병 기반 필터링
        disease_filter = DiseaseNutrientFilter()
        return disease_filter.filter_by_disease(filtered_with_nutrients, disease)

    def filter_by_allergies_and_disease_and_life_stage(
        self, allergies: list[str], disease: str, life_stage: str
    ) -> pd.DataFrame:
        """
        알러지, 질병, 연령대를 모두 고려한 필터링

        Args:
            allergies: 한글 알러지 성분 리스트
            disease: 질병명
            life_stage: 연령대 ('puppy', 'adult', 'senior', 'all')

        Returns:
            필터링된 DataFrame
        """
        # 0. 영양 정보가 있는 사료만 선택
        filtered_df = self.food_df.dropna(
            subset=["protein_pct", "fat_pct", "fiber_pct", "moisture_pct"]
        )

        # 0-1. 주식용 사료만 선택 (보충제/간식 제외)
        # 제외할 키워드
        exclude_keywords = [
            "bone broth",
            "topper",
            "treats",
            "supplement",
            "seasoning",
            "sprinkles",
            "nothing but",
            "booster",
            "mixer",
            "mix-in",
            "mix in",
            "topping",
            "appetizer",
            "treat",
            "snack",
            "jerky",
            "chew",
            "biscuit",
            "cookie",
            "dental",
        ]

        # 포함해야 할 키워드 (최소 하나)
        include_keywords = ["dog food", "puppy food", "adult food", "senior food"]

        # 1) 제외 키워드가 포함된 제품 제거
        for keyword in exclude_keywords:
            filtered_df = filtered_df[
                ~filtered_df["Product name"].str.lower().str.contains(keyword, na=False)
            ]

        # 2) 포함 키워드가 하나라도 있는 제품만 선택
        include_mask = (
            filtered_df["Product name"]
            .str.lower()
            .str.contains("|".join(include_keywords), na=False)
        )
        filtered_df = filtered_df[include_mask]

        # 1. 알러지 필터링
        if allergies:
            filtered_df = self.filter_by_allergies(allergies, base_df=filtered_df)

        # 2. 연령대 필터링
        filtered_df = filtered_df[
            (filtered_df["life_stage"] == life_stage)
            | (filtered_df["life_stage"] == "all")
        ]

        # 3. 질병 기반 필터링
        if disease:
            disease_filter = DiseaseNutrientFilter()
            filtered_df = disease_filter.filter_by_disease(filtered_df, disease)

            # 질병 기준에 따라 정렬
            if disease == "Obesity":
                # 비만: 단백질 높은 순, 지방 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["protein_pct", "fat_pct", "Price"],
                    ascending=[False, True, True],
                )
            elif disease == "Kidney Disease":
                # 신장질환: 인 낮은 순, 단백질 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["phosphorus_pct", "protein_pct", "Price"]
                )
            elif disease == "Liver Disease":
                # 간질환: 단백질 낮은 순(but 양질), 지방 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["fat_pct", "protein_pct", "Price"]
                )
            elif disease == "Pancreatitis":
                # 췌장염: 지방 낮은 순, 섬유질 높은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["fat_pct", "fiber_pct", "Price"], ascending=[True, False, True]
                )
            elif disease == "Heart Disease":
                # 심장질환: 나트륨 낮은 순, 지방 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["sodium_pct", "fat_pct", "Price"]
                )
            elif disease == "Diabetes":
                # 당뇨병: 섬유질 높은 순, 지방 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["fiber_pct", "fat_pct", "Price"], ascending=[False, True, True]
                )
            elif disease == "Food Allergies":
                # 식품 알레르기: 오메가3 높은 순, 단백질 높은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["omega_3_pct", "protein_pct", "Price"],
                    ascending=[False, False, True],
                )
            elif disease == "Urinary Stones":
                # 요로결석: 수분 높은 순, 인 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["moisture_pct", "phosphorus_pct", "Price"],
                    ascending=[False, True, True],
                )
            elif disease == "Skin Conditions":
                # 피부질환: 오메가3 데이터 있는 것 우선, 그 다음 오메가3 높은 순, 오메가6/3 비율 낮은 순
                filtered_df["has_omega3"] = ~filtered_df["omega_3_pct"].isna()
                filtered_df["omega_ratio"] = (
                    filtered_df["omega_6_pct"] / filtered_df["omega_3_pct"]
                )
                filtered_df = filtered_df.sort_values(
                    by=["has_omega3", "omega_3_pct", "omega_ratio", "Price"],
                    ascending=[False, False, True, True],
                )
                filtered_df = filtered_df.drop(["has_omega3", "omega_ratio"], axis=1)
            elif disease == "Joint Disease":
                # 관절질환: 오메가3 데이터 있는 것 우선, 그 다음 오메가3 높은 순, 지방 낮은 순
                filtered_df["has_omega3"] = ~filtered_df["omega_3_pct"].isna()
                filtered_df = filtered_df.sort_values(
                    by=["has_omega3", "omega_3_pct", "fat_pct", "Price"],
                    ascending=[False, False, True, True],
                )
                filtered_df = filtered_df.drop("has_omega3", axis=1)
            elif disease == "IBD":
                # 염증성 장질환: 섬유질 낮은 순, 지방 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["fiber_pct", "fat_pct", "Price"]
                )
            elif disease == "Cancer":
                # 암: 오메가3 데이터 있는 것 우선, 그 다음 단백질 높은 순, 지방 높은 순, 오메가3 높은 순
                filtered_df["has_omega3"] = ~filtered_df["omega_3_pct"].isna()
                filtered_df = filtered_df.sort_values(
                    by=["has_omega3", "protein_pct", "fat_pct", "omega_3_pct", "Price"],
                    ascending=[False, False, False, False, True],
                )
                filtered_df = filtered_df.drop("has_omega3", axis=1)
            elif disease == "Hypothyroidism":
                # 갑상선기능저하: 지방 낮은 순, 섬유질 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["fat_pct", "fiber_pct", "Price"]
                )
            elif disease == "Epilepsy":
                # 간질: 지방 높은 순(케토), 단백질 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["fat_pct", "protein_pct", "Price"],
                    ascending=[False, True, True],
                )
            elif disease == "Dental Disease":
                # 치과질환: 수분 낮은 순(건식선호), 칼슘 높은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["moisture_pct", "calcium_pct", "Price"],
                    ascending=[True, False, True],
                )
            elif disease == "Gastrointestinal Issues":
                # 위장관 질환: 지방 낮은 순, 섬유질 적정, 단백질 높은 순
                filtered_df = filtered_df.sort_values(
                    by=["fat_pct", "fiber_pct", "protein_pct", "Price"],
                    ascending=[True, True, False, True],
                )
            elif disease == "Anemia":
                # 빈혈: 단백질 높은 순, 지방 높은 순(에너지), 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["protein_pct", "fat_pct", "Price"],
                    ascending=[False, False, True],
                )
            elif disease == "Allergic Dermatitis":
                # 알레르기성 피부염: 오메가3 데이터 있는 것 우선, 그 다음 오메가3 높은 순, 오메가6 낮은 순
                filtered_df["has_omega3"] = ~filtered_df["omega_3_pct"].isna()
                filtered_df = filtered_df.sort_values(
                    by=["has_omega3", "omega_3_pct", "omega_6_pct", "Price"],
                    ascending=[False, False, True, True],
                )
                filtered_df = filtered_df.drop("has_omega3", axis=1)
            elif disease == "Hyperlipidemia":
                # 고지혈증: 지방 낮은 순, 섬유질 높은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["fat_pct", "fiber_pct", "Price"], ascending=[True, False, True]
                )
            elif disease == "Cushing's Disease":
                # 쿠싱증후군: 나트륨 낮은 순, 지방 낮은 순, 가격 낮은 순
                filtered_df = filtered_df.sort_values(
                    by=["sodium_pct", "fat_pct", "Price"]
                )
        else:
            # 일반적인 경우: 단백질 높은 순, 가격 낮은 순
            filtered_df = filtered_df.sort_values(
                by=["protein_pct", "Price"], ascending=[False, True]
            )

        return filtered_df.reset_index(drop=True)

    def _build_exclude_patterns(self, base_ingredient: str, synonyms: set) -> list[str]:
        """주어진 성분과 동의어들에 대한 정규표현식 패턴 생성"""
        patterns = []
        all_terms = list(synonyms) + [base_ingredient.lower()]

        for term in all_terms:
            patterns.append(rf"\b{re.escape(term)}\b")
            if term in ["beef", "chicken", "pork", "lamb"]:
                patterns.append(rf"\b{re.escape(term)}\s+\w+")
            patterns.append(rf"\b{re.escape(term)}[- ](based|derived|product|source)")

        if base_ingredient in EXTRA_SYNONYMS:
            for extra_syn in EXTRA_SYNONYMS[base_ingredient]:
                patterns.append(rf"\b{re.escape(extra_syn)}\b")

        return patterns

    def _build_exclude_set(
        self, user_allergies: list[str], user_diseases: list[str]
    ) -> tuple[set[str], dict]:
        """제외할 성분들의 집합과 정규표현식 패턴을 반환"""
        ex = set()
        patterns_by_allergy = {}

        # 알러지 처리
        for ko_allergy in user_allergies:
            if ko_allergy in ALLERGY_KO_TO_EN:
                en_allergy = ALLERGY_KO_TO_EN[ko_allergy]

                if ko_allergy == "BHA/BHT":
                    for chemical in ["BHA", "BHT"]:
                        syns = set(
                            self.allergy_map.loc[
                                self.allergy_map["Base Ingredient"] == chemical,
                                "Synonym/Name",
                            ].str.lower()
                        )
                        ex.update(syns)
                        patterns_by_allergy[chemical] = self._build_exclude_patterns(
                            chemical, syns
                        )
                    continue

                syns = set(
                    self.allergy_map.loc[
                        self.allergy_map["Base Ingredient"] == en_allergy,
                        "Synonym/Name",
                    ].str.lower()
                )
                ex.update(syns)
                ex.add(en_allergy.lower())
                patterns_by_allergy[en_allergy] = self._build_exclude_patterns(
                    en_allergy, syns
                )

        # 질병 처리
        for d in user_diseases:
            rows = self.disease_map.loc[
                self.disease_map["Disease"] == d, "Avoid Ingredients (with synonyms)"
            ]
            for row in rows:
                ingredients = [t.strip().lower() for t in row.split(",") if t.strip()]
                ex.update(ingredients)

        return ex, patterns_by_allergy

    def _hard_filter(
        self, food_df: pd.DataFrame, exclude_set: set[str], exclude_patterns: dict
    ) -> pd.DataFrame:
        """정규표현식 패턴을 포함한 필터링"""

        def ok(ing_list):
            ing_text = " , ".join(ing_list)
            if any(ing in exclude_set for ing in ing_list):
                return False
            for patterns in exclude_patterns.values():
                if any(re.search(pattern, ing_text) for pattern in patterns):
                    return False
            return True

        return food_df[food_df["processed"].apply(ok)].reset_index(drop=True)


class DiseaseNutrientFilter:
    def __init__(self):
        self.disease_thresholds = {
            # 신장 질환
            "Kidney Disease": {
                "protein_pct": {"max": 18},  # 단백질 제한
                "phosphorus_pct": {"max": 0.5},  # 인 제한
                "sodium_pct": {"max": 0.3},  # 나트륨 제한
                "moisture_pct": {"min": 60},  # 수분 함량 높게
            },
            # 간 질환
            "Liver Disease": {
                "fat_pct": {"max": 12},  # 지방 제한
                "protein_pct": {"max": 22},  # 양질의 단백질로 제한
                "sodium_pct": {"max": 0.3},  # 나트륨 제한
            },
            # 췌장염
            "Pancreatitis": {
                "fat_pct": {"max": 10},  # 저지방
                "fiber_pct": {"min": 3},  # 섬유질 충분히
                "protein_pct": {"min": 21},  # 양질의 단백질
            },
            # 심장 질환
            "Heart Disease": {
                "sodium_pct": {"max": 0.2},  # 나트륨 엄격 제한
                "fat_pct": {"max": 12},  # 지방 제한
                "protein_pct": {"min": 25},  # 양질의 단백질
            },
            # 당뇨병
            "Diabetes": {
                "fiber_pct": {"min": 5},  # 섬유질 높게
                "fat_pct": {"max": 12},  # 지방 제한
                "protein_pct": {"min": 25},  # 단백질 높게
            },
            # 식품 알레르기
            "Food Allergies": {
                "protein_pct": {"min": 22},  # 대체 단백질원 사용
                "omega_3_pct": {"min": 0.5},  # 항염증 효과
                "omega_6_pct": {"max": 3.0},  # 염증 조절
            },
            # 비만 (건식/습식 구분)
            "Obesity": {
                "dry": {  # 건식 사료 (수분 20% 미만)
                    "fat_pct": {"max": 12},
                    "fiber_pct": {"min": 3},
                    "protein_pct": {"min": 23},
                },
                "wet": {  # 습식 사료 (수분 20% 이상)
                    "fat_pct": {"max": 12},
                    "fiber_pct": {"min": 3},
                    "protein_pct": {"min": 23},
                    "moisture_pct": {"min": 60},
                },
            },
            # 요로결석
            "Urinary Stones": {
                "protein_pct": {"max": 20},  # 단백질 제한
                "phosphorus_pct": {"max": 0.6},  # 인 제한
                "calcium_pct": {"max": 0.9},  # 칼슘 제한
                "moisture_pct": {"min": 65},  # 수분 함량 높게
            },
            # 피부 질환
            "Skin Conditions": {
                "omega_3_pct": {"min": 0.5},  # 오메가3 높게
                "omega_6_pct": {"max": 3.0},  # 오메가6 제한
                "protein_pct": {"min": 23},  # 양질의 단백질
            },
            # 관절 질환
            "Joint Disease": {
                "fat_pct": {"max": 12},  # 체중 부담 줄이기
                "omega_3_pct": {"min": 0.5},  # 항염증 효과
                "calcium_pct": {"max": 1.2},  # 칼슘 과다 제한
            },
            # 염증성 장질환
            "IBD": {
                "fiber_pct": {"max": 3},  # 섬유질 제한
                "fat_pct": {"max": 12},  # 지방 제한
                "protein_pct": {"min": 23},  # 소화가 쉬운 단백질
                "moisture_pct": {"min": 65},  # 수분 함량 높게
            },
            # 암
            "Cancer": {
                "protein_pct": {"min": 25},  # 고단백
                "fat_pct": {"min": 15},  # 에너지 공급
                "omega_3_pct": {"min": 0.5},  # 항염증 효과
            },
            # 갑상선 기능저하증
            "Hypothyroidism": {
                "fat_pct": {"max": 12},  # 지방 제한
                "fiber_pct": {"max": 5},  # 섬유질 제한
                "protein_pct": {"min": 23},  # 양질의 단백질
            },
            # 간질
            "Epilepsy": {
                "fat_pct": {"min": 15},  # 케토제닉 식이
                "protein_pct": {"max": 20},  # 단백질 제한
                "fiber_pct": {"max": 3},  # 섬유질 제한
            },
            # 치과 질환
            "Dental Disease": {
                "moisture_pct": {"max": 10},  # 건식 사료 선호
                "calcium_pct": {"min": 1.0},  # 칼슘 충분히
                "phosphorus_pct": {"min": 0.8},  # 인 충분히
            },
            # 위장관 질환
            "Gastrointestinal Issues": {
                "fat_pct": {"max": 10},  # 저지방
                "fiber_pct": {"min": 3},  # 적당한 섬유질
                "protein_pct": {"min": 23},  # 소화가 쉬운 단백질
                "moisture_pct": {"min": 65},  # 수분 함량 높게
            },
            # 빈혈
            "Anemia": {
                "protein_pct": {"min": 25},  # 고단백
                "fat_pct": {"min": 12},  # 충분한 에너지
                "moisture_pct": {"max": 15},  # 영양 밀도 높게
            },
            # 알레르기성 피부염
            "Allergic Dermatitis": {
                "omega_3_pct": {"min": 0.5},  # 오메가3 높게
                "omega_6_pct": {"max": 3.0},  # 오메가6 제한
                "protein_pct": {"min": 23},  # 저자극성 단백질
            },
            # 고지혈증
            "Hyperlipidemia": {
                "fat_pct": {"max": 8},  # 저지방
                "fiber_pct": {"min": 5},  # 섬유질 높게
                "protein_pct": {"min": 25},  # 양질의 단백질
            },
            # 쿠싱 증후군
            "Cushing's Disease": {
                "fat_pct": {"max": 10},  # 저지방
                "sodium_pct": {"max": 0.2},  # 나트륨 엄격 제한
                "protein_pct": {"min": 23},  # 양질의 단백질
                "moisture_pct": {"min": 65},  # 수분 함량 높게
            },
        }

    def filter_by_disease(self, df: pd.DataFrame, disease: str) -> pd.DataFrame:
        """질병에 따른 영양 기준으로 필터링"""
        if disease not in self.disease_thresholds:
            return df

        filtered_df = df.copy()
        thresholds = self.disease_thresholds[disease]

        # 비만의 경우 건식/습식 구분하여 필터링
        if disease == "Obesity":
            # 건식 사료 필터링
            dry_mask = filtered_df["moisture_pct"] < 20
            dry_df = filtered_df[dry_mask].copy()
            for nutrient, limits in thresholds["dry"].items():
                if "max" in limits:
                    dry_df = dry_df[
                        (dry_df[nutrient].isna()) | (dry_df[nutrient] <= limits["max"])
                    ]
                if "min" in limits:
                    dry_df = dry_df[
                        (dry_df[nutrient].isna()) | (dry_df[nutrient] >= limits["min"])
                    ]

            # 습식 사료 필터링
            wet_mask = filtered_df["moisture_pct"] >= 20
            wet_df = filtered_df[wet_mask].copy()
            for nutrient, limits in thresholds["wet"].items():
                if "max" in limits:
                    wet_df = wet_df[
                        (wet_df[nutrient].isna()) | (wet_df[nutrient] <= limits["max"])
                    ]
                if "min" in limits:
                    wet_df = wet_df[
                        (wet_df[nutrient].isna()) | (wet_df[nutrient] >= limits["min"])
                    ]

            # 건식/습식 결과 합치기
            return pd.concat([dry_df, wet_df]).reset_index(drop=True)

        # 다른 질병의 경우 기존 로직 사용
        for nutrient, limits in thresholds.items():
            if nutrient not in df.columns:
                continue

            if "max" in limits:
                filtered_df = filtered_df[
                    (filtered_df[nutrient].isna())
                    | (filtered_df[nutrient] <= limits["max"])
                ]

            if "min" in limits:
                filtered_df = filtered_df[
                    (filtered_df[nutrient].isna())
                    | (filtered_df[nutrient] >= limits["min"])
                ]

        return filtered_df.reset_index(drop=True)


def filter_obesity(df: pd.DataFrame) -> pd.DataFrame:
    """비만 관리용 사료 필터링 (건식/습식 구분)"""
    # 사료 타입 구분
    dry_food = df[df["moisture_pct"] < 20]
    wet_food = df[df["moisture_pct"] >= 20]

    # 건식사료 필터링
    filtered_dry = dry_food[
        ((dry_food["fat_pct"].isna()) | (dry_food["fat_pct"] <= 10))
        & ((dry_food["fiber_pct"].isna()) | (dry_food["fiber_pct"] >= 5))
        & ((dry_food["protein_pct"].isna()) | (dry_food["protein_pct"] >= 25))
        & ((dry_food["moisture_pct"].isna()) | (dry_food["moisture_pct"] >= 8))
    ]

    # 습식사료 필터링
    filtered_wet = wet_food[
        ((wet_food["fat_pct"].isna()) | (wet_food["fat_pct"] <= 10))
        & ((wet_food["fiber_pct"].isna()) | (wet_food["fiber_pct"] >= 5))
        & ((wet_food["protein_pct"].isna()) | (wet_food["protein_pct"] >= 25))
        & ((wet_food["moisture_pct"].isna()) | (wet_food["moisture_pct"] >= 65))
    ]

    return pd.concat([filtered_dry, filtered_wet])


class DiseaseComboOptimizer:
    def __init__(self):
        # 질병 간의 상호작용 가중치 정의
        self.disease_interactions = {
            ("Obesity", "Joint Disease"): {
                "protein_pct": 1.2,  # 단백질 중요도 증가
                "fat_pct": 0.7,  # 지방 제한 강화
                "fiber_pct": 1.1,  # 섬유질 중요도 약간 증가
            },
            ("Diabetes", "Heart Disease"): {
                "sodium_pct": 0.6,  # 나트륨 제한 강화
                "fat_pct": 0.8,  # 지방 제한 강화
                "fiber_pct": 1.3,  # 섬유질 중요도 증가
            },
            ("Kidney Disease", "Heart Disease"): {
                "protein_pct": 0.6,  # 단백질 제한 강화
                "sodium_pct": 0.5,  # 나트륨 제한 강화
                "phosphorus_pct": 0.7,  # 인 제한 강화
            },
            ("Skin Conditions", "Food Allergies"): {
                "omega_3_pct": 1.5,  # 오메가3 중요도 증가
                "omega_6_pct": 0.7,  # 오메가6 제한 강화
            },
        }

        # 질병별 영양소 중요도 점수
        self.nutrient_importance = {
            "Obesity": {"protein_pct": 0.3, "fat_pct": -0.4, "fiber_pct": 0.2},
            "Joint Disease": {"omega_3_pct": 0.4, "fat_pct": -0.2},
            "Diabetes": {"fiber_pct": 0.4, "fat_pct": -0.3},
            "Heart Disease": {"sodium_pct": -0.4, "fat_pct": -0.3},
            "Kidney Disease": {"protein_pct": -0.4, "phosphorus_pct": -0.3},
            "Skin Conditions": {"omega_3_pct": 0.4, "omega_6_pct": -0.2},
            "Food Allergies": {"omega_3_pct": 0.3, "protein_pct": 0.2},
        }

    def calculate_food_score(self, food_row: pd.Series, diseases: list[str]) -> float:
        """
        주어진 사료의 여러 질병에 대한 적합도 점수 계산

        Args:
            food_row: 사료 데이터 (Series)
            diseases: 질병 리스트

        Returns:
            적합도 점수 (높을수록 좋음)
        """
        score = 0.0

        # 1. 각 질병별 기본 점수 계산
        for disease in diseases:
            if disease in self.nutrient_importance:
                for nutrient, importance in self.nutrient_importance[disease].items():
                    if not pd.isna(food_row.get(nutrient)):
                        score += food_row[nutrient] * importance

        # 2. 질병 조합에 대한 보정
        for i in range(len(diseases)):
            for j in range(i + 1, len(diseases)):
                disease_pair = (diseases[i], diseases[j])
                if disease_pair in self.disease_interactions:
                    interaction = self.disease_interactions[disease_pair]
                    for nutrient, weight in interaction.items():
                        if not pd.isna(food_row.get(nutrient)):
                            score *= weight

        # 3. 가격 고려 (가격이 낮을수록 약간의 보너스)
        if not pd.isna(food_row.get("Price")):
            price_score = 1 / (1 + food_row["Price"] / 100)  # 정규화된 가격 점수
            score += price_score * 0.1  # 가격의 영향력은 10%로 제한

        return score

    def optimize_food_selection(
        self, df: pd.DataFrame, diseases: list[str], top_n: int = 10
    ) -> pd.DataFrame:
        """
        여러 질병을 고려한 최적의 사료 선택

        Args:
            df: 필터링된 사료 DataFrame
            diseases: 질병 리스트
            top_n: 반환할 상위 사료 개수

        Returns:
            점수순으로 정렬된 상위 n개 사료
        """
        # 각 사료별 점수 계산
        df["combo_score"] = df.apply(
            lambda row: self.calculate_food_score(row, diseases), axis=1
        )

        # 점수순 정렬
        result = df.sort_values("combo_score", ascending=False).head(top_n)

        # 점수 컬럼 제거
        result = result.drop("combo_score", axis=1)

        return result


class ScoreBasedOptimizer:
    def __init__(self):
        self.feature_columns = [
            "protein_pct",
            "fat_pct",
            "fiber_pct",
            "moisture_pct",
            "omega_3_pct",
            "omega_6_pct",
            "sodium_pct",
            "phosphorus_pct",
        ]

        # 반려동물 특성
        self.pet_features = [
            "age_months",  # 나이(개월)
            "weight_kg",  # 체중(kg)
            "activity_level",  # 활동량 (1-5)
            "is_neutered",  # 중성화 여부
        ]

        # 조건 특성
        self.condition_features = [
            "has_obesity",
            "has_joint_disease",
            "has_diabetes",
            "has_heart_disease",
            "has_kidney_disease",
            "has_skin_condition",
            "has_food_allergies",
        ]

        # 알러지 특성
        self.allergy_features = [
            "allergic_to_chicken",
            "allergic_to_beef",
            "allergic_to_wheat",
            "allergic_to_soy",
        ]

        # 나이별 기본 영양소 요구량 (예시)
        self.age_based_requirements = {
            "puppy": {
                "protein_pct": {"min": 28, "optimal": 30, "max": 35},
                "fat_pct": {"min": 15, "optimal": 18, "max": 20},
                "calcium_phosphorus_ratio": {"min": 1.1, "optimal": 1.2, "max": 1.4},
            },
            "adult": {
                "protein_pct": {"min": 18, "optimal": 25, "max": 30},
                "fat_pct": {"min": 10, "optimal": 15, "max": 18},
                "calcium_phosphorus_ratio": {"min": 1.0, "optimal": 1.2, "max": 1.3},
            },
            "senior": {
                "protein_pct": {"min": 20, "optimal": 23, "max": 27},
                "fat_pct": {"min": 8, "optimal": 12, "max": 15},
                "calcium_phosphorus_ratio": {"min": 1.0, "optimal": 1.1, "max": 1.2},
            },
        }

        # 질병 조합별 영양소 보정 계수
        self.disease_combo_adjustments = {
            ("Obesity", "Joint Disease"): {
                "protein_pct": {"factor": 1.1, "max_adjustment": 2},
                "fat_pct": {"factor": 0.8, "max_adjustment": -3},
                "fiber_pct": {"factor": 1.2, "max_adjustment": 3},
            },
            ("Diabetes", "Heart Disease"): {
                "fiber_pct": {"factor": 1.3, "max_adjustment": 4},
                "sodium_pct": {"factor": 0.6, "max_adjustment": -2},
                "fat_pct": {"factor": 0.8, "max_adjustment": -2},
            },
        }

        # 질병별 필수 제약조건 추가
        self.disease_constraints = {
            "Diabetes": {
                "fat_pct": {"max": 12},  # 지방 상한
                "fiber_pct": {"min": 5},  # 섬유질 하한
            },
            "Heart Disease": {
                "sodium_pct": {"max": 0.3},  # 나트륨 상한
                "fat_pct": {"max": 12},  # 지방 상한
            },
            "Obesity": {
                "fat_pct": {"max": 10},  # 지방 상한
                "fiber_pct": {"min": 5},  # 섬유질 하한
            },
            "Joint Disease": {
                "protein_pct": {"min": 23},  # 단백질 하한
            },
        }

        # 실시간 데이터 가중치
        self.realtime_weights = {
            "weight_trend": 0.3,  # 체중 변화 추세
            "food_intake": 0.2,  # 사료 섭취량
            "activity": 0.2,  # 산책/활동량
            "water_intake": 0.1,  # 수분 섭취량
            "feedback_score": 0.2,  # 사용자 피드백
        }

        # 실시간 데이터 임계값
        self.trend_thresholds = {
            "weight_gain_pct": 0.05,  # 한달 5% 이상 체중증가는 경고
            "weight_loss_pct": 0.05,  # 한달 5% 이상 체중감소도 경고
            "low_food_intake": 0.8,  # 권장량 대비 80% 미만 섭취
            "high_food_intake": 1.2,  # 권장량 대비 120% 초과 섭취
            "low_activity": 0.7,  # 평균 대비 70% 미만 활동량
            "low_water": 0.8,  # 권장량 대비 80% 미만 수분섭취
            "high_water": 1.5,  # 권장량 대비 150% 초과 수분섭취 (다뇨증 의심)
        }

    def check_constraints(self, food_row: pd.Series, pet_data: dict) -> bool:
        """
        질병별 필수 제약조건 확인

        Args:
            food_row: 사료 데이터
            pet_data: 반려동물 정보

        Returns:
            제약조건 만족 여부
        """
        # 반려동물의 질병 확인
        diseases = [
            d.replace("has_", "")
            for d, v in pet_data.items()
            if d.startswith("has_") and v
        ]

        # 각 질병별 제약조건 확인
        for disease in diseases:
            if disease in self.disease_constraints:
                constraints = self.disease_constraints[disease]
                for nutrient, limits in constraints.items():
                    if not pd.isna(food_row.get(nutrient)):
                        if "max" in limits and food_row[nutrient] > limits["max"]:
                            return False
                        if "min" in limits and food_row[nutrient] < limits["min"]:
                            return False

        return True

    def analyze_weight_trend(self, weight_history: list[dict]) -> dict:
        """
        체중 변화 추세 분석

        Args:
            weight_history: [{"date": "2024-03-01", "weight": 12.5}, ...]

        Returns:
            분석 결과
        """
        if len(weight_history) < 2:
            return {"trend": "stable", "change_rate": 0}

        # 최근 한달 체중 변화율 계산
        recent = sorted(weight_history, key=lambda x: x["date"])[-30:]
        if len(recent) >= 2:
            # weight 또는 weight_kg 키 지원
            start_weight = recent[0].get("weight", recent[0].get("weight_kg", 0))
            end_weight = recent[-1].get("weight", recent[-1].get("weight_kg", 0))
            change_rate = (end_weight - start_weight) / start_weight

            if change_rate > self.trend_thresholds["weight_gain_pct"]:
                return {"trend": "gaining", "change_rate": change_rate}
            elif change_rate < -self.trend_thresholds["weight_loss_pct"]:
                return {"trend": "losing", "change_rate": change_rate}

        return {"trend": "stable", "change_rate": 0}

    def analyze_food_intake(
        self, intake_history: list[dict], recommended: float
    ) -> dict:
        """
        사료 섭취 패턴 분석

        Args:
            intake_history: [{"date": "2024-03-01", "amount": 200}, ...]
            recommended: 일일 권장 섭취량(g)

        Returns:
            분석 결과
        """
        if not intake_history:
            return {"pattern": "normal", "avg_intake_ratio": 1.0}

        # 최근 일주일 평균 섭취율
        recent = sorted(intake_history, key=lambda x: x["date"])[-7:]
        avg_intake = sum(
            day.get("amount", day.get("intake_g", 0)) for day in recent
        ) / len(recent)
        intake_ratio = avg_intake / recommended

        if intake_ratio < self.trend_thresholds["low_food_intake"]:
            return {"pattern": "low_intake", "avg_intake_ratio": intake_ratio}
        elif intake_ratio > self.trend_thresholds["high_food_intake"]:
            return {"pattern": "high_intake", "avg_intake_ratio": intake_ratio}

        return {"pattern": "normal", "avg_intake_ratio": intake_ratio}

    def analyze_activity(self, activity_history: list[dict]) -> dict:
        """
        활동량 패턴 분석

        Args:
            activity_history: [{"date": "2024-03-01", "minutes": 60, "intensity": "moderate"}, ...]

        Returns:
            분석 결과
        """
        if not activity_history:
            return {"level": "normal", "activity_ratio": 1.0}

        # 강도별 가중치
        intensity_weights = {"low": 0.5, "moderate": 1.0, "high": 1.5}

        # 최근 일주일 활동량
        recent = sorted(activity_history, key=lambda x: x["date"])[-7:]
        weighted_activity = sum(
            day["minutes"]
            * intensity_weights.get(day.get("intensity", "moderate"), 1.0)
            for day in recent
        ) / len(recent)

        # 기준 활동량 (예: 중강도 60분)
        baseline = 60
        activity_ratio = weighted_activity / baseline

        if activity_ratio < self.trend_thresholds["low_activity"]:
            return {"level": "low", "activity_ratio": activity_ratio}
        elif activity_ratio > 1.3:  # 30% 이상 활동적
            return {"level": "high", "activity_ratio": activity_ratio}

        return {"level": "normal", "activity_ratio": activity_ratio}

    def analyze_water_intake(
        self, water_history: list[dict], recommended_daily_ml: float
    ) -> dict:
        """
        수분 섭취 패턴 분석

        Args:
            water_history: [{"date": "2024-03-01", "ml_consumed": 750}, ...]
            recommended_daily_ml: 일일 권장 수분 섭취량 (ml)

        Returns:
            분석 결과 {"status": "low" | "adequate" | "high", "avg_intake_ratio": float}
        """
        if not water_history or recommended_daily_ml <= 0:
            return {"status": "adequate", "avg_intake_ratio": 1.0}

        # 최근 3일 평균 섭취량
        recent_days = 3
        recent_history = sorted(water_history, key=lambda x: x["date"])[-recent_days:]
        if not recent_history:
            return {"status": "adequate", "avg_intake_ratio": 1.0}

        avg_intake = sum(
            day.get("ml_consumed", day.get("ml", 0)) for day in recent_history
        ) / len(recent_history)
        intake_ratio = avg_intake / recommended_daily_ml

        if intake_ratio < self.trend_thresholds["low_water"]:
            return {"status": "low", "avg_intake_ratio": intake_ratio}
        elif intake_ratio > self.trend_thresholds["high_water"]:
            return {"status": "high", "avg_intake_ratio": intake_ratio}

        return {"status": "adequate", "avg_intake_ratio": intake_ratio}

    def adjust_nutrients_by_realtime_data(
        self, optimal_nutrients: dict, realtime_data: dict
    ) -> dict:
        """
        실시간 데이터 기반으로 영양소 요구량 조정

        Args:
            optimal_nutrients: 기본 영양소 요구량
            realtime_data: 실시간 데이터 분석 결과

        Returns:
            조정된 영양소 요구량
        """
        adjusted = optimal_nutrients.copy()

        # 1. 체중 변화에 따른 조정
        weight_trend = realtime_data.get("weight_trend", {})
        if weight_trend.get("trend") == "gaining":
            # 체중 증가 시 지방 감소, 단백질 증가
            adjusted["fat_pct"] *= 0.9
            adjusted["protein_pct"] *= 1.1
        elif weight_trend.get("trend") == "losing":
            # 체중 감소 시 전반적인 영양소 증가
            for nutrient in adjusted:
                adjusted[nutrient] *= 1.1

        # 2. 사료 섭취 패턴에 따른 조정
        food_pattern = realtime_data.get("food_intake", {})
        if food_pattern.get("pattern") == "low_intake":
            # 저조한 섭취 시 기호성 고려
            adjusted["fat_pct"] *= 1.1
        elif food_pattern.get("pattern") == "high_intake":
            # 과다 섭취 시 열량 감소
            adjusted["fat_pct"] *= 0.9

        # 3. 활동량에 따른 조정
        activity = realtime_data.get("activity", {})
        if activity.get("level") == "high":
            # 높은 활동량 시 단백질과 지방 증가
            adjusted["protein_pct"] *= 1.2
            adjusted["fat_pct"] *= 1.1
        elif activity.get("level") == "low":
            # 낮은 활동량 시 열량 감소
            adjusted["fat_pct"] *= 0.9

        # 4. 수분 섭취에 따른 조정 (필요시 추가 확장)
        # 예: 만약 water_intake_analysis 결과가 "low"이고, 현재 고려중인 사료가 건식이라면
        # 이 부분에 추가적인 로직을 넣거나, 점수 계산 시 반영할 수 있습니다.
        # 현재는 직접적인 영양소 조정을 수행하지 않지만, 분석 결과는 활용 가능합니다.
        water_analysis = realtime_data.get("water_intake_analysis", {})
        if water_analysis.get("status") == "low":
            # print("경고: 수분 섭취량이 낮습니다.") # 로깅 또는 사용자 알림용
            pass
        elif water_analysis.get("status") == "high":
            # print("경고: 수분 섭취량이 과도합니다. (다뇨증 가능성)") # 로깅 또는 사용자 알림용
            pass

        return adjusted

    def calculate_feedback_score(self, feedback_history: list[dict]) -> float:
        """
        사용자 피드백 점수 계산

        Args:
            feedback_history: [
                {
                    "date": "2024-03-01",
                    "food_id": "123",
                    "rating": 4.5,
                    "symptoms": ["diarrhea", "vomiting"],
                    "satisfaction": {"taste": 5, "digestion": 3}
                },
                ...
            ]

        Returns:
            피드백 점수 (0-1)
        """
        if not feedback_history:
            return 0.5  # 기본값

        # 최근 피드백에 더 높은 가중치 부여
        recent = sorted(feedback_history, key=lambda x: x["date"])[-5:]  # 최근 5개
        weights = [0.1, 0.15, 0.2, 0.25, 0.3]  # 가중치 합 1

        score = 0
        for feedback, weight in zip(recent, weights):
            # 기본 평점 (0-5 → 0-1)
            base_score = feedback["rating"] / 5

            # 증상에 따른 감점
            symptom_penalty = len(feedback["symptoms"]) * 0.1

            # 만족도 점수
            satisfaction_score = sum(feedback["satisfaction"].values()) / (
                len(feedback["satisfaction"]) * 5
            )

            # 종합 점수
            combined_score = (base_score + satisfaction_score) / 2 - symptom_penalty
            score += combined_score * weight

        return max(0, min(1, score))  # 0-1 범위로 제한

    def optimize_food_selection(
        self,
        df: pd.DataFrame,
        pet_data: dict,
        realtime_data: dict = None,
        feedback_history: list = None,
        top_n: int = 10,
    ) -> pd.DataFrame:
        """
        실시간 데이터와 피드백을 반영한 사료 추천

        Args:
            df: 사료 DataFrame
            pet_data: 반려동물 정보
            realtime_data: 실시간 측정 데이터
            feedback_history: 피드백 이력
            top_n: 추천할 사료 수

        Returns:
            추천 사료 목록
        """
        # 1. 제약조건 필터링
        df = df[df.apply(lambda row: self.check_constraints(row, pet_data), axis=1)]

        if len(df) == 0:
            print(
                "경고: 모든 제약조건을 만족하는 사료가 없습니다. 제약조건을 완화합니다."
            )
            return self.optimize_food_selection_relaxed(df, pet_data, top_n)

        # 2. 기본 영양소 요구량 계산
        optimal_nutrients = self.calculate_optimal_nutrients(pet_data)

        # 3. 실시간 데이터 반영
        if realtime_data:
            # 실시간 데이터 분석
            analyzed_data = {}
            if "weight_history" in realtime_data:
                analyzed_data["weight_trend"] = self.analyze_weight_trend(
                    realtime_data["weight_history"]
                )
            if "intake_history" in realtime_data:
                analyzed_data["food_intake"] = self.analyze_food_intake(
                    realtime_data["intake_history"], 150
                )  # 기본 권장량 150g
            if "activity_history" in realtime_data:
                analyzed_data["activity"] = self.analyze_activity(
                    realtime_data["activity_history"]
                )
            if "water_history" in realtime_data:
                analyzed_data["water_intake"] = self.analyze_water_intake(
                    realtime_data["water_history"], 300
                )  # 기본 권장량 300ml

            optimal_nutrients = self.adjust_nutrients_by_realtime_data(
                optimal_nutrients, analyzed_data
            )

        # 4. 각 사료별 점수 계산
        df["ml_score"] = df.apply(
            lambda row: self.calculate_food_score(row, optimal_nutrients), axis=1
        )

        # 5. 피드백 점수 반영
        if feedback_history:
            feedback_score = self.calculate_feedback_score(feedback_history)
            df["ml_score"] *= 1 + feedback_score

        # 6. 점수순 정렬
        result = df.sort_values("ml_score", ascending=False).head(top_n)
        result = result.drop("ml_score", axis=1)

        return result

    def optimize_food_selection_relaxed(
        self, df: pd.DataFrame, pet_data: dict, top_n: int = 10
    ) -> pd.DataFrame:
        """
        제약조건을 완화하여 사료 추천
        """
        # 제약조건 완화 (예: 20% 완화)
        relaxation_factor = 1.2

        for disease in self.disease_constraints:
            for nutrient in self.disease_constraints[disease]:
                if "max" in self.disease_constraints[disease][nutrient]:
                    self.disease_constraints[disease][nutrient][
                        "max"
                    ] *= relaxation_factor
                if "min" in self.disease_constraints[disease][nutrient]:
                    self.disease_constraints[disease][nutrient][
                        "min"
                    ] /= relaxation_factor

        # 완화된 제약조건으로 다시 시도
        return self.optimize_food_selection(df, pet_data, top_n)

    def calculate_optimal_nutrients(self, pet_data: dict) -> dict:
        """
        반려동물 데이터 기반으로 최적 영양소 비율 계산

        Args:
            pet_data: 반려동물 정보 (나이, 체중, 질병, 알러지 등)

        Returns:
            최적 영양소 비율
        """
        # 1. 나이 기반 기본 요구량 설정
        age_months = pet_data["age_months"]
        if age_months < 12:
            base_requirements = self.age_based_requirements["puppy"]
        elif age_months > 84:  # 7년 이상
            base_requirements = self.age_based_requirements["senior"]
        else:
            base_requirements = self.age_based_requirements["adult"]

        # 2. 체중에 따른 조정
        weight_factor = min(max(pet_data["weight_kg"] / 20, 0.8), 1.2)  # 20kg 기준

        # 3. 활동량에 따른 조정
        activity_level = pet_data.get("activity_level", "medium")
        activity_mapping = {"low": 1, "medium": 2, "high": 3}
        activity_factor = activity_mapping.get(activity_level, 2) / 3  # 3이 보통

        # 4. 질병 조합 조정
        diseases = [d for d in self.condition_features if pet_data.get(d)]
        disease_adjustments = {}

        for i in range(len(diseases)):
            for j in range(i + 1, len(diseases)):
                combo = (diseases[i], diseases[j])
                if combo in self.disease_combo_adjustments:
                    for nutrient, adj in self.disease_combo_adjustments[combo].items():
                        if nutrient not in disease_adjustments:
                            disease_adjustments[nutrient] = 1.0
                        disease_adjustments[nutrient] *= adj["factor"]

        # 5. 최종 영양소 요구량 계산
        optimal_nutrients = {}
        for nutrient, base in base_requirements.items():
            optimal = base["optimal"]
            # 체중 조정
            optimal *= weight_factor
            # 활동량 조정
            optimal *= activity_factor
            # 질병 조정
            if nutrient in disease_adjustments:
                adj_factor = disease_adjustments[nutrient]
                max_adj = self.disease_combo_adjustments[combo][nutrient][
                    "max_adjustment"
                ]
                optimal *= min(max(adj_factor, 1 + max_adj), 1 - max_adj)

            optimal_nutrients[nutrient] = optimal

        return optimal_nutrients

    def calculate_food_score(
        self, food_row: pd.Series, optimal_nutrients: dict
    ) -> float:
        """
        사료의 최적 영양소 기준 점수 계산

        Args:
            food_row: 사료 데이터
            optimal_nutrients: 최적 영양소 비율

        Returns:
            적합도 점수
        """
        score = 0.0

        for nutrient, optimal in optimal_nutrients.items():
            if not pd.isna(food_row.get(nutrient)):
                # 실제값과 최적값의 차이에 따른 감점
                diff = abs(food_row[nutrient] - optimal)
                score -= (diff**2) * 0.1  # 제곱 페널티

        # 가격 고려
        if not pd.isna(food_row.get("Price")):
            price_score = 1 / (1 + food_row["Price"] / 100)
            score += price_score * 0.1

        return score

    def calculate_ml_confidence(
        self, realtime_data: dict = None, feedback_history: list = None
    ) -> float:
        """스코어링 신뢰도 점수 계산"""
        confidence = 0.5  # 기본 신뢰도

        if realtime_data:
            # 실시간 데이터 완성도 체크
            data_completeness = (
                sum(
                    1
                    for key in [
                        "weight_trend",
                        "food_intake",
                        "activity",
                        "water_intake",
                    ]
                    if key in realtime_data and realtime_data[key]
                )
                / 4
            )
            confidence += data_completeness * 0.3

            # 데이터 품질 체크
            quality_score = 0
            if realtime_data.get("weight_trend", {}).get("trend") != "stable":
                quality_score += 0.1
            if realtime_data.get("food_intake", {}).get("pattern") != "normal":
                quality_score += 0.1
            if realtime_data.get("activity", {}).get("level") != "normal":
                quality_score += 0.1
            confidence += quality_score

        if feedback_history:
            # 피드백 데이터 신뢰도 체크
            recent_feedback = sorted(feedback_history, key=lambda x: x["date"])[-3:]
            if len(recent_feedback) >= 3:  # 최소 3일 이상의 데이터
                avg_rating = sum(f["rating"] for f in recent_feedback) / len(
                    recent_feedback
                )
                confidence += (avg_rating / 5) * 0.2

                # 증상 정보 체크
                if any(f.get("symptoms") for f in recent_feedback):
                    confidence += 0.1

        return min(1.0, confidence)

    def calculate_realtime_score(
        self, food_row: pd.Series, realtime_data: dict
    ) -> float:
        """실시간 데이터 기반 점수 계산"""
        score = 0.0

        if realtime_data:
            weight_trend = realtime_data.get("weight_trend", {})
            food_intake = realtime_data.get("food_intake", {})
            activity = realtime_data.get("activity", {})
            water_intake = realtime_data.get("water_intake", {})

            # 체중 증가 + 높은 섭취량인 경우 저지방 사료 선호
            if (
                weight_trend.get("trend") == "gaining"
                and food_intake.get("pattern") == "high_intake"
            ):
                if food_row["fat_pct"] < 8:  # 지방 기준 더 엄격하게
                    score += 0.5
                elif food_row["fat_pct"] < 10:
                    score += 0.3

            # 낮은 활동량인 경우 저칼로리 사료 선호
            if activity.get("level") == "low":
                if food_row["fat_pct"] < 10 and food_row["protein_pct"] < 25:
                    score += 0.3

            # 수분 섭취량이 낮은 경우 수분 함량 높은 사료 선호
            if water_intake.get("status") == "low":
                if food_row["moisture_pct"] > 60:
                    score += 0.4
                elif food_row["moisture_pct"] > 30:
                    score += 0.2

        return score


class ComprehensiveOptimizer:
    def __init__(self, data_dir: Path = None):
        """
        규칙 기반과 스코어링 기반을 결합
        """
        if data_dir is None:
            # 기본 데이터 디렉토리 설정
            data_dir = Path(__file__).parent / "data"

        self.disease_optimizer = DiseaseComboOptimizer()
        self.score_optimizer = ScoreBasedOptimizer()
        self.pet_filter = PetFoodFilter(data_dir=data_dir)

        # 피드백 데이터 기반 가중치 조정을 위한 임계값
        self.feedback_threshold = {
            "min_feedback_count": 10,  # 최소 피드백 수
            "min_confidence_score": 0.7,  # 스코어링 신뢰도 최소값
        }

        # 실시간 데이터 신뢰도 가중치
        self.realtime_weights = {
            "weight_trend": 0.3,
            "food_intake": 0.2,
            "activity": 0.2,
            "water_intake": 0.1,
            "feedback": 0.2,
        }

        # 영양소 중요도 초기화
        self.nutrient_importance = {
            "protein_pct": 1.0,
            "fat_pct": 1.0,
            "fiber_pct": 1.0,
            "moisture_pct": 1.0,
            "omega_3_pct": 1.0,
            "omega_6_pct": 1.0,
            "glucosamine_pct": 1.0,
            "chondroitin_pct": 1.0,
        }

        # 체중 기반 필터링 추가
        self.weight_categories = {
            "small": (0, 10),  # 10kg 미만
            "medium": (10, 25),  # 10-25kg
            "large": (25, 45),  # 25kg 이상
        }

        # 견종별 특성 고려
        self.breed_characteristics = {
            "small_breed": {
                "puppy": {
                    "protein_min": 28,  # 성장기에는 더 높은 단백질
                    "protein_optimal": 32,
                    "fat_min": 17,  # 성장기에는 더 높은 지방
                    "fat_optimal": 20,
                },
                "adult": {
                    "protein_min": 25,
                    "protein_optimal": 30,
                    "fat_min": 15,
                    "fat_optimal": 20,
                },
                "senior": {
                    "protein_min": 22,
                    "protein_optimal": 27,
                    "fat_min": 12,
                    "fat_optimal": 17,
                },
            },
            "large_breed": {
                "puppy": {
                    "protein_min": 23,  # 대형견 퍼피는 과도한 성장 방지
                    "protein_optimal": 25,
                    "fat_min": 12,  # 지방도 조절하여 급성장 방지
                    "fat_optimal": 15,
                    "calcium_phosphorus_ratio": (1.2, 1.4),  # 골격 발달에 중요
                    "glucosamine_min": 500,  # mg/kg
                },
                "adult": {
                    "protein_min": 23,
                    "protein_optimal": 25,
                    "fat_min": 12,
                    "fat_optimal": 15,
                    "calcium_phosphorus_ratio": (1.2, 1.4),
                    "glucosamine_min": 500,
                },
                "senior": {
                    "protein_min": 20,  # 노령 대형견은 관절 부담 고려
                    "protein_optimal": 23,
                    "fat_min": 10,
                    "fat_optimal": 13,
                    "calcium_phosphorus_ratio": (1.1, 1.3),
                    "glucosamine_min": 750,  # 관절 보호를 위해 증가
                },
            },
        }

    def filter_by_size(
        self, df: pd.DataFrame, weight_kg: float, life_stage: str = "adult"
    ) -> pd.DataFrame:
        """체중 기반 사료 필터링"""
        if weight_kg < 10:  # 소형견
            small_breed_criteria = self.breed_characteristics["small_breed"][life_stage]

            # 소형견용 사료 키워드
            small_breed_keywords = [
                "small breed",
                "toy breed",
                "mini",
                "small dog",
                "toy dog",
                "miniature",
            ]

            # 제품명에서 소형견용 사료 확인
            is_small_breed = (
                df["Product name"]
                .str.lower()
                .str.contains("|".join(small_breed_keywords), na=False)
            )

            # 키워드 필터링 적용 전 결과
            filtered_without_keyword = df[
                (df["protein_pct"] >= small_breed_criteria["protein_min"])
                & (df["fat_pct"] >= small_breed_criteria["fat_min"])
            ]

            # 키워드 필터링 적용 후 결과
            filtered_with_keyword = df[
                (df["protein_pct"] >= small_breed_criteria["protein_min"])
                & (df["fat_pct"] >= small_breed_criteria["fat_min"])
                & is_small_breed
            ]

            # 결과 비교를 위해 두 결과 모두 반환
            return filtered_without_keyword, filtered_with_keyword

        elif weight_kg >= 25:  # 대형견
            large_breed_criteria = self.breed_characteristics["large_breed"][life_stage]

            # 대형견용 사료 키워드
            large_breed_keywords = [
                "large breed",
                "giant breed",
                "large dog",
                "giant dog",
                "maxi",
            ]

            # 제품명에서 대형견용 사료 확인
            is_large_breed = (
                df["Product name"]
                .str.lower()
                .str.contains("|".join(large_breed_keywords), na=False)
            )

            filtered = df[
                (
                    df["protein_pct"] >= large_breed_criteria["protein_min"]
                )  # 최소 단백질 요구량
                & (df["fat_pct"] >= large_breed_criteria["fat_min"])  # 최소 지방 요구량
                & is_large_breed  # 대형견용 표시
            ]

            # 글루코사민 기준이 있는 경우 적용
            if "glucosamine_pct" in df.columns:
                filtered = filtered[
                    (filtered["glucosamine_pct"].isna())  # 데이터가 없는 경우는 통과
                    | (
                        filtered["glucosamine_pct"]
                        >= large_breed_criteria["glucosamine_min"]
                    )
                ]

            # 칼슘/인 비율 확인 (둘 다 있는 경우에만)
            if "calcium_pct" in df.columns and "phosphorus_pct" in df.columns:
                min_ratio, max_ratio = large_breed_criteria["calcium_phosphorus_ratio"]
                filtered = filtered[
                    (
                        filtered["calcium_pct"].isna()
                        | filtered["phosphorus_pct"].isna()
                    )  # 데이터가 없는 경우는 통과
                    | (
                        (
                            filtered["calcium_pct"] / filtered["phosphorus_pct"]
                            >= min_ratio
                        )
                        & (
                            filtered["calcium_pct"] / filtered["phosphorus_pct"]
                            <= max_ratio
                        )
                    )
                ]

            return filtered

        return df  # 중형견은 기본 필터링만 적용

    def calculate_ml_confidence(
        self, realtime_data: dict = None, feedback_history: list = None
    ) -> float:
        """스코어링 신뢰도 점수 계산"""
        confidence = 0.5  # 기본 신뢰도

        if realtime_data:
            # 실시간 데이터 완성도 체크
            data_completeness = (
                sum(
                    1
                    for key in [
                        "weight_trend",
                        "food_intake",
                        "activity",
                        "water_intake",
                    ]
                    if key in realtime_data and realtime_data[key]
                )
                / 4
            )
            confidence += data_completeness * 0.3

            # 데이터 품질 체크
            quality_score = 0
            if realtime_data.get("weight_trend", {}).get("trend") != "stable":
                quality_score += 0.1
            if realtime_data.get("food_intake", {}).get("pattern") != "normal":
                quality_score += 0.1
            if realtime_data.get("activity", {}).get("level") != "normal":
                quality_score += 0.1
            confidence += quality_score

        if feedback_history:
            # 피드백 데이터 신뢰도 체크
            recent_feedback = sorted(feedback_history, key=lambda x: x["date"])[-3:]
            if len(recent_feedback) >= 3:  # 최소 3일 이상의 데이터
                avg_rating = sum(f["rating"] for f in recent_feedback) / len(
                    recent_feedback
                )
                confidence += (avg_rating / 5) * 0.2

                # 증상 정보 체크
                if any(f.get("symptoms") for f in recent_feedback):
                    confidence += 0.1

        return min(1.0, confidence)

    def calculate_realtime_score(
        self, food_row: pd.Series, realtime_data: dict
    ) -> float:
        """실시간 데이터 기반 점수 계산"""
        score = 0.0

        if realtime_data:
            weight_trend = realtime_data.get("weight_trend", {})
            food_intake = realtime_data.get("food_intake", {})
            activity = realtime_data.get("activity", {})
            water_intake = realtime_data.get("water_intake", {})

            # 체중 증가 + 높은 섭취량인 경우 저지방 사료 선호
            if (
                weight_trend.get("trend") == "gaining"
                and food_intake.get("pattern") == "high_intake"
            ):
                if food_row["fat_pct"] < 8:  # 지방 기준 더 엄격하게
                    score += 0.5
                elif food_row["fat_pct"] < 10:
                    score += 0.3

            # 낮은 활동량인 경우 저칼로리 사료 선호
            if activity.get("level") == "low":
                if food_row["fat_pct"] < 10 and food_row["protein_pct"] < 25:
                    score += 0.3

            # 수분 섭취량이 낮은 경우 수분 함량 높은 사료 선호
            if water_intake.get("status") == "low":
                if food_row["moisture_pct"] > 60:
                    score += 0.4
                elif food_row["moisture_pct"] > 30:
                    score += 0.2

        return score

    def calculate_symptom_score(self, food_row: pd.Series, symptoms: list) -> float:
        """증상 기반 점수 계산"""
        score = 0.0

        for symptom in symptoms:
            if symptom == "joint_pain":
                # 글루코사민/콘드로이틴 함량 체크
                if (
                    not pd.isna(food_row.get("glucosamine_pct"))
                    and food_row["glucosamine_pct"] > 0
                ):
                    score += 0.4
                if (
                    not pd.isna(food_row.get("omega_3_pct"))
                    and food_row["omega_3_pct"] > 0
                ):
                    score += 0.3
            elif symptom == "lethargy":
                # 단백질과 지방 밸런스 체크
                if not pd.isna(food_row.get("protein_pct")) and not pd.isna(
                    food_row.get("fat_pct")
                ):
                    if 25 <= food_row["protein_pct"] <= 30 and food_row["fat_pct"] < 12:
                        score += 0.3
            elif symptom == "skin_condition":
                # 오메가3/6 밸런스 체크
                if not pd.isna(food_row.get("omega_3_pct")) and not pd.isna(
                    food_row.get("omega_6_pct")
                ):
                    ratio = food_row["omega_6_pct"] / food_row["omega_3_pct"]
                    if 2.5 <= ratio <= 7.0:  # 이상적인 비율
                        score += 0.4

        return score

    def get_recent_symptoms(self, feedback_history: list) -> list:
        """최근 증상 목록 추출"""
        if not feedback_history:
            return []

        recent_feedback = sorted(feedback_history, key=lambda x: x["date"])[
            -3:
        ]  # 최근 3개
        symptoms = []
        for feedback in recent_feedback:
            symptoms.extend(feedback.get("symptoms", []))
        return list(set(symptoms))  # 중복 제거

    def blend_recommendations(
        self,
        rule_based_df: pd.DataFrame,
        ml_based_df: pd.DataFrame,
        ml_confidence: float,
        realtime_data: dict = None,
        feedback_history: list = None,
        top_n: int = 10,
    ) -> pd.DataFrame:
        """규칙 기반과 스코어링 기반 추천 결과를 블렌딩"""
        if ml_confidence < self.feedback_threshold["min_confidence_score"]:
            rule_weight = 0.8
            ml_weight = 0.2
        else:
            rule_weight = 0.3
            ml_weight = 0.7

        # 1. 각 사료별 최종 점수 계산
        all_products = pd.concat([rule_based_df, ml_based_df]).drop_duplicates(
            subset=["Product name"]
        )

        # 2. 규칙 기반 점수 계산
        all_products["rule_score"] = all_products.apply(
            lambda row: self.calculate_nutrient_score(row), axis=1
        )
        all_products["final_score"] = all_products["rule_score"] * rule_weight

        # 3. 실시간 데이터 점수 반영
        if realtime_data:
            all_products["realtime_score"] = all_products.apply(
                lambda row: self.calculate_realtime_score(row, realtime_data), axis=1
            )
            all_products["final_score"] += all_products["realtime_score"] * 0.4

        # 4. 증상 기반 점수 반영
        if feedback_history:
            symptoms = self.get_recent_symptoms(feedback_history)
            if symptoms:
                all_products["symptom_score"] = all_products.apply(
                    lambda row: self.calculate_symptom_score(row, symptoms), axis=1
                )
                all_products["final_score"] += all_products["symptom_score"] * 0.3

        # 5. 점수순 정렬 및 상위 N개 반환
        result = all_products.sort_values("final_score", ascending=False).head(top_n)

        # 6. 임시 컬럼 삭제
        columns_to_drop = ["rule_score", "final_score"]
        if "realtime_score" in result.columns:
            columns_to_drop.append("realtime_score")
        if "symptom_score" in result.columns:
            columns_to_drop.append("symptom_score")

        result = result.drop(columns=columns_to_drop)
        return result

    def calculate_nutrient_score(self, food_row: pd.Series) -> float:
        """
        영양소 기준 충족도 점수 계산
        """
        score = 0.0

        # 1. 기본 영양소 점수
        nutrients = ["protein_pct", "fat_pct", "fiber_pct", "moisture_pct"]
        for nutrient in nutrients:
            if not pd.isna(food_row.get(nutrient)):
                # 적정 범위 내에 있으면 높은 점수
                if nutrient == "protein_pct":
                    score += 0.25 if 25 <= food_row[nutrient] <= 35 else 0.15
                elif nutrient == "fat_pct":
                    score += 0.25 if 10 <= food_row[nutrient] <= 15 else 0.15
                elif nutrient == "fiber_pct":
                    score += 0.25 if 3 <= food_row[nutrient] <= 7 else 0.15

        # 2. 특수 영양소 보너스 점수
        special_nutrients = [
            "omega_3_pct",
            "omega_6_pct",
            "glucosamine_pct",
            "chondroitin_pct",
        ]
        for nutrient in special_nutrients:
            if not pd.isna(food_row.get(nutrient)) and food_row[nutrient] > 0:
                score += 0.1

        # 3. 가격 점수
        if not pd.isna(food_row.get("Price")):
            price_score = 1 / (1 + food_row["Price"] / 100)
            score += price_score * 0.1

        return score

    def optimize_food_selection(
        self,
        df: pd.DataFrame,
        pet_data: dict,
        diseases: list[str],
        realtime_data: dict = None,
        feedback_history: list = None,
        top_n: int = 10,
    ) -> pd.DataFrame:
        """
        하이브리드 방식의 사료 추천

        Args:
            df: 필터링된 사료 DataFrame
            pet_data: 반려동물 정보
            diseases: 질병 리스트
            realtime_data: 실시간 모니터링 데이터
            feedback_history: 사용자 피드백 이력
            top_n: 추천할 사료 수

        Returns:
            추천 사료 목록
        """
        # 1. 스코어링 신뢰도 계산
        ml_confidence = self.calculate_ml_confidence(realtime_data, feedback_history)

        # 2. 규칙 기반 추천
        rule_based_results = self.disease_optimizer.optimize_food_selection(
            df, diseases, top_n=top_n
        )

        # 3. 스코어링 기반 추천
        ml_based_results = self.score_optimizer.optimize_food_selection(
            df, pet_data, realtime_data, feedback_history, top_n=top_n
        )

        # 4. 결과 블렌딩
        final_recommendations = self.blend_recommendations(
            rule_based_results,
            ml_based_results,
            ml_confidence,
            realtime_data,
            feedback_history,
            top_n,
        )

        return final_recommendations

    def adjust_nutrient_preferences(self, increase: list[str], decrease: list[str]):
        """
        영양소 선호도 조정

        Args:
            increase: 증가시킬 영양소 리스트
            decrease: 감소시킬 영양소 리스트
        """
        for nutrient in increase:
            self.nutrient_importance["Obesity"][nutrient] += 0.1
            self.nutrient_importance["Joint Disease"][nutrient] += 0.1
            self.nutrient_importance["Diabetes"][nutrient] += 0.1
            self.nutrient_importance["Heart Disease"][nutrient] += 0.1
            self.nutrient_importance["Kidney Disease"][nutrient] += 0.1
            self.nutrient_importance["Skin Conditions"][nutrient] += 0.1
            self.nutrient_importance["Food Allergies"][nutrient] += 0.1

        for nutrient in decrease:
            self.nutrient_importance["Obesity"][nutrient] -= 0.1
            self.nutrient_importance["Joint Disease"][nutrient] -= 0.1
            self.nutrient_importance["Diabetes"][nutrient] -= 0.1
            self.nutrient_importance["Heart Disease"][nutrient] -= 0.1
            self.nutrient_importance["Kidney Disease"][nutrient] -= 0.1
            self.nutrient_importance["Skin Conditions"][nutrient] -= 0.1
            self.nutrient_importance["Food Allergies"][nutrient] -= 0.1

    def adjust_nutrient_preferences_by_symptoms(self, symptoms: list[str]):
        """
        증상에 따른 영양소 조정

        Args:
            symptoms: 증상 리스트
        """
        for symptom in symptoms:
            if symptom == "joint_pain":
                self.nutrient_importance["Joint Disease"]["omega_3_pct"] += 0.1
                self.nutrient_importance["Joint Disease"]["calcium_pct"] += 0.1
            elif symptom == "lethargy":
                self.nutrient_importance["Kidney Disease"]["protein_pct"] += 0.1
                self.nutrient_importance["Kidney Disease"]["phosphorus_pct"] += 0.1
            elif symptom == "diarrhea":
                self.nutrient_importance["Diabetes"]["fiber_pct"] += 0.1
                self.nutrient_importance["Food Allergies"]["protein_pct"] += 0.1
            elif symptom == "vomiting":
                self.nutrient_importance["Food Allergies"]["protein_pct"] += 0.1
            elif symptom == "skin_condition":
                self.nutrient_importance["Skin Conditions"]["omega_3_pct"] += 0.1
                self.nutrient_importance["Skin Conditions"]["omega_6_pct"] += 0.1
            elif symptom == "heart_disease":
                self.nutrient_importance["Heart Disease"]["sodium_pct"] += 0.1
            elif symptom == "kidney_disease":
                self.nutrient_importance["Kidney Disease"]["sodium_pct"] += 0.1
                self.nutrient_importance["Kidney Disease"]["phosphorus_pct"] += 0.1
            elif symptom == "diabetes":
                self.nutrient_importance["Diabetes"]["fiber_pct"] += 0.1
            elif symptom == "food_allergies":
                self.nutrient_importance["Food Allergies"]["protein_pct"] += 0.1
            elif symptom == "obesity":
                self.nutrient_importance["Obesity"]["fat_pct"] += 0.1
            elif symptom == "hyperlipidemia":
                self.nutrient_importance["Hyperlipidemia"]["fat_pct"] += 0.1
            elif symptom == "cushing_disease":
                self.nutrient_importance["Cushing's Disease"]["fat_pct"] += 0.1
            elif symptom == "anemia":
                self.nutrient_importance["Anemia"]["protein_pct"] += 0.1
            elif symptom == "allergic_dermatitis":
                self.nutrient_importance["Allergic Dermatitis"]["omega_3_pct"] += 0.1
                self.nutrient_importance["Allergic Dermatitis"]["omega_6_pct"] += 0.1
            elif symptom == "hypothyroidism":
                self.nutrient_importance["Hypothyroidism"]["fat_pct"] += 0.1
            elif symptom == "dental_disease":
                self.nutrient_importance["Dental Disease"]["calcium_pct"] += 0.1
            elif symptom == "gastrointestinal_issues":
                self.nutrient_importance["Gastrointestinal Issues"]["fiber_pct"] += 0.1

    def analyze_recent_feedback(self, feedback_history: list[dict]) -> dict:
        """
        최근 피드백 분석

        Args:
            feedback_history: 피드백 이력

        Returns:
            분석 결과
        """
        if not feedback_history:
            return {}

        recent_feedback = feedback_history[-1]
        symptoms = recent_feedback["symptoms"]
        satisfaction = recent_feedback["satisfaction"]

        return {
            "symptoms": symptoms,
            "satisfaction": satisfaction,
        }

    def recommend_from_request(self, request_data: dict, top_n: int = 10) -> dict:
        """
        FastAPI 요청 형태의 데이터를 받아서 추천 결과를 반환하는 래퍼 함수

        Args:
            request_data: {
                "pet_data": {...},
                "diseases": [...],
                "realtime_data": {...},  # optional
                "feedback_history": [...],  # optional
            }
            top_n: 추천할 사료 수

        Returns:
            {
                "status": "success",
                "recommendations": [
                    {
                        "product_name": "...",
                        "brand": "...",
                        "price": 0.0,
                        "protein_pct": 0.0,
                        "fat_pct": 0.0,
                        "fiber_pct": 0.0,
                        "moisture_pct": 0.0,
                        "life_stage": "...",
                        "calorie_content": "...",
                        "ingredients": "...",
                        "rank": 1
                    },
                    ...
                ],
                "total_count": 3
            }
        """
        try:
            # 입력 데이터 추출
            pet_data = request_data.get("pet_data", {})
            diseases = request_data.get("diseases", [])
            realtime_data = request_data.get("realtime_data", None)
            feedback_history = request_data.get("feedback_history", None)

            # 추천 실행
            recommendations_df = self.optimize_food_selection(
                df=self.pet_filter.food_df,
                pet_data=pet_data,
                diseases=diseases,
                realtime_data=realtime_data,
                feedback_history=feedback_history,
                top_n=top_n,
            )

            # 결과를 JSON 친화적인 형태로 변환
            recommendations_list = []
            for rank, (idx, food) in enumerate(recommendations_df.iterrows(), 1):
                recommendation = {
                    "rank": rank,
                    "csv_index": int(idx),  # DataFrame의 원본 인덱스를 csv_index로 사용
                    "product_name": food.get("Product name", "N/A"),
                    "brand": food.get("Brand", "N/A"),
                    "price": (
                        float(food.get("Price", 0))
                        if pd.notna(food.get("Price"))
                        else None
                    ),
                    "protein_pct": (
                        float(food.get("protein_pct", 0))
                        if pd.notna(food.get("protein_pct"))
                        else None
                    ),
                    "fat_pct": (
                        float(food.get("fat_pct", 0))
                        if pd.notna(food.get("fat_pct"))
                        else None
                    ),
                    "fiber_pct": (
                        float(food.get("fiber_pct", 0))
                        if pd.notna(food.get("fiber_pct"))
                        else None
                    ),
                    "moisture_pct": (
                        float(food.get("moisture_pct", 0))
                        if pd.notna(food.get("moisture_pct"))
                        else None
                    ),
                    "life_stage": food.get("life_stage", "N/A"),
                    "calorie_content": food.get("Calorie Content", "N/A"),
                    "ingredients": food.get("Ingredients", "N/A"),
                    "url": food.get("Url", "N/A"),
                }
                recommendations_list.append(recommendation)

            return {
                "status": "success",
                "recommendations": recommendations_list,
                "total_count": len(recommendations_list),
                "input_summary": {
                    "pet_weight_kg": pet_data.get("weight_kg"),
                    "pet_age_months": pet_data.get("age_months"),
                    "life_stage": pet_data.get("life_stage"),
                    "breed_size": pet_data.get("breed_size"),
                    "allergies": pet_data.get("allergies", []),
                    "diseases": diseases,
                    "has_realtime_data": realtime_data is not None,
                    "has_feedback_data": feedback_history is not None,
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "error_type": type(e).__name__,
                "recommendations": [],
                "total_count": 0,
            }
