1.---> Which AI tool(s) you used.
## 1. AI Tools Used

### 1. ChatGPT

ChatGPT was used for understanding project requirements discussing how to implement Django improving the logic for selecting boxes troubleshooting problems reviewing test results and preparing project documentation.

### 2. Antigravity

Antigravity was used for AI‑assisted code development, refining application features reviewing the recommendation algorithm, troubleshooting issues and improving the consistency, between the backend logic and the user interface.

AI tools were used as development assistants. Their suggestions were reviewed against the project requirements and the application was tested to verify the implemented functionality.


2.-----> The prompts you gave.
## 2. Prompts Given to AI Tools

During development I used AI tools to understand the requirements implement features, troubleshoot issues and verify the application.

### Prompt 1: Understanding Project Requirements

**AI Tool:** ChatGPT

"Help me understand the Python/Django AI-Assisted Box Selection System requirements and identify the features, application components and implementation steps."

### Prompt 2: Implementing Box Selection Logic

**AI Tool:** ChatGPT / Antigravity

"Review the box-selection algorithm. The system should evaluate product dimensions, product weight, box dimensions, maximum box weight and box cost. Recommend the lowest-cost box that satisfies all constraints."

### Prompt 3: Validating Box Recommendations

**AI Tool:** Antigravity

"Review the recommendation service to ensure that boxes are evaluated using their dimensions and weight limits. Consider supported rotations. Ensure that unsuitable boxes are rejected with accurate explanations."

### Prompt 4: Improving the Fulfillment Queue

**AI Tool:** Antigravity

"Review the Fulfillment Queue workflow. Ensure that recommendations are associated with the orders and that running the standalone parcel simulator does not modify unrelated orders."

### Prompt 5: Reviewing the Audit Trail

**AI Tool:** Antigravity

"Review the audit trail to ensure that the acceptance and rejection reasons accurately reflect the box-selection algorithm and its validation rules."

### Prompt 6: Testing and Debugging

**AI Tool:** ChatGPT

"Help me understand the Django automated test results identify issues in the recommendation logic and verify that the tested scenarios cover dimensions, weight constraints, cost optimization, packing and order workflows."

### Prompt 7: Fixing Issues and Verifying Changes

**AI Tool:** ChatGPT / Antigravity

"Review the implementation, against the project requirements identify inconsistencies suggest corrections and explain how to verify the changes using Django system checks and automated tests."


3.----> What output you accepted.
## 3. What I Took in Output

I used ChatGPT and Antigravity to build my Python/Django AI-Assisted Box Selection System.

I accepted and used relevant AI generated suggestions for the tasks below:

1. Box Selection Algorithm:** Help select appropriate boxes based on product dimensions, weight limitations, and box price.
2. Cost Optimization:** Tips on how to choose the cheapest box that fits all your size and weight requirements.
3. Validation Logic:** Tips on how to verify product dimensions and weight against box specifications.
4. Fulfillment Queue:** Help review order recommendations and confirm that standalone parcel calculations do not unintentionally change unrelated orders.
5. Audit Trail: Guidance on how to determine if the reasons for box acceptance/rejection are consistent with the recommendation logic.
6. Testing and Debugging:Assist in identifying test scenarios, resolving issues, and understanding Django test results.

4.----> What output you rejected or modified.

## 4. What Output I Rejected or Modified

The main areas I reviewed and refined were:

The main things I checked and improved:

1. **Logic for Box Selection:** I checked that box recommendations were based on product dimensions, weight limits, and cost, not just volume of the box.

2. **Validation of recommendation:** I checked the logic of selection and made sure that boxes that could not fit a product were rejected properly.

3. Fulfillment Queue: I checked the workflow to ensure that calculations for standalone parcels were not affecting other orders.

4. **Audit Trail:** I confirmed that the reasons for accepting or rejecting the box were consistent with the recommendation logic.

5. **Test**: I checked the implementation against project requirements and scenarios tested with automated tests.

5.----> Any mistakes the AI made.
During verification, the following points have been checked:

Ensuring that box suggestions were made taking into account the dimensions, weight limitations, and box cost.

Checking that the inappropriate boxes were not accepted.

Ensuring that there was consistency between recommendation and audit trail explanation.

Ensuring that separate package calculations did not unintentionally affect other orders.

6. How you verified the final code

----->6. How I Verified the Final Code

The final implementation of the AI-Assisted Box Selection System created with Python/Django has been verified by performing Django system checks, automated testing and manual testing.

### 1. Django System Check

I executed the following command:

`python manage.py check`

**Result:** System check identified no issues (0 silenced).

It has shown that there are no problems detected by Django system check.

### 2. Automated Testing

Django automated testing was done by executing the following command:

`python manage.py test --verbosity=2`

**Test Execution Results:**
- Number of tests: 46
- Tests passed: 46
- Tests failed: 0
- Final status: OK

### 3. Manual Testing

I manually tested the application via web interface in order to see if its basic functionalities work as intended.

The scenarios used during manual testing included:

- **Box Selection:** Checking whether the application recommends a proper box for a product.
- **Dimension Validation:** Checking whether boxes, that cannot fit a product inside, are rejected.
- **Weight Validation:** Checking whether boxes, exceeding the permissible weight limit, are rejected.
- **Cost Optimization:** Checking whether the recommended box is a least expensive one among the options.
- **Order Recommendations:** Checking whether recommendations are correctly associated with orders.
- **Fulfillment Queue:** Checking whether calculations of standalone parcels are not affecting other orders.
- **Audit Trail:** Checking reasons for accepting/rejecting boxes.

Each manual test was evaluated by comparing the actual result with the expected result. Pass/fail status was noted.

### 4. Final Verification

I have compared the results of the system-checks, automated testing and manual testing with the requirements of the project.

Automated testing gave me a possibility to verify the repeatable scenarios. Manual testing helped to evaluate the application by its interface.

The above mentioned results prove the functionality checked during the testing. They do not guarantee correctness of every possible scenario or input.