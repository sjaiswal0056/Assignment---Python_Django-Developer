For Automatic Testing 

python manage.py check
System check identified no issues (0 silenced).
PS D:\python-Django-project> 


 python manage.py runserver
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 24, 2026 - 01:15:33
Django version 5.2.18, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.

WARNING: This is a development server. Do not use it in a production setting. Use a production WSGI or ASGI server instead.
For more information on production servers see: https://docs.djangoproject.com/en/5.2/howto/deployment/
[24/Oct/2026 01:15:56] "GET /admin/orders/order/add/ HTTP/1.1" 200 25707
[24/Oct/2026 01:16:04,103] - Broken pipe from ('127.0.0.1', 50499)
[24/Oct/2026 01:16:04] "GET / HTTP/1.1" 200 50468
[24/Oct/2026 01:50:04] "GET /recommender/ HTTP/1.1" 200 68330
[24/Oct/2026 01:56:56] "GET /?utm_source=chatgpt.com HTTP/1.1" 200 50468
[24/Oct/2026 01:57:26] "GET /recommender/ HTTP/1.1" 200 68330
PS D:\python-Django-project> python manage.py check
System check identified no issues (0 silenced).
PS D:\python-Django-project> python manage.py test --verbosity=2
Found 46 test(s).
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
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
  Applying orders.0002_alter_order_status... OK
  Applying recommendations.0001_initial... OK
  Applying recommendations.0002_boxrecommendation_is_stale_and_more... OK
  Applying sessions.0001_initial... OK
System check identified no issues (0 silenced).
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
test_catalog_product_vs_custom_item_equivalence (tests.test_validation_parcel.ParcelRecommendationValidationTests.test_catalog_product_vs_custom_item_equivalence)
Verify that selecting a catalog product and adding a custom item with ... ok
test_cost_optimization_prioritizes_lowest_cost (tests.test_validation_parcel.ParcelRecommendationValidationTests.test_cost_optimization_prioritizes_lowest_cost)
Verify that the engine always chooses the lowest cost box among all feasible candidates, ... ok
test_decision_rationale_consistency (tests.test_validation_parcel.ParcelRecommendationValidationTests.test_decision_rationale_consistency)
Verify that the generated explanation is completely consistent with the audit trail. ... ok
test_every_box_evaluated_in_audit_trail (tests.test_validation_parcel.ParcelRecommendationValidationTests.test_every_box_evaluated_in_audit_trail)
Verify that EVERY active box in inventory is evaluated in the audit trail, ... ok
test_extra_small_padded_mailer_rejection (tests.test_validation_parcel.ParcelRecommendationValidationTests.test_extra_small_padded_mailer_rejection)
Verify Extra Small Padded Mailer (15x10x5cm, max 1.0kg, $0.75) is rejected ... ok
test_item_orientation_rotation_enables_fit (tests.test_validation_parcel.ParcelRecommendationValidationTests.test_item_orientation_rotation_enables_fit)
Verify that when an item is provided in an orientation that doesn't fit (e.g. height 15cm > 12cm), ... ok
test_optimal_recommendation_and_utilization_metrics (tests.test_validation_parcel.ParcelRecommendationValidationTests.test_optimal_recommendation_and_utilization_metrics)
Verify that for the test parcel (20x15x10cm, 1.2kg), Box-S is selected ... ok
test_product_32_21_12_recommends_medium_parcel_box (tests.test_validation_parcel.ParcelRecommendationValidationTests.test_product_32_21_12_recommends_medium_parcel_box)
Verify recommendation for product measuring 32 x 21 x 12 cm and weighing 1.1 kg: ... ok
test_slim_book_box_rejection_against_all_orientations (tests.test_validation_parcel.ParcelRecommendationValidationTests.test_slim_book_box_rejection_against_all_orientations)
Verify that the Slim Book & Document Box (35x26x6cm, 3kg, $1.10) is rejected ... ok
test_scenario_10_shipment_modifications_invalidate_outdated_recommendations (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_10_shipment_modifications_invalidate_outdated_recommendations)
Scenario 10: Modifying order items, quantities, or product dimensions ... ok
test_scenario_11_audit_logs_reflect_actual_recommendation_decision (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_11_audit_logs_reflect_actual_recommendation_decision)
Scenario 11: Audit log accurately records candidate box evaluations, ... ok
test_scenario_12_api_response_provides_all_required_fields_for_frontend (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_12_api_response_provides_all_required_fields_for_frontend)
Scenario 12: The API response provides all required fields for immediate ... ok
test_scenario_1_calculated_recommendation_appears_in_fulfillment_queue (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_1_calculated_recommendation_appears_in_fulfillment_queue)
Scenario 1: When a recommendation is calculated for an order, it is ... ok
test_scenario_2_packaging_cost_updated_after_recalculation (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_2_packaging_cost_updated_after_recalculation)
Scenario 2: Packaging cost starts empty/pending, and is correctly updated ... ok
test_scenario_3_oversized_shipment_displays_oversized_special_freight (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_3_oversized_shipment_displays_oversized_special_freight)
Scenario 3: An item whose dimensions exceed all boxes in the catalog is ... ok
test_scenario_4_weight_limit_exceeded_not_marked_as_oversized (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_4_weight_limit_exceeded_not_marked_as_oversized)
Scenario 4: An item that fits dimensionally but exceeds weight limits ... ok
test_scenario_5_recommendation_associated_with_correct_order (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_5_recommendation_associated_with_correct_order)
Scenario 5: Calculating for Order 1 persists a recommendation for Order 1 ... ok
test_scenario_6_standalone_simulator_does_not_modify_unrelated_orders (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_6_standalone_simulator_does_not_modify_unrelated_orders)
Scenario 6: Using the simulator in standalone mode (no order_id) calculates ... ok
test_scenario_7_failed_calculation_not_marked_as_recommended (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_7_failed_calculation_not_marked_as_recommended)
Scenario 7: When an order cannot be accommodated or calculation encounters ... ok
test_scenario_8_recalculating_one_order_leaves_other_orders_unchanged (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_8_recalculating_one_order_leaves_other_orders_unchanged)
Scenario 8: Recalculating Order 1 does not alter Order 2's recommendation, ... ok
test_scenario_9_queue_displays_latest_saved_recommendation (tests.test_workflow_integration.RecommendationWorkflowIntegrationTests.test_scenario_9_queue_displays_latest_saved_recommendation)
Scenario 9: If multiple recommendations exist historically for an order, ... ok
test_item_fits_with_3d_rotation (tests.test_packing_engine.PackingEngineTests.test_item_fits_with_3d_rotation) ... ok
test_item_rejected_when_exceeding_volume (tests.test_packing_engine.PackingEngineTests.test_item_rejected_when_exceeding_volume) ... ok
test_item_rejected_when_exceeding_weight_capacity (tests.test_packing_engine.PackingEngineTests.test_item_rejected_when_exceeding_weight_capacity) ... ok
test_item_rejected_when_single_dimension_too_long (tests.test_packing_engine.PackingEngineTests.test_item_rejected_when_single_dimension_too_long) ... ok
test_multi_item_packing_non_overlapping (tests.test_packing_engine.PackingEngineTests.test_multi_item_packing_non_overlapping) ... ok
test_single_item_fits_exact_dimensions (tests.test_packing_engine.PackingEngineTests.test_single_item_fits_exact_dimensions) ... ok
test_spatial_collision_failure (tests.test_packing_engine.PackingEngineTests.test_spatial_collision_failure) ... ok

----------------------------------------------------------------------
Ran 46 tests in 1.214s

OK
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
PS D:\python-Django-project> 


