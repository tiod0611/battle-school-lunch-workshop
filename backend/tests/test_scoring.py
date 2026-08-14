from app.services import scoring


def test_seasonal_ingredient_scores():
    assert scoring.score_seasonal_ingredients(["불고기"], "20260401") == 0
    assert scoring.score_seasonal_ingredients(["딸기샐러드"], "20260401") == 10
    assert scoring.score_seasonal_ingredients(["딸기샐러드", "냉이국"], "20260401") == 18
    assert scoring.score_seasonal_ingredients(["딸기샐러드", "냉이국", "두릅무침"], "20260401") == 25


def test_nutrition_balance_scores():
    good = "탄수화물(g) 120<br/>단백질(g) 20<br/>지방(g) 20"
    low = "탄수화물(g) 20<br/>단백질(g) 20<br/>지방(g) 20"
    missing = "단백질(g) 20<br/>지방(g) 20"
    assert scoring.score_nutrition_balance(good)[0] == 30
    assert scoring.score_nutrition_balance(low)[0] < 30
    assert scoring.score_nutrition_balance(missing)[0] == 0


def test_menu_variety_scores():
    assert scoring.score_menu_variety(["1"])[0] == 5
    assert scoring.score_menu_variety(["1", "2", "3", "4"])[0] == 15
    assert scoring.score_menu_variety(["1", "2", "3", "4", "5", "6"])[0] == 20
    assert scoring.score_menu_variety(["1", "2", "3", "4", "5", "6", "7", "8"])[0] == 25


def test_processed_food_penalty_scores():
    assert scoring.score_processed_food_penalty(["비빔밥"]) == 0
    assert scoring.score_processed_food_penalty(["소시지볶음"]) == -5
    assert scoring.score_processed_food_penalty(["소시지볶음", "햄구이"]) == -10
    assert scoring.score_processed_food_penalty(["소시지", "햄", "베이컨", "스팸", "너겟"]) == -20