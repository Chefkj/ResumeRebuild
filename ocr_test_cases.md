# OCR TEXT EXTRACTION TEST CASES

## Test Case 1: merged_location

### Input Text:
```
ColoradoFacilitated as part of the team responsibilities.
```

### Expected Output:
```
Colorado
Facilitated as part of the team responsibilities.
```

---

## Test Case 2: merged_city_state

### Input Text:
```
Portland, COFacilitated as partof the role.
```

### Expected Output:
```
Portland, CO
Facilitated as part of the role.
```

---

## Test Case 3: merged_location

### Input Text:
```
IdahoMaintained as part of the team responsibilities.
```

### Expected Output:
```
Idaho
Maintained as part of the team responsibilities.
```

---

## Test Case 4: merged_city_state

### Input Text:
```
Philadelphia, IDMaintained as part of the role.
```

### Expected Output:
```
Philadelphia, ID
Maintained as part of the role.
```

---

## Test Case 5: merged_location

### Input Text:
```
FloridaSpearheaded as part of the team responsibilities.
```

### Expected Output:
```
Florida
Spearheaded as part of the team responsibilities.
```

---

## Test Case 6: merged_city_state

### Input Text:
```
Salt Lake City, FLSpearheaded as part of the role.
```

### Expected Output:
```
Salt Lake City, FL
Spearheaded as part of the role.
```

---

## Test Case 7: merged_location

### Input Text:
```
CaliforniaImplemented as part of the team responsibilities.
```

### Expected Output:
```
California
Implemented as part of the team responsibilities.
```

---

## Test Case 8: merged_city_state

### Input Text:
```
Miami, CAImplemented as part of the role.
```

### Expected Output:
```
Miami, CA
Implemented as part of the role.
```

---

## Test Case 9: merged_location

### Input Text:
```
FloridaAnalyzed as part of the team responsibilities.
```

### Expected Output:
```
Florida
Analyzed as part of the team responsibilities.
```

---

## Test Case 10: merged_city_state

### Input Text:
```
Portland, FLAnalyzed as part of the role.
```

### Expected Output:
```
Portland, FL
Analyzed as part of the role.
```

---

## Test Case 11: embedded_header_after_period

### Input Text:
```
Completed all required tasks.EMPLOYMENTCreated a new system.
```

### Expected Output:
```
Completed all required tasks.

EMPLOYMENT

Created a new system.
```

---

## Test Case 12: embedded_header_within_text

### Input Text:
```
iiwseEMPLOYMENThpqwl
```

### Expected Output:
```
iiwse

EMPLOYMENT

hpqwl
```

---

## Test Case 13: embedded_header_after_period

### Input Text:
```
Completed all required tasks.SUMMARYCreated a new system.
```

### Expected Output:
```
Completed all required tasks.

SUMMARY

Created a new system.
```

---

## Test Case 14: embedded_header_within_text

### Input Text:
```
ssxhgSUMMARYtidou
```

### Expected Output:
```
ssxhg

SUMMARY

tidou
```

---

## Test Case 15: embedded_header_after_period

### Input Text:
```
Completed all required tasks.EDUCATIONCreated a new system.
```

### Expected Output:
```
Completed all required tasks.

EDUCATION

Created a new system.
```

---

## Test Case 16: embedded_header_within_text

### Input Text:
```
zrobqEDUCATIONepsmt
```

### Expected Output:
```
zrobq

EDUCATION

epsmt
```

---

## Test Case 17: embedded_header_after_period

### Input Text:
```
Completed all required tasks.SKILLSCreated a new system.
```

### Expected Output:
```
Completed all required tasks.

SKILLS

Created a new system.
```

---

## Test Case 18: embedded_header_within_text

### Input Text:
```
xebtwSKILLSlcwuc
```

### Expected Output:
```
xebtw

SKILLS

lcwuc
```

---

## Test Case 19: embedded_header_after_period

### Input Text:
```
Completed all required tasks.WORK HISTORYCreated a new system.
```

### Expected Output:
```
Completed all required tasks.

WORK HISTORY

Created a new system.
```

---

## Test Case 20: embedded_header_within_text

### Input Text:
```
gkwoqWORK HISTORYztkrr
```

### Expected Output:
```
gkwoq

WORK HISTORY

ztkrr
```

---

## Test Case 21: broken_date_range

### Input Text:
```
November 2014 - July
2018
```

### Expected Output:
```
November 2014 - July 2018
```

---

## Test Case 22: missing_space_date

### Input Text:
```
November2014 - July 2018
```

### Expected Output:
```
November 2014 - July 2018
```

---

## Test Case 23: dash_prefix_date

### Input Text:
```
-November 2014- July 2018
```

### Expected Output:
```
 - November 2014 - July 2018
```

---

## Test Case 24: broken_date_range

### Input Text:
```
May 2020- October
2022
```

### Expected Output:
```
May 2020 - October 2022
```

---

## Test Case 25: missing_space_date

### Input Text:
```
May2020 - October 2022
```

### Expected Output:
```
May 2020 - October 2022
```

---

## Test Case 26: dash_prefix_date

### Input Text:
```
-May 2020 - October2022
```

### Expected Output:
```
 - May 2020 - October 2022
```

---

## Test Case 27: broken_date_range

### Input Text:
```
May 2016 - October
2019
```

### Expected Output:
```
May 2016 - October 2019
```

---

## Test Case 28: missing_space_date

### Input Text:
```
May2016 - October 2019
```

### Expected Output:
```
May 2016 - October 2019
```

---

## Test Case 29: dash_prefix_date

### Input Text:
```
-May 2016 - October 2019
```

### Expected Output:
```
 - May 2016 - October 2019
```

---

## Test Case 30: broken_date_range

### Input Text:
```
December 2022 - March
2023
```

### Expected Output:
```
December 2022 - March 2023
```

---

## Test Case 31: missing_space_date

### Input Text:
```
December2022 - March 2023
```

### Expected Output:
```
December 2022 - March 2023
```

---

## Test Case 32: dash_prefix_date

### Input Text:
```
-December 2022 - March 2023
```

### Expected Output:
```
 - December 2022 - March 2023
```

---

## Test Case 33: broken_date_range

### Input Text:
```
July 2021 - November
2022
```

### Expected Output:
```
July 2021 - November 2022
```

---

## Test Case 34: missing_space_date

### Input Text:
```
July2021 - November 2022
```

### Expected Output:
```
July 2021 - November 2022
```

---

## Test Case 35: dash_prefix_date

### Input Text:
```
-July 2021 - November 2022
```

### Expected Output:
```
 - July 2021 - November 2022
```

---

## Test Case 36: email_space_after_at

### Input Text:
```
30l0e4a7@ gmail.com
```

### Expected Output:
```
30l0e4a7@gmail.com
```

---

## Test Case 37: email_space_before_at

### Input Text:
```
30l0e4a7 @gmail.com
```

### Expected Output:
```
30l0e4a7@gmail.com
```

---

## Test Case 38: email_space_after_at

### Input Text:
```
gt07djcz@ company.com
```

### Expected Output:
```
gt07djcz@company.com
```

---

## Test Case 39: email_space_before_at

### Input Text:
```
gt07djcz @company.com
```

### Expected Output:
```
gt07djcz@company.com
```

---

## Test Case 40: email_space_after_at

### Input Text:
```
dbe5krqo@ company.com
```

### Expected Output:
```
dbe5krqo@company.com
```

---

## Test Case 41: email_space_before_at

### Input Text:
```
dbe5krqo @company.com
```

### Expected Output:
```
dbe5krqo@company.com
```

---

## Test Case 42: email_space_after_at

### Input Text:
```
zqtq92ni@ outlook.com
```

### Expected Output:
```
zqtq92ni@outlook.com
```

---

## Test Case 43: email_space_before_at

### Input Text:
```
zqtq92ni @outlook.com
```

### Expected Output:
```
zqtq92ni@outlook.com
```

---

## Test Case 44: email_space_after_at

### Input Text:
```
4oucuzmc@ gmail.com
```

### Expected Output:
```
4oucuzmc@gmail.com
```

---

## Test Case 45: email_space_before_at

### Input Text:
```
4oucuzmc @gmail.com
```

### Expected Output:
```
4oucuzmc@gmail.com
```

---

## Test Case 46: broken_line_after_connector

### Input Text:
```
Collaborated in
stakeholders to complete the project.
```

### Expected Output:
```
Collaborated in stakeholders to complete the project.
```

---

## Test Case 47: broken_line_before_connector

### Input Text:
```
Implemented the
system in users across departments
```

### Expected Output:
```
Implemented the system in users across departments
```

---

## Test Case 48: broken_line_after_connector

### Input Text:
```
Collaborated in
stakeholders to complete the project.
```

### Expected Output:
```
Collaborated in stakeholders to complete the project.
```

---

## Test Case 49: broken_line_before_connector

### Input Text:
```
Implemented
the system in users across departments
```

### Expected Output:
```
Implemented the system in users across departments
```

---

## Test Case 50: broken_line_after_connector

### Input Text:
```
Collaborated by
stakeholders to complete the project.
```

### Expected Output:
```
Collaborated by stakeholders to complete the project.
```

---

## Test Case 51: broken_line_before_connector

### Input Text:
```
Implemented
the system by users across departments
```

### Expected Output:
```
Implemented the system by users across departments
```

---

## Test Case 52: broken_line_after_connector

### Input Text:
```
Collaborated for
stakeholders to complete the project.
```

### Expected Output:
```
Collaborated for stakeholders to complete the project.
```

---

## Test Case 53: broken_line_before_connector

### Input Text:
```
Implemented
the system for users across departments
```

### Expected Output:
```
Implemented the system for users across departments
```

---

## Test Case 54: broken_line_after_connector

### Input Text:
```
Collaborated and
stakeholders to complete the project.*
```

### Expected Output:
```
Collaborated and stakeholders to complete the project.
```

---

## Test Case 55: broken_line_before_connector

### Input Text:
```
Implemented the
system and users across departments
```

### Expected Output:
```
Implemented the system and users across departments
```

---

## Test Case 56: multiple_skills_sections

### Input Text:
```
SKILLS

JavaScript,Customer Service, Critical Thinking

Some professional accomplishments here.*

SKILLS

JavaScript, Design, C++
```

### Expected Output:
```
SKILLS

JavaScript, Customer Service, Critical Thinking

Some professional accomplishments here.

• SKILLS:

JavaScript, Design, C++
```

---

## Test Case 57: multiple_skills_sections

### Input Text:
```
SKILLS

Design, Sales, Critical Thinking

Some professional accomplishments here.

SKILLS

C++, SQL, Machine Learning
```

### Expected Output:
```
SKILLS

Design, Sales, Critical Thinking

Some professional accomplishments here.

• SKILLS:

C++, SQL, Machine Learning
```

---

## Test Case 58: multiple_skills_sections

### Input Text:
```
SKILLS

Data Analysis, Java, JavaScript

Some professional accomplishments here.

SKILLS

Leadership, Customer Service, Communication
```

### Expected Output:
```
SKILLS

Data Analysis, Java, JavaScript

Some professional accomplishments here.

• SKILLS:

Leadership, Customer Service, Communication
```

---

## Test Case 59: multiple_skills_sections

### Input Text:
```
SKILLS

SQL, Python, Sales

Some professional accomplishments here.

SKILLS

Problem Solving, JavaScript, Java
```

### Expected Output:
```
SKILLS

SQL, Python, Sales

Some professional accomplishments here.

• SKILLS:

Problem Solving, JavaScript, Java
```

---

## Test Case 60: multiple_skills_sections

### Input Text:
```
SKILLS

Project Management, Writing, Design

Some professional accomplishments here.

SKILLS

JavaScript, Problem Solving, Writing
```

### Expected Output:
```
SKILLS

Project Management, Writing, Design

Some professional accomplishments here.

• SKILLS:

JavaScript, Problem Solving, Writing
```

---

## Test Case 61: combined_issues

### Input Text:
```
Executive Assistant
Uber | ArizonaAnalyzed as team lead
May 2019 - November
2023
• Improved efficiency by 20% through automation.
• Collaborated with
stakeholders to develop new products.
Contact: i4lqcqva@ gmail.com
SKILLS.Advanced in Python and SQL.
```

### Expected Output:
```
Executive Assistant
Uber | Arizona
Analyzed as team lead
May 2019 - November 2023
• Improved efficiency by 20% through automation.
• Collaborated with stakeholders to develop new products.
Contact: i4lqcqva@gmail.com

SKILLS

Advanced in Python and SQL.
```

---

## Test Case 62: combined_issues

### Input Text:
```
Human Resources Coordinator
HP | ColoradoFacilitated as team lead
September 2017 - September
2018
• Improved efficiency by 20% through automation.
• Collaborated with
stakeholders to develop new products.
Contact: ocbdbut0@ gmail.com
SKILLS.Advanced in Python and SQL.
```

### Expected Output:
```
Human Resources Coordinator
HP | Colorado
Facilitated as team lead
September 2017 - September 2018
• Improved efficiency by 20% through automation.
• Collaborated with stakeholders to develop new products.
Contact: ocbdbut0@gmail.com

SKILLS

Advanced in Python and SQL.
```

---

## Test Case 63: combined_issues

### Input Text:
```
Customer Service Manager
Apple | OhioProduced as team lead
September 2013 - June
2016
• Improved efficiency by 20% through automation.
• Collaborated with
stakeholders to develop new products.
Contact: jwdkn7h7@ gmail.com
SKILLS.Advanced in Python and SQL.
```

### Expected Output:
```
Customer Service Manager
Apple | Ohio
Produced as team lead
September 2013 - June 2016
• Improved efficiency by 20% through automation.
• Collaborated with stakeholders to develop new products.
Contact: jwdkn7h7@gmail.com

SKILLS

Advanced in Python and SQL.
```

---

## Test Case 64: combined_issues

### Input Text:
```
Software Engineer
Microsoft | OregonResearched as team lead
March 2012 - May
2014
• Improved efficiency by 20% through automation.*
• Collaborated with
stakeholders to develop new products.
Contact: 11pq9brf@ gmail.com
SKILLS.Advanced in Python and SQL.
```

### Expected Output:
```
Software Engineer
Microsoft | Oregon
Researched as team lead
March 2012 - May 2014
• Improved efficiency by 20% through automation.
• Collaborated with stakeholders to develop new products.
Contact: 11pq9brf@gmail.com

SKILLS

Advanced in Python and SQL.
```

---

## Test Case 65: combined_issues

### Input Text:
```
Customer Service Manager
Dell | ColoradoAnalyzed as team lead
May 2020 - January
2021
• Improved efficiency by 20% through automation.
• Collaborated with
stakeholders to develop new products.
Contact: kp0xzuu0@gmail.com
SKILLS.Advanced in Python and SQL.
```

### Expected Output:
```
Customer Service Manager
Dell | Colorado
Analyzed as team lead
May 2020 - January 2021
• Improved efficiency by 20% through automation.
• Collaborated with stakeholders to develop new products.
Contact: kp0xzuu0@gmail.com

SKILLS

Advanced in Python and SQL.
```

---

