from copy import deepcopy


def find_error_dict_with_code(tests, code):
    return next((test_dict for test_dict in tests if test_dict["code"] == code), None)


def update_migration_tests(base_tests, specific_tests):
    base_tests = deepcopy(base_tests)
    for override_test in specific_tests:
        migration_test_dict = find_error_dict_with_code(
            base_tests, override_test["code"]
        )

        if migration_test_dict is None or not override_test["code"]:
            migration_test_dict = {}
            base_tests.append(migration_test_dict)

        for key in override_test.keys():
            migration_test_dict[key] = override_test[key]
    return base_tests
