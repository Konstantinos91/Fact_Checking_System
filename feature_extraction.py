import spacy
from spacy.tokenizer import Tokenizer
from nltk.corpus import wordnet as WN
from nltk.corpus import stopwords
import en_core_web_sm
import re

#nltk.download("stopwords")
stopwords = set(stopwords.words('english'))

#nlp = spacy.load('en_core_web_sm')
nlp = en_core_web_sm.load()

#input = input('Input your claim: ')
#input = "Brad Pitt starred in Fight Club"
#input = "The Wizard of Oz was filmed in 1939 by David Fincher"
#submission = "the film The Hudsucker Proxy features an actress called Jennifer Jason Leigh"
submission = "an actor called Tom Cruise was in Top Gun"
#input = input.lower()

TAGS = ['VBN', 'VBD', 'VB', 'VBG', 'NN', 'NNP', 'NNS']
ENT_TAGS = ['NN', 'NNP', 'NNS']

#def chain_nouns(prevtok, features):
#    #if prevtag was a noun
#    if prevtok != "":
#        #first, append the previous noun chain as an entity
#        if 
#        features.append([prevtok, 'ENT'])
#        prevtok = ""
#    return features

def extract(claim):

    claim = re.sub('[^a-zA-Z0-9\s]+','',claim).strip()
    
    #claim is assumed defective until succussfully processed
    features = "failed"
    
    #Validating user input
    if claim == "":
        print("Sorry, you have not entered any claim. Please retry to enter your claim")
    elif claim.isspace() == True:
        print("Sorry, you have not entered any claim. Please retry to enter your claim")
    elif claim.isdigit():
        print("Sorry, you have entered only number(s). Please retry to enter your claim")
    elif len(claim) <= 20 or len(claim) >= 100: #too many character or too few
        print("Sorry, you have entered invalid length")
    else:
    #    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    #
    #    no_punct = ""
    #    for char in claim:
    #        if char not in punctuations:
    #            no_punct = no_punct + char
    # 
    #    doc = nlp(no_punct)
        doc = nlp(claim)
    
        token = 0
        grammatic = True
        while token < len(doc) and grammatic:
            #if token is not within a named entity and is not a noun tag
            if doc[token].ent_iob_ == 'O' and doc[token].text.lower() not in stopwords:#and doc[token].tag_  not in ENT_TAGS
                grammatic = WN.synsets(doc[token].text.lower())
            token += 1
       
        if not grammatic:
            print("Sorry, please check your spelling and try again")
        else:
            features = []
            prevtok = ""
            chain = 0 # length of current noun chain
            entity = ""
            for pos, token in enumerate(doc):
                #if this is the start of an entity
                if token.ent_iob_ == 'B':
                    #then start a new entity chain
                    entity = token.text
                #if this is a continuation of the current entity
                elif token.ent_iob_ == 'I':
                    #then concatenate this token to the current entity chain
                    entity = " ".join([entity, token.text])
                else:
                    # (token.ent_iob must therefore be 'O' - we are hence outside any entity)
                    #if an entity has just been built
                    if entity != "":
                        #if tag preceding the entity was a noun chain
                        if chain > 0:
                            #first, append the previous noun chain
                            if chain > 1 or prevtok == prevtok.title():
                                features.append([prevtok, 'ENT'])
                            else:
                                features.append([prevtok, 'NN'])
                            prevtok = ""
                            chain = 0
                        #then append the entity
                        features.append([entity, 'ENT'])
                        entity = ""
                    #if this is a meaninful token, that potentially carries content
                    if token.tag_ in TAGS and not (token.is_stop or token.text.lower() in stopwords):
                        #if this is any form of NOUN
                        if token.tag_[:2] == 'NN':
                            #if prevtag was NOT a noun, 
                            if chain == 0:
                                #then start a new noun chain
                                prevtok = token.text
                            else:
                                #else concatenate this noun to the current chain
                                prevtok = " ".join([prevtok, token.text])
                            chain += 1
                        else:
                            #if prevtag was a noun
                            if chain > 0:
                                #first, append the previous noun chain as an entity
                                if chain > 1 or prevtok == prevtok.title():
                                    features.append([prevtok, 'ENT'])
                                else:
                                    features.append([prevtok, 'NN'])
                                prevtok = ""
                                chain = 0
                            #append the new token
                            features.append([token.text, token.tag_])
                    else:
                        #if prevtag was a noun
                        if chain > 0:
                            #first, append the previous noun chain
                            if chain > 1 or prevtok == prevtok.title():
                                features.append([prevtok, 'ENT'])
                            else:
                                features.append([prevtok, 'NN'])
                            prevtok = ""
                            chain = 0
            #if there is still an un-appended noun chain
            if prevtok != "":
                #then append this final noun chain as an entity
                if chain > 1 or prevtok == prevtok.title():
                    features.append([prevtok, 'ENT'])
                else:
                    features.append([prevtok, 'NN'])
            #if the last token was an entity
            if entity != "":
                #then append the entity                        
                features.append([entity, 'ENT'])
                
    #        tag = [(token, token.tag_) for token in doc
    #                if token.tag_ in TAGS]
        
    #        ner = [(entity.text, "ENT") for entity in doc.ents if entity.text!=tag]
    #        features = tag+ner
      
    
    return features
        
if __name__ == '__main__':
    output = extract(submission)
    if output != []:
        print(output)
