# OpportunitySummaryV1

**Properties**

| Name                              | Type                     | Required | Description                                                                                                            |
| :-------------------------------- | :----------------------- | :------- | :--------------------------------------------------------------------------------------------------------------------- |
| additional_info_url               | str                      | ❌       | A URL to a website that can provide additional information about the opportunity                                       |
| additional_info_url_description   | str                      | ❌       | The text to display for the additional_info_url link                                                                   |
| agency_contact_description        | str                      | ❌       | Information regarding contacting the agency who owns the opportunity                                                   |
| agency_email_address              | str                      | ❌       | The contact email of the agency who owns the opportunity                                                               |
| agency_email_address_description  | str                      | ❌       | The text for the link to the agency email address                                                                      |
| applicant_eligibility_description | str                      | ❌       | Additional information about the types of applicants that are eligible                                                 |
| applicant_types                   | List[ApplicantTypes]     | ❌       |                                                                                                                        |
| archive_date                      | str                      | ❌       | When the opportunity will be archived                                                                                  |
| award_ceiling                     | int                      | ❌       | The maximum amount an opportunity would award                                                                          |
| award_floor                       | int                      | ❌       | The minimum amount an opportunity would award                                                                          |
| close_date                        | str                      | ❌       | The date that the opportunity will close - only set if is_forecast=False                                               |
| close_date_description            | str                      | ❌       | Optional details regarding the close date                                                                              |
| created_at                        | str                      | ❌       | When the opportunity summary was created                                                                               |
| estimated_total_program_funding   | int                      | ❌       | The total program funding of the opportunity in US Dollars                                                             |
| expected_number_of_awards         | int                      | ❌       | The number of awards the opportunity is expected to award                                                              |
| fiscal_year                       | int                      | ❌       | Forecasted opportunity only. The fiscal year the project is expected to be funded and launched                         |
| forecasted_award_date             | str                      | ❌       | Forecasted opportunity only. The date the grantor plans to award the opportunity.                                      |
| forecasted_close_date             | str                      | ❌       | Forecasted opportunity only. The date the opportunity is expected to be close once posted.                             |
| forecasted_close_date_description | str                      | ❌       | Forecasted opportunity only. Optional details regarding the forecasted closed date.                                    |
| forecasted_post_date              | str                      | ❌       | Forecasted opportunity only. The date the opportunity is expected to be posted, and transition out of being a forecast |
| forecasted_project_start_date     | str                      | ❌       | Forecasted opportunity only. The date the grantor expects the award recipient should start their project               |
| funding_categories                | List[FundingCategories]  | ❌       |                                                                                                                        |
| funding_category_description      | str                      | ❌       | Additional information about the funding category                                                                      |
| funding_instruments               | List[FundingInstruments] | ❌       |                                                                                                                        |
| is_cost_sharing                   | bool                     | ❌       | Whether or not the opportunity has a cost sharing/matching requirement                                                 |
| is_forecast                       | bool                     | ❌       | Whether the opportunity is forecasted, that is, the information is only an estimate and not yet official               |
| post_date                         | str                      | ❌       | The date the opportunity was posted                                                                                    |
| summary_description               | str                      | ❌       | The summary of the opportunity                                                                                         |
| updated_at                        | str                      | ❌       | When the opportunity summary was last updated                                                                          |
| version_number                    | int                      | ❌       | The version number of the opportunity summary                                                                          |

# ApplicantTypes

**Properties**

| Name                                               | Type | Required | Description                                               |
| :------------------------------------------------- | :--- | :------- | :-------------------------------------------------------- |
| STATEGOVERNMENTS                                   | str  | ✅       | "state_governments"                                       |
| COUNTYGOVERNMENTS                                  | str  | ✅       | "county_governments"                                      |
| CITYORTOWNSHIPGOVERNMENTS                          | str  | ✅       | "city_or_township_governments"                            |
| SPECIALDISTRICTGOVERNMENTS                         | str  | ✅       | "special_district_governments"                            |
| INDEPENDENTSCHOOLDISTRICTS                         | str  | ✅       | "independent_school_districts"                            |
| PUBLICANDSTATEINSTITUTIONSOFHIGHEREDUCATION        | str  | ✅       | "public_and_state_institutions_of_higher_education"       |
| PRIVATEINSTITUTIONSOFHIGHEREDUCATION               | str  | ✅       | "private_institutions_of_higher_education"                |
| FEDERALLYRECOGNIZEDNATIVEAMERICANTRIBALGOVERNMENTS | str  | ✅       | "federally_recognized_native_american_tribal_governments" |
| OTHERNATIVEAMERICANTRIBALORGANIZATIONS             | str  | ✅       | "other_native_american_tribal_organizations"              |
| PUBLICANDINDIANHOUSINGAUTHORITIES                  | str  | ✅       | "public_and_indian_housing_authorities"                   |
| NONPROFITSNONHIGHEREDUCATIONWITH501C3              | str  | ✅       | "nonprofits_non_higher_education_with_501c3"              |
| NONPROFITSNONHIGHEREDUCATIONWITHOUT501C3           | str  | ✅       | "nonprofits_non_higher_education_without_501c3"           |
| INDIVIDUALS                                        | str  | ✅       | "individuals"                                             |
| FORPROFITORGANIZATIONSOTHERTHANSMALLBUSINESSES     | str  | ✅       | "for_profit_organizations_other_than_small_businesses"    |
| SMALLBUSINESSES                                    | str  | ✅       | "small_businesses"                                        |
| OTHER                                              | str  | ✅       | "other"                                                   |
| UNRESTRICTED                                       | str  | ✅       | "unrestricted"                                            |

# FundingCategories

**Properties**

| Name                                            | Type | Required | Description                                             |
| :---------------------------------------------- | :--- | :------- | :------------------------------------------------------ |
| RECOVERYACT                                     | str  | ✅       | "recovery_act"                                          |
| AGRICULTURE                                     | str  | ✅       | "agriculture"                                           |
| ARTS                                            | str  | ✅       | "arts"                                                  |
| BUSINESSANDCOMMERCE                             | str  | ✅       | "business_and_commerce"                                 |
| COMMUNITYDEVELOPMENT                            | str  | ✅       | "community_development"                                 |
| CONSUMERPROTECTION                              | str  | ✅       | "consumer_protection"                                   |
| DISASTERPREVENTIONANDRELIEF                     | str  | ✅       | "disaster_prevention_and_relief"                        |
| EDUCATION                                       | str  | ✅       | "education"                                             |
| EMPLOYMENTLABORANDTRAINING                      | str  | ✅       | "employment_labor_and_training"                         |
| ENERGY                                          | str  | ✅       | "energy"                                                |
| ENVIRONMENT                                     | str  | ✅       | "environment"                                           |
| FOODANDNUTRITION                                | str  | ✅       | "food_and_nutrition"                                    |
| HEALTH                                          | str  | ✅       | "health"                                                |
| HOUSING                                         | str  | ✅       | "housing"                                               |
| HUMANITIES                                      | str  | ✅       | "humanities"                                            |
| INFRASTRUCTUREINVESTMENTANDJOBSACT              | str  | ✅       | "infrastructure_investment_and_jobs_act"                |
| INFORMATIONANDSTATISTICS                        | str  | ✅       | "information_and_statistics"                            |
| INCOMESECURITYANDSOCIALSERVICES                 | str  | ✅       | "income_security_and_social_services"                   |
| LAWJUSTICEANDLEGALSERVICES                      | str  | ✅       | "law_justice_and_legal_services"                        |
| NATURALRESOURCES                                | str  | ✅       | "natural_resources"                                     |
| OPPORTUNITYZONEBENEFITS                         | str  | ✅       | "opportunity_zone_benefits"                             |
| REGIONALDEVELOPMENT                             | str  | ✅       | "regional_development"                                  |
| SCIENCETECHNOLOGYANDOTHERRESEARCHANDDEVELOPMENT | str  | ✅       | "science_technology_and_other_research_and_development" |
| TRANSPORTATION                                  | str  | ✅       | "transportation"                                        |
| AFFORDABLECAREACT                               | str  | ✅       | "affordable_care_act"                                   |
| OTHER                                           | str  | ✅       | "other"                                                 |

# FundingInstruments

**Properties**

| Name                 | Type | Required | Description             |
| :------------------- | :--- | :------- | :---------------------- |
| COOPERATIVEAGREEMENT | str  | ✅       | "cooperative_agreement" |
| GRANT                | str  | ✅       | "grant"                 |
| PROCUREMENTCONTRACT  | str  | ✅       | "procurement_contract"  |
| OTHER                | str  | ✅       | "other"                 |

<!-- This file was generated by liblab | https://liblab.com/ -->
