//Import ESCO using CSV files
CREATE INDEX occupationGroup IF NOT EXISTS FOR (o:Occupation) ON (o.conceptUri);
CREATE INDEX skillLabel IF NOT EXISTS FOR (s:Skill) ON (s.conceptUri);
CREATE INDEX ISCOGroup IF NOT EXISTS FOR (g:ISCOGroup) ON (g.code);

//import skills and skillgroups
//skillgroups are also skills
load csv with headers from "file:///skillGroups_en.csv" as row
create (sg:Skillgroup {id:row.code})
set sg = row;
//skills
load csv with headers from "file:///skills_en.csv" as row
create (s:Skill {id:row.conceptUri})
set s = row;
//add the BROADER_THAN relationship between different skills
load csv with headers from "file:///broaderRelationsSkillPillar.csv" as row
match (smaller:Skill {conceptUri: row.conceptUri}), (broader:Skill {conceptUri: row.broaderUri})
create (broader)-[:BROADER_THAN]->(smaller);

//import occupations
load csv with headers from "file:///occupations_en.csv" as row
create (o:Occupation)
set o = row;

//import the International Standard Classification for Occupations of the ILO
load csv with headers from "file:///ISCOGroups_en.csv" as row
create (isco:ISCOGroup)
set isco = row;
//import the BROADER_THAN relationships between ISCO groups
load csv with headers from "file:///broaderRelationsOccPillar.csv" as row
match (smaller:ISCOGroup {conceptUri: row.conceptUri}), (broader:ISCOGroup {conceptUri: row.broaderUri})
create (broader)-[:BROADER_THAN]->(smaller);
//connect the occupations to their ISCOGroup
match (isco:ISCOGroup), (o:Occupation)
where isco.code = o.iscoGroup
create (o)-[:PART_OF_ISCOGROUP]->(isco);


:auto load csv with headers from "file:///occupationSkillRelations.csv" as row
CALL{
    with row
    match (s:Skill {conceptUri: row.skillUri}), (o:Occupation {conceptUri: row.occupationUri})
    CREATE (s)-[:RELATED_TO {type: row.relationType}]->(o)
} IN TRANSACTIONS OF 100 ROWS;
//Connect Skills to Occupations

//differentiate the different types of relations between occupations and skills
match (a)-[r:RELATED_TO]->(b)
where r.type = "essential"
create (a)-[:ESSENTIAL_FOR]->(b);
match (a)-[r:RELATED_TO]->(b)
where r.type = "optional"
create (a)-[:OPTIONAL_FOR]->(b);
//remove the old relationships
match (a)-[r:RELATED_TO]->(b)
delete r;



CALL apoc.periodic.iterate(
  "MATCH (a1:Skill)-[:ESSENTIAL_FOR]->(o:Occupation)<-[:ESSENTIAL_FOR]-(a2:Skill)
   WITH a1, a2, o
   RETURN a1, a2, count(*) AS occurred_together",
  "MERGE (a1)-[r:COMMUNITY_OF]-(a2)
   WHERE occurred_together > 5
   SET r.occurences = occurred_together",
  {batchSize: 100}
);

match(n:Skill)-[r:COMMUNITY_OF]->(m:Skill)
where r.occurences < 5
DELETE r;

CALL apoc.meta.graph;

