# coding: utf-8

import random

#Phrase tamplates, for response gernation
#These correspond to the spaCy definitions at https://spacy.io/api/annotation#named-entities
#[D] = Date  [P] = Person  [W] = Work-of-Art
#[V] and [N] represent verb and noun features that accompany the entities
PHRASES = [['DPWAF', ['(P) (A) in a (N) called (W) in (D)']],
            ['DPWCF', ['a (F) called (W) was (C) by (P) in (D)', '(P) (C) a (F) called (W) in (D)']],
            ['DPWFN', ['(P) was an (N) in a (F) called (W) in (D)']],
            ['DPBN', ['(P) is an (N) (B) in (D)', 'an (N) called (P) was (B) in (D)', 'in (D) the (N) (P) was (B)']],
            ['DPNZ', ['the (N) (P) (Z) in (D)', 'in (D) the (N) (P) (Z)', 'an (N) called (P) (Z) in (D)']],
            ['DPWA', ['(P) was in (W) in (D)']],
            ['DPWC', ['in (D) (W) was (C) by (P)', '(W) was (C) by (P) in (D)', '(P) (C) (W) in (D)']],
            ['DPWF', ['(W) was a (F) starring (P) in (D)']],
            ['DPWN', ['(P) was an (N) in (W) in (D)']],
            ['DWCF', ['a (F) called (W) was (C) in (D)', '(W) is a (F) (C) in (D)']],
            ['PWAF', ['(P) (A) in a (F) called (W)']],
            ['PWFN', ['(P) was an (N) in a (F) called (W)']],
            ['DPB', ['(P) was (B) in (D)', 'in (D) (P) was (B)']],
            ['DPZ', ['(P) (Z) in (D)', 'in (D) (P) (Z)']],
            ['DWP', ['in (D) (P) was in (W)', '(W) starred (P) in (D)']],
            ['PWA', ['(P) (A) in (W)']],
            ['PWC', ['(P) (C) (W)', '(W) was (C) by (P)']],
            ['PWF', ['(P) was in a (F) called (W)']],
            ['PFN', ['(P) is a (F) (N)', '(P) is an (N) in (F)']],
            ['PWN', ['(P) was an (N) in (W)']],
            ['PWN', ['(P) was an (N) in (W)']],
            ['PN', ['(P) is an (N)']],
            ['PA', ['(P) (A) in many movies']],
            ['WF', ['(W) is a (F)']],
            ['WP', ['(P) was in (W)', '(W) starred (P)']]]

#SYNSETS of FORM  [phrase key, [response substitution set, additional fact triggers]]
SYNSETS = [['VC',['directed', 'helmed', 'filmed'],['director']], #addnl stems[list] needed for finding the synset
           ['VC',['made', 'produced', 'created'],['producer']],
           ['VA',['starred', 'featured', 'acted'],['actor', 'actress']],
           ['VB',['born'],['DOB']],
           ['VZ',['died', 'passed away'],['RIP']],
           ['NN',['director'],['skipper']],
           ['NN',['producer'],['maker']],
           ['NN',['actor', 'movie star'],['thespian']],
           ['NN',['actress', 'movie star'],['thespian']],
           ['NF',['tvepisode', 'tv show'],['serial', 'show']],
           ['NF',['film', 'movie', 'motion picture'],['blockbuster', 'tvmovie']]]

ENTITIES = ['PERSON', 'WORK_OF_ART', 'DATE', 'ORG', 'FACILITY', 'MONEY']
ENT_ATTRS = ['DATE', 'MONEY']

#it is assumed all features have been stemmed/lemmatised on extraction
#claim = [['The Hudsucker Proxy', 'ENT'], ['Jennifer Jason Leigh', 'ENT'], ['actress', 'VERB']]#Ruby Barnhill

claim = [['actor', 'NN'],
         ['called', 'VBN'],
         ['Tom Cruise', 'ENT'],
         ['was', 'VBD'],
         ['Top', 'NNP'],
         ['Gun', 'NNP']]

def rank_facts(facts, features):
    """=============================FACT SCORING================================================================
    cross-references each fact against the fullset of salient claim features,
    and calculate a score according to an algorithm thta factors #entities and #non-entities matching the claim> 
    the 2 highest scoring fact indexes are then stored, ready for processing"""
    
    #map each fact against the set of claim features, and calculate the fact's resulting score
    #and locate the 2 highest scoring facts (for responses purposes)
    responses = [[0, 0],[0, 0]] #each top scoring fact comprising its [index posn & score]
    for pos, fact in enumerate(facts):
        match = [0, 0] # tracks entity & feature matches for this fact
        for feature in features:
            attr = 0
            
            #for entity features of the claim, try to find a matching entity within this candidate fact
            if feature[1] == 'ENT': 
                while attr < len(fact) and ((fact[attr][1] not in ENTITIES) or feature[0].lower() != fact[attr][0]):
                    attr += 1
                #if a matching entity attribute was found
                if attr < len(fact):
                    fact[attr][2] = True #mark this attribute as a hit (needed for responses generation later)
                    if fact[attr][1] in ENT_ATTRS:
                        match[1] += 1
                    else:
                        match[0] += 1
            else:     
                #!!!! below needs to be enhanced - we strictly speaking should be using synonym sets,
                #AND fatrues should be checked in relation to context of preceding entity
                
                #for NON-entity features of the claim, try to find a matching NON-entity within this candidate fact
                #NOTE as our fact store is not POS-tagged, the first match is used irrespective of the claim POS
                while attr < len(fact) and ((fact[attr][1] in ENTITIES) or feature[0].lower() != fact[attr][0]):
                    attr += 1
                #if a matching non-entity attribute was found
                if attr < len(fact):
                    #fact[attr][2] = True #do not mark as hit, accompanying faetures are used for truth testing only
                    match[1] += 1
                    
        #set the score for this fact, based on the total matches across all features of the claim
        score = (2 * match[0] - min(2, match[0])) * (2 * match[1] + max(0, 1 - match[1])) + match[0]
        
        #if the score exceeds either of the current top scoring facts, insert this new responses accordingly
        if score > responses[0][1]:
            responses[1] = responses[0] #demote current 1st responses (if any) to position 2
            responses[0] = [pos, score] #and set new 1st responses to this new fact
        else:
            if score > responses[1][1]:
                responses[1] = [pos, score] #replace current 2nd responses with this new fact
                
        #repeat for each fact in the fact store
    return [facts[responses[0][0]], facts[responses[1][0]]]


#find a synset with same POS of the feature, that contains this feature
def find_synset(attribute, tag):
    synset = 0
    while synset < len(SYNSETS) and (tag != SYNSETS[synset][0][0] or attribute not in (SYNSETS[synset][1] + SYNSETS[synset][2])):
        synset += 1
    if synset == len(SYNSETS):
        synset = -1
    return synset


#insert this key into its component of the phrase key, into its alphabetic position
def get_hook(char, hooks):
    hook = 0
    while hook < len(hooks) and char > hooks[hook]:
        hook += 1 
    return hook


def generate_response(facts, features):
    """=============================RESPONSE GENERATION================================================================
    scans the highest scoring facts against the claim to establish the matching set of entities and features
    this scan includes accomapnying verbs and nouns that describe the respective entities
    synonym sets are used to verify matches for non-proper (verb, noun) features
    an appropriate parse template is then randonly selected for this match-set
    and random substitutions are made from each synonym set when generating the response
    If any features don't match, the response is set to False,
    and in this case a parse template is insrtead randonly selected from thos templates that match the number of asserted features """
    
    phrases = []
    previous = False
    for rank, fact in enumerate(facts):
        hooks = [' ',' ']
        hits = [['ents'],['feats']]
        checked = []
        accompany = 0
        #intiialise entity features as failed. All matched entities will then be reverted below
        for feature in features:
            if feature[1] == 'ENT':
                checked.append(['FAIL',''])
            else:
                checked.append(['',''])
        result = False #claim is assumed to be in-correct until we prove otherwise          
        #for each attribute in highest scoring fact
        for attribute in fact:
            #if attribute is a Hit
            if attribute[2] == True:
                #if this is an entity atribute
                if attribute[1] in ENTITIES:
                    #find position of this entity char within current hook string
                    hook = get_hook(attribute[1][0], hooks[0])
                    #add first char of attribute[1] to hook_1
                    hooks[0] = hooks[0][:hook] + attribute[1][0] + hooks[0][hook:]
                    #add corresponding entity to hit-set
                    hits[0].insert(hook, attribute[0])
                    hit = True
                    result = True
                    fcount = 0
                    #mark this asserted entity as matched (in the claim)
                    while fcount < len(features) and features[fcount][0].lower() != attribute[0]:
                        fcount += 1
                    if fcount == len(features):
                        return ("Error - entity hit not found in previously ranked fact")
                    else:
                        checked[fcount][0] = 'DONE'
            else:
                #if this is an accompanying feature for prev matched entity
                if attribute[1] == 'RELN' or (attribute[1] == '' and hit):
                    #starting at 1st feature of claim
                    fcount = 0
                    matched = False
                    accompanying = False
                    #while more features remaining and attribute not yet matched
                    while fcount < len(features) and not matched:
                        #print(attribute[0])
                        #if feature is NOT an entity and feature[1] not alraedy DONE:
                        if not (features[fcount][1] == 'ENT' or checked[fcount][0] == 'DONE'):
                            #find synonym set for this POS usage of this attribute
                            synset = find_synset(attribute[0], features[fcount][1][0])
                            #print(features[fcount][0], "|", features[fcount][1], "|", synset,)
                            if synset in range(0, len(SYNSETS)):
                                #include this as an accompanying attribute in the fact
                                accompanying = True
                                #if feature is in this synonym set
                                if features[fcount][0].lower() in (SYNSETS[synset][1] + SYNSETS[synset][2]):
                                    #set matched = true (ie. stop checking more attributes)
                                    matched = True
                                    #set this attribute's target synset against this feature
                                    checked[fcount][1] = synset
                                    #set feature[1] to 'DONE' (ie. feature should only be used once)
                                    checked[fcount][0] = 'DONE'
                                    #print('DONE')
                                else:
                                    #if a synset matches the failed faeture
                                    failset = find_synset(features[fcount][0], features[fcount][1][0])
                                    if failset < 0:
                                        #then set feature synset
                                        checked[fcount][1] = synset
                                        checked[fcount][0] = 'FAILF'
                                    else:
                                        #otherwise no other choice but to use attribute synset
                                        checked[fcount][1] = failset
                                        checked[fcount][0] = 'FAILA'
                                    #set feature[1] to 'FAIL' (will persist unless resolved by another fact attribute)                          
                                    #print('FAIL')
                            else:
                                print ("Error - No Synset available for ",attribute[0]," used as a ", features[fcount][1])
                                #return ("Error - No Synset available for ",attribute[0]," used as a ", features[fcount][1])

                        #contnue to nnxt feature
                        fcount += 1
                    #if an available synset was found matching this accompanying attribute
                    if accompanying:
                        #then include it in the response
                        accompany += 1
    
                #set hit to false
                hit = False
            
            #repeat for next attribute of fact
        
        #if at least one entity was matched
        if result:
      
            """----Build the 2nd (accompanying) part of the Phrase Key ----------------------------------------------- """
            # continue building rest of phrase key for any accompanying fact attributes that matched the claim
            #prioritising those claim features that matched the synset of the fact attribute
            length = 0 #length of the phrase key
            for outcome in ['DONE', 'FAILF', 'FAILA']:
                for check in checked:
                    #if this is an accompanying feature 
                    if check[0] == outcome and check[1] != '':
                        #if there are still more accompanying fact attributes not yet matched
                        if length < accompany:
                            #print(check[1], hooks[1])
                            #find position of the key of this synset within current hook string
                            hook = get_hook(SYNSETS[check[1]][0][1], hooks[1])
                            #add first char of POS of synonym root to hook_2
                            hooks[1] = hooks[1][:hook] + SYNSETS[check[1]][0][1] + hooks[1][hook:]
                            #print(hooks[1])
                            #add index of synonym set to match-set
                            hits[1].insert(hook, check[1])
                            length += 1
            
            """----Calculate the Fact Result -------------------------------------------------------------------------- """
            #check overall validity including any other accompanying assertions made in the claim
            #for the second ranked fact this only needs to be done if the first 'full' fact was False
            if not previous:
                fcount = 0
                #while result still currently true    
                while fcount < len(features) and result:
                    #continue checking for failure
                    if features[fcount][1] == 'ENT':
                        #principal entities are only mandatory on top ranked fact
                        if rank == 0:
                            #for frst ranked fact, check prcinipal entity hits
                            result = checked[fcount][0] == 'DONE' 
                    else:
                        #then check for accompanying features
                        result = checked[fcount][0] not in ['FAILF', 'FAILA']
                    fcount += 1
                #record this as a reference for the next fact check
                previous = result
            
            """---Construct the Narrative Response -------------------------------------------------------------------------- """
            #set key as hook_1+hook_2
            #starting at first phrase set
            pcount = 0
            #while key not in this phrase key
            while pcount < len(PHRASES) and (hooks[0] + hooks[1]).replace(' ','') != PHRASES[pcount][0]:
                #continue tonext phrase set
                pcount += 1
            #if key matched (else this is an error)
            if pcount < len(PHRASES):
                #set phrase as random pick from phrase[1]
                phrase = random.choice(PHRASES[pcount][1])
                #for each char in hook_1
                for char in range(1, len(hooks[0])):
                    #substitute char for hit-set[count] in phrase
                    phrase = phrase.replace("(" + hooks[0][char] + ")", hits[0][char].title())
                #for each char in hook_2
                for char in range(1, len(hooks[1])):
                    #substitute random pick from synonym set attched to match-set[count] in phrase
                    phrase = phrase.replace("(" + hooks[1][char] + ")", random.choice(SYNSETS[hits[1][char]][1]))
                
                phrases.append([result, ":: ", phrase])#return (result, ":: ", phrase)

            else:
                #phrases.append(["error - bad phrase key - ", hooks[0] + hooks[1]])#return ("error - bad phrase key - ", hooks[0] + hooks[1])
                pass
                  
        else:
            #no entities match the claim

            if rank == 0:
                #this advice is only necessaray for top ranked fact
                #if the second ranked fact has zero asociation with claim, we simply dont display anything
                return ("Your claim doesn't appear to mention any known entity (for example, film or person)")
                #print("Please try again")

                
        #and repeat for next (second) ranked fact

    return phrases
            
if __name__ == '__main__':
    
#    facts = [[['The Hudsucker Proxy', 'WORK_OF_ART', True],
#             ['movie', '', False],
#             ['1994', 'DATE', False],
#             ['made', '', False],
#             ['actress', '', False],
#             ['Jennifer Jason Leigh', 'PERSON', True],
#             ['1962', 'DATE', False],
#             ['born', '', False]],
#            [['Jennifer Jason Leigh', 'PERSON', True],
#             ['1962', 'DATE', False],
#             ['born', '', False],
#             ['actress', '', True],
#             ['A Thousand Acres', 'WORK_OF_ART', False],
#             ['movie', '', False],
#             ['1997', 'DATE', False],
#             ['made', '', False]]]
    
    facts = [[['tom cruise', 'WORK_OF_ART', True],
              ['tvepisode', '', False],
              ['2004', 'DATE', False],
              ['made', '', False],
              ['self', 'RELN', False],
              ['tom cruise', 'PERSON', False],
              ['1962', 'DATE', False],
              ['born', '', False]],
             [['tom cruise', 'WORK_OF_ART', True],
              ['tvepisode', '', False],
              ['2004', 'DATE', False],
              ['made', '', False],
              ['self', 'RELN', False],
              ['stephen colbert', 'PERSON', False],
              ['1964', 'DATE', False],
              ['born', '', False]]]
    
    topfacts = rank_facts(facts, claim)
    generate_response(topfacts, claim)
    
            
            
            
    
