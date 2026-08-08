# UI workflow missing outcomes

1. **UI:** Click Add Merchant
   - Actor: Partner admin
   - Action: Click Add Merchant in the nav.
   - outcome_missing: true

2. **UI:** Fill registration form
   - Actor: Partner admin
   - Action: Enter business name and country.
   - Expected outcome: The confirmation dialog appears.
   - outcome_missing: false

3. **API:** Submit registration
   - Actor: Partner system
   - Action: POST /boarding/v1/registrations
   - outcome_missing: true
