import streamlit as st
import pandas as pd
from py2neo import Graph 
from fuzzywuzzy import process, fuzz
from neo4j import GraphDatabase

# App to connect to Neo4j database
class App:
    def __init__(self):
        self.uri = 'neo4j+s://1df939c0.databases.neo4j.io'
        self.user = 'neo4j'
        self.password = 'AHX_6mwHoWnQt0KZm4NYX6uVCsYfa91fCervkPreoKc'
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        self.driver.close()
    
    def run_cypher_query(self, query, params=None, as_list = False):
        """ Run a Cypher query and return the results as a Pandas DataFrame 
        
        Parameters
        ----------
        query : str
            The Cypher query to run
        params : dict, optional
            The parameters to pass to the Cypher query
        as_list : bool, optional
            Whether to return the results as a list or as a Pandas DataFrame
        
        Returns
        -------
        Pandas DataFrame
            The results of the Cypher query
        """
        with self.driver.session() as session:
            result = session.run(query, params)
            df = pd.DataFrame([r.values() for r in result], columns=result.keys())
            # self.close()
        if as_list:
            col = df.columns[0]
            return df[col].values
        else:
            return df
        # session = self.driver.session()
        # result = session.run(query, parameters=params)
        # df = pd.json_normalize(result)
        # return result

app = App()
# query = """
# MATCH (n)-[r]->(c) RETURN n.preferredLabel, n.essential_occurrences LIMIT 5
#         """
# df = app.run_cypher_query(query)

# import networkx as nx
# from pyvis.network import Network


st.set_page_config(layout="wide", page_title='GripHR', page_icon='🖖')


# def run_cypher_query(query, as_list = False, params = None):
#     print(query)
#     # session = Graph("bolt://localhost:7687", auth=("neo4j", "griphr"))
#     session = Graph(st.secrets["NEO4J_URI"], auth=(st.secrets["NEO4J_USERNAME"], st.secrets["NEO4J_PASSWORD"]))

    
#     result = session.run(query, parameters = params).data() 
#     # convert result into pandas dataframe 
#     df = pd.json_normalize(result)
#     if as_list:
#         col = df.columns[0]
#         return df[col].values
#     else:
#         return df

# @st.cache(allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None})
@st.experimental_memo
def initializing_app():
    """
    Initializing the app by downloading all skills and occupations and storing these in a dataframe for quick reference
    """ 
    df_occupations = app.run_cypher_query(
        """
        MATCH (Occupation:Occupation) RETURN Occupation.code, Occupation.preferredLabel, Occupation.description, Occupation.altLabels, Occupation.iscoGroup, Occupation.conceptUri
        """
    )
    df_allpersons = app.run_cypher_query(
        """
        MATCH (Person:Person) RETURN Person.name as Name
        """
    )
    cols = df_occupations.columns.str.split('Occupation.')
    df_occupations.columns = [el[1] for el in cols]

    df_skills = app.run_cypher_query(
        """
        MATCH (Skill:Skill) RETURN DISTINCT Skill.preferredLabel, Skill.altLabels, Skill.description, Skill.conceptUri
        """
    )
    cols = df_skills.columns.str.split('Skill.')
    df_skills.columns = [el[1] for el in cols]

    allskills = df_skills.preferredLabel.unique()

    df_altlabels = (df_occupations[['conceptUri', 'preferredLabel', 'altLabels']].set_index(['conceptUri', 'preferredLabel'])
    .apply(lambda x: x.str.split('\n').explode())
    .reset_index())  

    altlabels = df_altlabels.altLabels.unique()
    preferredlabels = df_altlabels.preferredLabel.unique()
    return df_skills, df_occupations, df_altlabels, altlabels, preferredlabels, allskills, df_allpersons

df_skills, df_occupations, df_altlabels, altlabels, preferredlabels, allskills, df_allpersons = initializing_app()

def getUri(name, column = 'conceptUri'):
    print(name)
    try:
        row = df_altlabels.loc[df_altlabels.preferredLabel == name]
        return row[column].values[0]
    except:
        row = df_altlabels.loc[df_altlabels.altLabels == name]
        print(row)
        return row[column].values[0]

def getUriSkills(name, column = 'conceptUri'):
    if isinstance(name, str):
        name = [name]
    row = df_skills.loc[df_skills.preferredLabel.isin(name)]
    return row[column].values

exceptions = ['and', 'as', 'as if', 'as long as', 'at', 'but', 'by', 
            'even if', 'for', 'from', 'if', 'if only', 'in', 'into', 
            'like', 'near', 'now that', 'nor', 'of', 'off', 'on', 
            'on top of', 'once', 'onto', 'or', 'out of', 'over', 'past', 
            'so', 'so that', 'than', 'that', 'till', 'to', 'up', 'upon', 'with', 'when', 'yet']

def get_skills(uri):
    """
    Get the skills for a given Occupation URI and return a list of skills
    """
    query = f'''
                MATCH( (Occupation:Occupation {{conceptUri:'{uri}'}})<-[r]->(Skill:Skill))
                RETURN TYPE(r) as RelationType, Occupation.preferredLabel, Skill.preferredLabel, Skill.description
            '''
    df = app.run_cypher_query(query)
    df = df[['Occupation.preferredLabel', 'RelationType','Skill.preferredLabel', 'Skill.description']]
    df.columns = ['Occupation', 'RelationType','Skill', 'Skill description']
    return df

def space(num_lines=1):
    """Adds empty lines to the Streamlit app."""
    for _ in range(num_lines):
        st.write("")

def titleize(text, exceptions=exceptions):
    """
    Titleizes text by replacing words with their first letter capitalized, except for the exceptions.
    """
    text = text.split()
    # Capitalize every word that is not on "exceptions" list
    for i, word in enumerate(text):
        if word.isupper():
            text[i] = word
        else:
            text[i] = word.title() if word not in exceptions or i == 0 else word
    # Capitalize first word no matter what
    return ' '.join(text)

def find_label(name):
    """
    Finds the label for a given Occupation URI
    """
    match1 = process.extract(name, preferredlabels, scorer=fuzz.token_sort_ratio, limit = 1)[0]
    match2 = process.extract(name, altlabels, scorer=fuzz.token_sort_ratio, limit = 1)[0]
    if (match1[1] > 80) and (match1[1] > match2[1]):
        return match1[0]
    else:
        # match2 = process.extract(name, altlabels, scorer=fuzz.token_sort_ratio, limit = 1)[0]
        if match2[1] > 80:
            return match2[0]
        else:
            return f'Could not find match (Best was {match2})'

def create_person(name, occupation):
    """
    Creates a person with the given name and occupation
    """

    occ_uri = getUri(occupation)
    query = '''MERGE (person:Person {name: $name})
            WITH person
            MATCH (occupation:Occupation {conceptUri: $occupation})
            MERGE (person)-[r:HasOccupation]->(occupation)
            RETURN person.name as Name, occupation.preferredLabel as Occupation
            '''

    return app.run_cypher_query(query, params = {'name': name, 'occupation': occ_uri})

def get_person(name):
    """
    Finds the person with the given name
    """
    query = """
            MATCH (person:Person {name: $name})-[]->(o:Occupation)
            RETURN person.name as Name, o.preferredLabel as Occupation
            """
    return app.run_cypher_query(query, params = {'name' : name})

def add_skills(name, skill_list):
    """
    Adds skills to a person with the given name
    """
    uri_list = getUriSkills(skill_list)
    print(uri_list)
    query1 = '''
            MATCH (skill:Skill)-[r]-(person:Person {name: $name})
            DELETE r'''
    app.run_cypher_query(query1, params = {'name' : name})
    query2 = '''
            UNWIND $list AS AddSkill
            MATCH (skill:Skill {conceptUri: AddSkill}), (person:Person {name: $name})
            MERGE (person)-[r:HasSkill]->(skill)
            RETURN person.name as Name, skill.preferredLabel as Skill, skill.description as Description
            '''
    return app.run_cypher_query(query2, params = {'name': name, 'list': list(uri_list)})

def get_persons_skills(name):
    """
    Finds the skills of a person with the given name
    """
    query = """
            MATCH (person:Person {name: $name})-[]->(skill:Skill)
            RETURN person.name as Name, skill.preferredLabel as Skill, skill.description as Description
            """
    return app.run_cypher_query(query, params = {'name' : name})

def get_recommendations(name, num = 5):
    """
    Gets recommendations for a person with the given name, based on their current skills
    """
    query = f"""
            MATCH (person:Person {{name: $name}})-[]-(s1:Skill)-[r:CommunityOf]-(s:Skill)
            WHERE NOT (person)-[]-(s)
            RETURN sum(r.normalized_occurences) as link_prediction, s.preferredLabel as Skill
            ORDER BY link_prediction desc
            LIMIT $num;
            """
    return app.run_cypher_query(query, params = {'name': name, 'num': num})

# def create_pyvis(G):
    pvgraph = Network(height='465px', bgcolor='#222222', font_color='white')
    pvgraph.from_nx(G)

    # Generate network with specific layout settings
    pvgraph.repulsion(node_distance=420, central_gravity=0.33,
                       spring_length=110, spring_strength=0.10,
                       damping=0.95)

    # Save and read graph as HTML file (on Streamlit Sharing)
    try:
        path = '/tmp'
        pvgraph.save_graph(f'{path}/pyvis_graph.html')
        HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

    # Save and read graph as HTML file (locally)
    except:
        path = '/html_files'
        pvgraph.save_graph(f'{path}/pyvis_graph.html')
        HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

    # Load HTML file in HTML component for display on Streamlit page
    return HtmlFile


label_type_query = """CALL db.labels()"""
rel_type_query = """CALL db.relationshipTypes()"""

intro_text = """
# Introduction
**GripHR** is a revolutionary new app that allows companies to get a comprehensive overview of 
the talents and skills of their employees. With the app, companies can easily identify 
the strengths and areas for improvement within their workforce, helping them 
to make more informed decisions about training and development. 
The app uses a **graph database** to link occupations to the skills 
required for each job, making it easy to see the relationships 
between different roles and abilities. Whether you're a small 
business owner looking to optimize your team's potential or a 
HR professional looking to stay on top of employee skill sets, GripHR is the perfect solution.
"""

st.sidebar.image("./LogoWit.png", width = 193) #use_column_width=True, 

st.sidebar.markdown(intro_text)
st.sidebar.markdown("""---""")

st.sidebar.header('Graph management')

if st.sidebar.button('Get graph list'):
    graph_ls = app.run_cypher_query(label_type_query, as_list = True)
    if len(graph_ls) > 0:
        for el in graph_ls:
            st.sidebar.write(el)
    else:
        st.sidebar.write('There are currently no graphs in memory.')

##############################
#
#   Main panel content
#
##############################


##############################



#####
#
# Embedding column (col1)
#
#####

occupation_sel = 'data scientist'

def set_occupation(name = occupation_sel):
    st.session_state.occupation = name
    return 

if 'occupation' not in st.session_state:
    set_occupation()

for ss in ['owned_essential', 'owned_optional', 'other_skills']:
    if ss not in st.session_state:
        st.session_state[ss] = []

with st.expander('1. Find occupation and corresponding skills'):

    col1, col2 = st.columns((1, 2))
    with col1:
        occupation = st.text_input('Search for an occupation')
        search = st.button('Search')
        if search:
            search_label = find_label(occupation)
            if search_label.startswith('Could not'):
                st.write(search_label)
            else:
                # Session State also supports attribute based syntax
                set_occupation(name = search_label)

        occupation_sel = st.selectbox('Or select one from the list', preferredlabels, key='occupation')

        occ_category = getUri(st.session_state.occupation, column = 'preferredLabel')
        URI = getUri(st.session_state.occupation)
        st.markdown(f"You've selected: {titleize(st.session_state.occupation)} ([{titleize(occ_category)}]({URI}))")
        
        # st.write(st.session_state)
    ##### FastRP embedding creation
    with col2:
        # skills_button = st.button('Show skills')
        # if skills_button:
        df = get_skills(URI)
        df_essential = df.loc[df['RelationType'] == 'HasEssentialSkill']
        df_optional = df.loc[df['RelationType'] == 'HasOptionalSkill']
        st.write('Dataframe with the skills for a', titleize(occ_category))
        st.dataframe(df)


st.markdown("---")

with st.expander('2. Add persons & skills'):
    col1, col2 = st.columns((1, 2))

    with col1:
        with st.form("my_form"):
            st.write("Create user")
            name = st.text_input('Enter your name')
            occupation_val = st.text_input('Occupation', value = st.session_state.occupation, disabled=True)
            slider_val = st.slider("Years experience")
            # checkbox_val = st.checkbox("Create new person", default=True)
            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            if submitted:
                df_person = create_person(name, st.session_state.occupation)
                st.write("Added person: ", name)
                st.session_state.name = name

        try:
            st.dataframe(df_person)
        except:
            pass
        
        
        st.write("Or select existing person:")
        names = [''] + df_allpersons.Name.tolist()
        
        selected_name = st.selectbox('Or select one from the list', names, format_func=lambda x: 'Select an option' if x == '' else x)
        if selected_name != '':
            st.session_state.name = selected_name
            st.write(st.session_state.name)
            df_person = get_person(st.session_state.name)
            URI = getUri(df_person.Occupation.tolist()[0])
            df = get_skills(URI)
            df_essential = df.loc[df['RelationType'] == 'HasEssentialSkill']
            df_optional = df.loc[df['RelationType'] == 'HasOptionalSkill']

        if st.button('Show skills'):
            df_personalskills = get_persons_skills(st.session_state.name)
            personalskills = df_personalskills.Skill.tolist()
            owned_essential = [p for p in personalskills if p in df_essential.Skill.tolist()]
            owned_optional = [p for p in personalskills if p in df_optional.Skill.tolist()]
            other_skills = [p for p in personalskills if p not in df_essential.Skill.tolist() and p not in df_optional.Skill.tolist()]
            st.session_state.owned_essential = owned_essential
            st.session_state.owned_optional = owned_optional
            st.session_state.other_skills = other_skills
        # else:
        #     owned_essential = []
        #     owned_optional = []
        #     other_skills = []    
        #     st.session_state.owned_essential = owned_essential
        #     st.session_state.owned_optional = owned_optional
        #     st.session_state.other_skills = other_skills
            
        try:
            st.dataframe(df_person)
        except:
            pass
        


    space(1)
    with col2:
        try:
            essential_skills = df_essential.Skill
            optional_skills = df_optional.Skill
            if len(essential_skills) > 0:
                skills1 = st.multiselect("Choose from essential skills", essential_skills, default=st.session_state.owned_essential)
            if len(optional_skills) > 0:
                skills2 = st.multiselect("Choose from optional skills", optional_skills, default=st.session_state.owned_optional)

        except:
            pass
        skills3 = st.multiselect('Choose other skills', allskills, default=st.session_state.other_skills)
        
        if st.button('Add / update skills'):
            st.write('Adding skills to profile')
            st.session_state.skills = []
            for skill_list in [skills1, skills2, skills3]:
                try:
                    st.session_state.skills.extend(skill_list)
                except:
                    pass
            df_personalskills = add_skills(st.session_state.name, st.session_state.skills)
        

        try:
            st.dataframe(df_personalskills)
        except:
            pass

st.markdown("---")

with st.expander('3. Get recommended skills'):
    col1, col2 = st.columns((1, 1))
    button_recommend = []
    slider_recommend = st.slider("Number of recommendations", min_value=1, max_value=10)
    if st.button('Get recommendations'):
        # with col1:
        df_recommendations = get_recommendations(st.session_state.name, num = slider_recommend)
        st.dataframe(df_recommendations)
            # st.write(df_recommendations.Skill)
        # with col2:
        #     for rec in df_recommendations.Skill:
        #         button_recommend[rec] = st.button(rec)

# if st.button('Create graph of person'):

#     HtmlFile = create_pyvis(G)
#     st.components.v1.html(HtmlFile.read(), height=435)

st.markdown(""" <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style> """, unsafe_allow_html=True)

padding = 0
st.markdown(f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
    }} </style> """, unsafe_allow_html=True)
