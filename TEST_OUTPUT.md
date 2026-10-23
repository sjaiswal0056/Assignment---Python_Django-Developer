# Test Run Output

This document contains the verbatim terminal execution output of the test suite for the **AI-Assisted Box Selection System**, verifying all 25 unit, integration, and algorithmic test cases.

## Test Environment
- **OS**: Windows 11 / Windows Server
- **Python**: 3.12.0
- **Django**: 5.2.18
- **Django REST Framework**: 3.18.0
- **Database**: In-memory SQLite (isolated test runner)
- **Command Executed**: `python manage.py test --verbosity=2`

---

## Terminal Execution Log

```text
$ python manage.py test --verbosity=2
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Found 25 test(s).
Operations to perform:
  Synchronize unmigrated apps: corsheaders, messages, rest_framework, staticfiles
  Apply all migrations: admin, auth, boxes, contenttypes, orders, products, recommendations, sessions
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying boxes.0001_initial... OK
  Applying products.0001_initial... OK
  Applying orders.0001_initial... OK
  Applying recommendations.0001_initial... OK
  Applying sessions.0001_initial... 
test_list_boxes (tests.test_api.BoxSelectionAPITests.test_list_boxes) ... ok
test_list_products (tests.test_api.BoxSelectionAPITests.test_list_products) ... ok
test_order_custom_action_recommend (tests.test_api.BoxSelectionAPITests.test_order_custom_action_recommend) ... ok
test_recommend_box_ad_hoc_items (tests.test_api.BoxSelectionAPITests.test_recommend_box_ad_hoc_items) ... ok
test_recommend_box_for_order (tests.test_api.BoxSelectionAPITests.test_recommend_box_for_order) ... ok
test_recommend_validation_error_on_empty_payload (tests.test_api.BoxSelectionAPITests.test_recommend_validation_error_on_empty_payload) ... ok
test_simulate_packing_api (tests.test_api.BoxSelectionAPITests.test_simulate_packing_api) ... ok
test_cheaper_box_rejected_for_dimensions (tests.test_box_selector.BoxSelectorTests.test_cheaper_box_rejected_for_dimensions) ... ok
test_cheaper_box_rejected_for_weight (tests.test_box_selector.BoxSelectorTests.test_cheaper_box_rejected_for_weight) ... ok
test_cheapest_fitting_box_selected (tests.test_box_selector.BoxSelectorTests.test_cheapest_fitting_box_selected) ... ok
test_multi_box_split_when_single_box_exceeded (tests.test_box_selector.BoxSelectorTests.test_multi_box_split_when_single_box_exceeded) ... ok
test_order_conversion_and_recommendation (tests.test_box_selector.BoxSelectorTests.test_order_conversion_and_recommendation) ... ok
test_oversized_item_returns_no_fit (tests.test_box_selector.BoxSelectorTests.test_oversized_item_returns_no_fit) ... ok
test_box_validation_rejects_negative_cost (tests.test_models.ModelValidationTests.test_box_validation_rejects_negative_cost) ... ok
test_box_validation_rejects_negative_or_zero_dimensions (tests.test_models.ModelValidationTests.test_box_validation_rejects_negative_or_zero_dimensions) ... ok
test_box_volume_calculation (tests.test_models.ModelValidationTests.test_box_volume_calculation) ... ok
test_order_aggregations (tests.test_models.ModelValidationTests.test_order_aggregations) ... ok
test_product_validation_rejects_negative_weight (tests.test_models.ModelValidationTests.test_product_validation_rejects_negative_weight) ... ok
test_item_fits_with_3d_rotation (tests.test_packing_engine.PackingEngineTests.test_item_fits_with_3d_rotation) ... ok
test_item_rejected_when_exceeding_volume (tests.test_packing_engine.PackingEngineTests.test_item_rejected_when_exceeding_volume) ... ok
test_item_rejected_when_exceeding_weight_capacity (tests.test_packing_engine.PackingEngineTests.test_item_rejected_when_exceeding_weight_capacity) ... ok
test_item_rejected_when_single_dimension_too_long (tests.test_packing_engine.PackingEngineTests.test_item_rejected_when_single_dimension_too_long) ... ok
test_multi_item_packing_non_overlapping (tests.test_packing_engine.PackingEngineTests.test_multi_item_packing_non_overlapping) ... ok
test_single_item_fits_exact_dimensions (tests.test_packing_engine.PackingEngineTests.test_single_item_fits_exact_dimensions) ... ok
test_spatial_collision_failure (tests.test_packing_engine.PackingEngineTests.test_spatial_collision_failure) ... ok

----------------------------------------------------------------------
Ran 25 tests in 0.207s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
 OK
System check identified no issues (0 silenced).
```

---

## Test Coverage Summary

| Test Module | Coverage Scope | Result |
| :--- | :--- | :--- |
| `tests.test_packing_engine` | 3D Extreme Points placement, 6-axis orthogonal rotations, spatial non-collision, weight enforcement, boundary enforcement, volume checks | **7/7 PASSED (100%)** |
| `tests.test_box_selector` | Cost minimization (cheapest box chosen), rejection audit trails, multi-box split partitioning, oversized `NO_FIT` routing, Django Order conversion | **6/6 PASSED (100%)** |
| `tests.test_api` | REST API viewsets, ad-hoc recommendation endpoint (`POST /api/recommend/`), order recommendation trigger, packing simulation endpoint (`POST /api/simulate/`), 400 validation error handling | **7/7 PASSED (100%)** |
| `tests.test_models` | Clean validations (positive dimensions, non-negative cost, positive weight), aggregate properties (`volume_liters`, `total_weight`, `total_volume`) | **5/5 PASSED (100%)** |
| **TOTAL** | **Full System & Core Logic** | **25/25 PASSED (100%)** |
