from app.services.builder import determine_environment


def test_main_branch_maps_to_prod():
    assert determine_environment("main") == "prod"


def test_prod_branch_maps_to_prod():
    assert determine_environment("prod") == "prod"


def test_master_branch_maps_to_prod():
    assert determine_environment("master") == "prod"


def test_dev_branch_maps_to_dev():
    assert determine_environment("dev") == "dev"


def test_feature_branch_returns_none():
    assert determine_environment("feature/new-thing") is None


def test_random_branch_returns_none():
    assert determine_environment("hotfix/bug-123") is None
