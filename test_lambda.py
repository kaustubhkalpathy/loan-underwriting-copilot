"""Test Lambda with different applicant profiles."""
import boto3, json

client = boto3.Session(region_name='us-east-1').client('lambda')

def test(label, props):
    payload = {"actionGroup":"predict-risk","apiPath":"/predict","httpMethod":"POST",
               "requestBody":{"content":{"application/json":{"properties":props}}}}
    r = client.invoke(FunctionName='predict-default-risk', Payload=json.dumps(payload))
    body = json.loads(r['Payload'].read())
    result = json.loads(body['response']['responseBody']['application/json']['body'])
    score = result["risk_score"]
    action = result["recommended_action"]
    print(f"  {label:12s} | score={score:.4f} ({score*100:.1f}%) | {action}")
    return score

def p(name, value):
    return {"name": name, "value": str(value)}

print("=" * 60)
print("  LAMBDA TEST RESULTS")
print("=" * 60)
print()

# Test 1: Perfect applicant
s1 = test("PERFECT", [p("AGE_YEARS",45),p("EMPLOYMENT_YEARS",15),p("IS_UNEMPLOYED",0),p("CREDIT_TO_INCOME_RATIO",1.5),p("ANNUITY_TO_INCOME_RATIO",0.1),p("CREDIT_PER_FAMILY_MEMBER",112500),p("INCOME_PER_FAMILY_MEMBER",75000),p("CHILD_DEPENDENCY_RATIO",0.25),p("EXT_SOURCE_MEAN",0.85),p("CREDIT_TERM",36),p("EXT_SOURCE_1_MISSING",0),p("OWN_CAR_AGE_MISSING",0),p("YEARS_BUILD_MISSING",0),p("NAME_CONTRACT_TYPE","Cash loans"),p("CODE_GENDER","F"),p("FLAG_OWN_CAR","Y"),p("FLAG_OWN_REALTY","Y"),p("NAME_TYPE_SUITE","Unaccompanied"),p("NAME_INCOME_TYPE","State servant"),p("NAME_EDUCATION_TYPE","Higher education"),p("NAME_FAMILY_STATUS","Married"),p("NAME_HOUSING_TYPE","House / apartment"),p("OCCUPATION_TYPE","Accountants"),p("WEEKDAY_APPR_PROCESS_START","MONDAY"),p("ORGANIZATION_TYPE","Business Entity Type 3"),p("FONDKAPREMONT_MODE","reg oper account"),p("HOUSETYPE_MODE","block of flats"),p("WALLSMATERIAL_MODE","Panel"),p("EMERGENCYSTATE_MODE","No")])

# Test 2: Worst case
s2 = test("WORST", [p("AGE_YEARS",22),p("EMPLOYMENT_YEARS",0),p("IS_UNEMPLOYED",1),p("CREDIT_TO_INCOME_RATIO",15),p("ANNUITY_TO_INCOME_RATIO",0.7),p("CREDIT_PER_FAMILY_MEMBER",1000000),p("INCOME_PER_FAMILY_MEMBER",30000),p("CHILD_DEPENDENCY_RATIO",0.5),p("EXT_SOURCE_MEAN",0.1),p("CREDIT_TERM",120),p("EXT_SOURCE_1_MISSING",1),p("OWN_CAR_AGE_MISSING",1),p("YEARS_BUILD_MISSING",1),p("NAME_CONTRACT_TYPE","Revolving loans"),p("CODE_GENDER","M"),p("FLAG_OWN_CAR","N"),p("FLAG_OWN_REALTY","N"),p("NAME_TYPE_SUITE","Unaccompanied"),p("NAME_INCOME_TYPE","Unemployed"),p("NAME_EDUCATION_TYPE","Lower secondary"),p("NAME_FAMILY_STATUS","Single / not married"),p("NAME_HOUSING_TYPE","Rented apartment"),p("OCCUPATION_TYPE","Low-skill Laborers"),p("WEEKDAY_APPR_PROCESS_START","MONDAY"),p("ORGANIZATION_TYPE","Business Entity Type 3"),p("FONDKAPREMONT_MODE","reg oper account"),p("HOUSETYPE_MODE","block of flats"),p("WALLSMATERIAL_MODE","Panel"),p("EMERGENCYSTATE_MODE","No")])

# Test 3: Default settings (average male worker)
s3 = test("DEFAULT", [p("AGE_YEARS",35),p("EMPLOYMENT_YEARS",5),p("IS_UNEMPLOYED",0),p("CREDIT_TO_INCOME_RATIO",3),p("ANNUITY_TO_INCOME_RATIO",0.18),p("CREDIT_PER_FAMILY_MEMBER",225000),p("INCOME_PER_FAMILY_MEMBER",75000),p("CHILD_DEPENDENCY_RATIO",0.33),p("EXT_SOURCE_MEAN",0.6),p("CREDIT_TERM",24),p("EXT_SOURCE_1_MISSING",0),p("OWN_CAR_AGE_MISSING",1),p("YEARS_BUILD_MISSING",1),p("NAME_CONTRACT_TYPE","Cash loans"),p("CODE_GENDER","M"),p("FLAG_OWN_CAR","N"),p("FLAG_OWN_REALTY","Y"),p("NAME_TYPE_SUITE","Unaccompanied"),p("NAME_INCOME_TYPE","Working"),p("NAME_EDUCATION_TYPE","Secondary / secondary special"),p("NAME_FAMILY_STATUS","Married"),p("NAME_HOUSING_TYPE","House / apartment"),p("OCCUPATION_TYPE","Laborers"),p("WEEKDAY_APPR_PROCESS_START","MONDAY"),p("ORGANIZATION_TYPE","Business Entity Type 3"),p("FONDKAPREMONT_MODE","reg oper account"),p("HOUSETYPE_MODE","block of flats"),p("WALLSMATERIAL_MODE","Panel"),p("EMERGENCYSTATE_MODE","No")])

# Test 4: Same but low credit score
s4 = test("LOW_SCORE", [p("AGE_YEARS",35),p("EMPLOYMENT_YEARS",5),p("IS_UNEMPLOYED",0),p("CREDIT_TO_INCOME_RATIO",3),p("ANNUITY_TO_INCOME_RATIO",0.18),p("CREDIT_PER_FAMILY_MEMBER",225000),p("INCOME_PER_FAMILY_MEMBER",75000),p("CHILD_DEPENDENCY_RATIO",0.33),p("EXT_SOURCE_MEAN",0.2),p("CREDIT_TERM",24),p("EXT_SOURCE_1_MISSING",0),p("OWN_CAR_AGE_MISSING",1),p("YEARS_BUILD_MISSING",1),p("NAME_CONTRACT_TYPE","Cash loans"),p("CODE_GENDER","M"),p("FLAG_OWN_CAR","N"),p("FLAG_OWN_REALTY","Y"),p("NAME_TYPE_SUITE","Unaccompanied"),p("NAME_INCOME_TYPE","Working"),p("NAME_EDUCATION_TYPE","Secondary / secondary special"),p("NAME_FAMILY_STATUS","Married"),p("NAME_HOUSING_TYPE","House / apartment"),p("OCCUPATION_TYPE","Laborers"),p("WEEKDAY_APPR_PROCESS_START","MONDAY"),p("ORGANIZATION_TYPE","Business Entity Type 3"),p("FONDKAPREMONT_MODE","reg oper account"),p("HOUSETYPE_MODE","block of flats"),p("WALLSMATERIAL_MODE","Panel"),p("EMERGENCYSTATE_MODE","No")])

# Test 5: Female pensioner
s5 = test("PENSIONER_F", [p("AGE_YEARS",62),p("EMPLOYMENT_YEARS",25),p("IS_UNEMPLOYED",0),p("CREDIT_TO_INCOME_RATIO",2),p("ANNUITY_TO_INCOME_RATIO",0.08),p("CREDIT_PER_FAMILY_MEMBER",150000),p("INCOME_PER_FAMILY_MEMBER",75000),p("CHILD_DEPENDENCY_RATIO",0),p("EXT_SOURCE_MEAN",0.7),p("CREDIT_TERM",18),p("EXT_SOURCE_1_MISSING",0),p("OWN_CAR_AGE_MISSING",0),p("YEARS_BUILD_MISSING",0),p("NAME_CONTRACT_TYPE","Cash loans"),p("CODE_GENDER","F"),p("FLAG_OWN_CAR","Y"),p("FLAG_OWN_REALTY","Y"),p("NAME_TYPE_SUITE","Unaccompanied"),p("NAME_INCOME_TYPE","Pensioner"),p("NAME_EDUCATION_TYPE","Higher education"),p("NAME_FAMILY_STATUS","Married"),p("NAME_HOUSING_TYPE","House / apartment"),p("OCCUPATION_TYPE","Managers"),p("WEEKDAY_APPR_PROCESS_START","MONDAY"),p("ORGANIZATION_TYPE","Business Entity Type 3"),p("FONDKAPREMONT_MODE","reg oper account"),p("HOUSETYPE_MODE","block of flats"),p("WALLSMATERIAL_MODE","Panel"),p("EMERGENCYSTATE_MODE","No")])

# Test 6: Young unemployed
s6 = test("YOUNG_UNEMP", [p("AGE_YEARS",21),p("EMPLOYMENT_YEARS",0.5),p("IS_UNEMPLOYED",1),p("CREDIT_TO_INCOME_RATIO",5),p("ANNUITY_TO_INCOME_RATIO",0.3),p("CREDIT_PER_FAMILY_MEMBER",400000),p("INCOME_PER_FAMILY_MEMBER",40000),p("CHILD_DEPENDENCY_RATIO",0),p("EXT_SOURCE_MEAN",0.35),p("CREDIT_TERM",60),p("EXT_SOURCE_1_MISSING",1),p("OWN_CAR_AGE_MISSING",1),p("YEARS_BUILD_MISSING",1),p("NAME_CONTRACT_TYPE","Cash loans"),p("CODE_GENDER","M"),p("FLAG_OWN_CAR","N"),p("FLAG_OWN_REALTY","N"),p("NAME_TYPE_SUITE","Unaccompanied"),p("NAME_INCOME_TYPE","Student"),p("NAME_EDUCATION_TYPE","Incomplete higher"),p("NAME_FAMILY_STATUS","Single / not married"),p("NAME_HOUSING_TYPE","With parents"),p("OCCUPATION_TYPE","Low-skill Laborers"),p("WEEKDAY_APPR_PROCESS_START","MONDAY"),p("ORGANIZATION_TYPE","Business Entity Type 3"),p("FONDKAPREMONT_MODE","reg oper account"),p("HOUSETYPE_MODE","block of flats"),p("WALLSMATERIAL_MODE","Panel"),p("EMERGENCYSTATE_MODE","No")])

print()
print("=" * 60)
print("  VALIDATION")
print("=" * 60)
checks = [
    ("Perfect < 10%", s1 < 0.10),
    ("Worst > 50%", s2 > 0.50),
    ("Low score > Default", s4 > s3),
    ("Perfect < Pensioner < Default", s1 < s5 < s3),
    ("Worst is highest", s2 == max(s1,s2,s3,s4,s5,s6)),
    ("Young unemployed > Default", s6 > s3),
]
all_pass = True
for name, passed in checks:
    status = "PASS" if passed else "FAIL"
    if not passed: all_pass = False
    print(f"  [{status}] {name}")

print()
if all_pass:
    print("  ALL CHECKS PASSED - Model behaves correctly!")
else:
    print("  SOME CHECKS FAILED - Review above")
