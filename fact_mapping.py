# coding: utf-8

import sqlite3
from sqlite3 import Error

import re
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

#The following lists define the resident fact tables in the SQL database, and their associated fields

#PRINCIPAL tables house ENTITIES. Generally a distinct table will comprise each CLASS (type) of entity we may choose to collect/scrape
#PRINCIPAL tables must adhere to the following structural constraints.
#If any new tables are generated via web scraping (for example), then they must be constructed accordingly
    #the FIRST field MUST contain the index. This can be anything (arbitrary) provided only it be unique to that table
    #this first index field MUST be of the format 'labelid' (ie. nameid/titleid)
    #the SECOND field MUST contain the entity's identifying label (ie. name/title)
    #all remaining fields in the table contain any additional attributes of the entity, as may be required
#The following LIST (of tables) defines the Tablename and Label field for each table.
#NOTE the respective index fields are derived from the label field (by appending the text 'id')
PRINCIPALS = [['Titles','title'], ['Names','name']]

#The next LIST contains the respective spaCy Entity types that would have been reported by spaCy if this content HAD been web-scraped
#these are presented in field order, NOT including the index (hence from the label onwards)
#NULL entries are NOT entities (according to spaCY)
#NOTE the first label field is always an entity (by definition, as this identifies the principal entity)
#however this principal entity may also have further entity attributes (for example - dates, locations, £amounts)
PRINC_NERS = [['WORK_OF_ART','','DATE'],['PERSON','DATE','DATE']]

#The next LIST contains the accompanying salient term that MAY have been scraped alongside each ATTRIBUTE
#if an accompanying term WAS scraped, then this helps to deduce the context/interpretation of the attribute
#if no such term was scraped, then the context of the attribute may not be inferrable
#these are again presented in field order, BUT NOT including the leading index OR label (ie. the trailing attributes ONLY are shown)
#NULL entries means context is very unlikely to be obtained when scraping - for these attributes we can rely only on the data itself
PRINC_CTXT = [['','made'],['born','died']]

#RELATIONAL tables define any RELATION between entities (of different CLASSES)
#RELATIONAL tables must adhere to the following structural constraints.
#If any new tables are generated via web scraping (for example), then they must be constructed accordingly
    #relational tables must NOT be used to store any principal/entity records
    #they are used exclusively to specify relational connections (between entities), and any attributes arising from those relations
    #FOREIGN KEYS must be stored at the START of the table. Each FK is identified by the name of its target principal Table
    #all remaining fields (if any) contain any additional attributes arising from the relation, as may be required
#The following LIST (of tables) defines the relational Tablename and the name of each FK target table
RELATIONS = [['Cast',['Titles', 'Names']]]

#The next lists adopt precisely the same protocols as defined above for the prinicpal tables (***PLEASE READ ABOVE***)
#these are presented in field order, NOT including the FKs - hence the additional attributes only of the relation are listed
#hence, if a relation has NO attributes (ie. it purely defines the relation only) it will comprise an EMPTY [] entry in both lists below
RELAT_NERS = [['RELN']]
RELAT_CTXT = [['']]

ENTITIES = ['PERSON', 'WORK_OF_ART', 'DATE', 'ORG', 'FACILITY', 'MONEY']

#it is assumed all features have been stemmed/lemmatised on extraction
#claim = [['The Hudsucker Proxy', 'ENT'], ['Jennifer Jason Leigh', 'ENT'], ['actress', 'VERB']]#Ruby Barnhill
claim = [['Brad Pitt', 'ENT'], ['actor', 'NN']]

def create_connection(db_file):
    """
    Create a SQLite database connection to the specified database file.
    The value ":memory:" should be used if a memory based database is
    desired.
    :param db_file: The file to connect to
    :return: The database connection
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print("Error:", e)
        return None

def map_facts(features):
    """=============================FACT MAPPING================================================================
    builds a list of every fact associated with each entity in the claim,
    then stores these in a local facts array, each fact comrpising a set of attributes defining that fact
    each attribute is tagged with its spaCy entity identifier"""
     
    stemmer = SnowballStemmer("english")
    conn = create_connection("./data.db")
    facts = []
    
    #for each entity in the claim, collect all of its associated facts from the fact store
    for fpos, feature in enumerate(features):
        if feature[1] == 'ENT': #we are only interested in entity features at this stage (for fact extraction)
            found = False
            
            #check if this entity was already retrieved on an earlier pass
            fact = 0
            fcount = len(facts)
            while fact < fcount:
                attr = 0
                while attr < len(facts[fact]) and ((facts[fact][attr][1] not in ENTITIES) or feature[0].lower() != facts[fact][attr][0]):
                    attr += 1
                if attr < len(facts[fact]):
                    facts.pop(fact) #if it was, then delete it to prevent duplication
                    fcount -= 1
                fact += 1
    
            #check through each principal table until a match is found
            c = conn.cursor()
            prcount = 0
            while prcount < len(PRINCIPALS) and not found:
                
                #extract all matching records from this principal table, ready for inspection
                query = ("SELECT * FROM " + PRINCIPALS[prcount][0] + 
                             " WHERE " + PRINCIPALS[prcount][1] + "='" + feature[0].lower() + "';")
                c.execute(query)
                entities = list(c.fetchall())
                #if at least 1 matching entity was found
                if len(entities) > 0:
                    found = True
                    features[fpos][1] = 'ENT' #then mark this claim feature as an entity
            
                #extract all associated facts for each matching entity
                for entity in entities:
                    #print(entity)
                                    
                    #for each relational table, check through its FKs attempting to match this principal table
                    for relnum, relation in enumerate(RELATIONS):
                        rcount = 0
                        while rcount < len(relation[1]) and relation[1][rcount] != PRINCIPALS[prcount][0]:
                            rcount += 1
                            
                        #if a relational link was found, then select all records relating to this entity
                        if rcount < len(relation[1]): 
                            query = ("SELECT * FROM " + relation[0] + #
                                     " WHERE " + PRINCIPALS[prcount][1] + "id='" + entity[0] + "';")   
                            c.execute(query)
                            
                            #for each relational record, start building the fact for this relation
                            fact = []
                            for record in list(c.fetchall()):                    
                                #attribute | type(entity/feature) | hit? - !!need to stem the text
                                fact = [[entity[1], PRINC_NERS[prcount][0], True]] #initialise fact along with its entity flag
                                for pos, attribute in enumerate(entity[2:]): #and append its principal attributes
                                    if not re.search('[^a-z0-9\s]',attribute): #do not load null attributes
                                        fact.append([attribute, PRINC_NERS[prcount][pos + 1], False])
                                        if PRINC_CTXT[prcount][pos] != '':
                                            fact.append([PRINC_CTXT[prcount][pos], '', False])
                                #print("entity - ", fact)
                                #append the relational attributes (if any)
                                for pos, attribute in enumerate(record[len(relation[1]):]):
                                    if not re.search('[^a-z0-9\s]',attribute): #do not load null attributes
                                        fact.append([attribute, RELAT_NERS[relnum][pos], False])
                                        if RELAT_CTXT[relnum][pos] != '':
                                            fact.append([RELAT_CTXT[relnum][pos], '', False])
                                            #print("relation - ", fact)
                                
                                #for each additional FK in this relation, locate the respective principal table associated with this FK
                                for fcount, fkey in enumerate(relation[1]): 
                                    princ = 0
                                    while princ < len(PRINCIPALS) and (fkey != PRINCIPALS[princ][0] or fkey == PRINCIPALS[prcount][0]):
                                        princ += 1
                                        
                                    #extract the full respective record from this related principal table
                                    if princ < len(PRINCIPALS):                 
                                        query = ("SELECT * FROM " + PRINCIPALS[princ][0] + 
                                                 " WHERE " + PRINCIPALS[princ][1] + "id='" + record[fcount] + "';")
                                        c.execute(query)
                                            
                                        #then append this related entity, and each of its attributes
                                        #a single record only should always returned, as principal tables are indexed by entity
                                        #however the first record is delimited explicitly as a fail safe to avoid errors
                                        attributes = list(c.fetchall())[0]
                                        fact.append([attributes[1], PRINC_NERS[princ][0], False])
                                        for pos, attribute in enumerate(attributes[2:]):
                                            if not re.search('[^a-z0-9\s]',attribute): #do not load null attributes
                                                fact.append([attribute, PRINC_NERS[princ][pos + 1], False])
                                                if PRINC_CTXT[princ][pos] != '':
                                                    fact.append([PRINC_CTXT[princ][pos], '', False])
                                                #print("reln attr - ", attribute)                                    
                                    
                                #add new candidate fact for this relation
                                facts.append(fact)
                    
                    #if no relations were found, then store the entity fact alone, along with its principal attributes
                    if len(fact) == 0:  
                        fact.append([entity[1], PRINC_NERS[prcount][0], True])
                        for pos, attribute in enumerate(entity[2:]): #and its principal attributes
                            if not re.search('[^a-z0-9\s]',attribute): #do not load null attributes
                                fact.append([attribute, PRINC_NERS[prcount][pos + 1], False])
                                if PRINC_CTXT[prcount][pos] != '':
                                    fact.append([PRINC_CTXT[prcount][pos], '', False])
                        facts.append(fact)
                        
                #repeat for the next principal table if needed (if entity not yet found) 
                prcount += 1
                
        #and continue building facts for the next feature (if any) of the claim
    return facts

if __name__ == '__main__':
    facts = map_facts(claim)
            

            
            
            
    