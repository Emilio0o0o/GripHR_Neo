# Readme for a streamlit app to connect with Neo4j
## How to run

1. Install modules from requirements.txt
2. Add password to secrets.toml file
3. run:

```
streamlit run app.py
```

## How connections are made

1. The app connects to the Neo4j database using the password in the secrets.toml file
2. The app then queries the database for all the nodes and edges
3. The nodes and edges are then passed to a dataframe, used by the streamlit app, but any other format can be used as well

```mermaid
classDiagram
  class Employee {
    Employee_ID: int
    Employee_Name: string
    Job_Title: string
    Department: string
    Contact_Info: string
    Start_Date: date
    Location: string
    Manager_ID: int
    getSkills()
  }

  class Skill {
    Skill_ID: int
    Skill_Name: string
    Skill_Description: string
    getEmployees()
  }

  class Project {
    Project_ID: int
    Project_Name: string
    Project_Description: string
    Project_Start_Date: date
    Project_End_Date: date
    Project_Manager_ID: int
    getSkills()
  }

  class Training {
    Training_ID: int
    Training_Name: string
    Training_Description: string
    Training_Provider: string
    Training_Start_Date: date
    Training_End_Date: date
    getSkills()
  }

  class Assessment {
    Assessment_ID: int
    Assessment_Type: string
    Assessment_Date: date
    Assessment_Score: int
    Assessor_Name: string
    getEmployee()
    getSkill()
  }

  class Employee_Skill {
    Employee_ID: int
    Skill_ID: int
    Skill_Level: int
    Years_of_Experience: int
    Proficiency_Rating: int
    getEmployee()
    getSkill()
  }

  class Project_Skill {
    Project_ID: int
    Skill_ID: int
    Skill_Level_Required: int
    getProject()
    getSkill()
  }

  class Training_Skill {
    Training_ID: int
    Skill_ID: int
    Skill_Covered: string
    getTraining()
    getSkill()
  }

  Employee "1" *-- "0..*" Employee_Skill : has
  Skill "1" *-- "0..*" Employee_Skill : has
  Skill "1" *-- "0..*" Project_Skill : required for
  Project "1" *-- "0..*" Project_Skill : has
  Skill "1" *-- "0..*" Training_Skill : covered in
  Training "1" *-- "0..*" Training_Skill : has
  Employee "1" *-- "0..*" Assessment : takes
  Skill "1" *-- "0..*" Assessment : measures proficiency
```
