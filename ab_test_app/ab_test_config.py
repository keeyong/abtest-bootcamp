# A/B 테스트 설정 (예: 100명 중 50명만 참여, A/B 각각 50%)
AB_TEST_CONFIG = {
    "test_name": "new_button_color",
    "enabled": True,
    "percentage": 50,  # 전체 중 50%만 참여
    "variant_split": {"A": 50, "B": 50}  # 참여자 중 A/B를 50:50으로
}
